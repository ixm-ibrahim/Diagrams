"""Big files and locked files carried through git in parts, so that the work can go on from another computer.

    python tools/bigfiles.py split      before a commit: cut the carried files into parts under bigfiles/, locking what is to be locked
    python tools/bigfiles.py join       after a clone or a pull: put those files together again and check each one
    python tools/bigfiles.py status     what is whole here, what is missing, what has changed since it was cut
    python tools/bigfiles.py key        where the key is kept and whether it fits; --set to type the key in on another computer
    python tools/bigfiles.py audit      is everything that must be locked locked? (run before anything goes to a public repository)

What is carried is listed in bigfiles/carry.txt: one pattern a line, relative to the project folder. `*` is any run of
characters inside one name, `**` any run of folders, a line that starts with `!` takes files out again, `#` starts a
remark, and a line that starts with the word `lock` names files that are locked.

A plain carried file over 45 MB (GitHub refuses a file over 100 MB and warns from 50) is cut into parts of 45 MB at
most: bigfiles/<the file's own path>.part001, .part002 and so on. Smaller plain files are ordinary git files and this
tool leaves them alone.

A locked file, whatever its size, enters git only as encrypted parts: bigfiles/<its path>.lock001 and so on. Without
the key those parts are noise, so they may sit in a public repository while the file itself is given to no one. The
files themselves are named in a marked block at the end of .gitignore, and bigfiles/manifest.json holds what `join`
needs to put each one together and to prove it is right.

THE KEY is one line of text in a file outside the project: by default .sensory_triview/bigfiles.key in the user's home
folder (the variable BIGFILES_KEY names another place). `split` makes one when there is none. It never enters this
repository and this tool never prints it. Lose it and the locked files in git cannot be opened: the files on a
computer that has them are then the only copies.
On another computer the key comes by itself when carry.txt has a line `key-from <address of a private git
repository> <path of the key inside it>`: with no key file there, `join` fetches the key from that repository with
the user's own sign-in and keeps it. The repository may hold the keys of many projects, each at its own path.
`python tools/bigfiles.py key --put` puts this computer's key there and leaves everything else in it alone. A
place that can be read without signing in is refused both ways: a key there would open the locked files for
everyone. Without such a line: copy the key file to the same place on the other computer, or run `python tools/bigfiles.py key --set` there
and type or paste its one line.

How a file is locked, with Python's standard library alone: the key line is stretched by scrypt (2^16, 8, 1, a random
salt kept in the manifest) into a master key. Each file gets a random 16 byte nonce and two keys of its own, both
HMAC-SHA256 of the master key over the nonce: one for the cipher, one for the seal. The cipher is SHAKE-256 used as a
stream: block number i of 5 MB is XORed with SHAKE-256(cipher key, i). The seal is HMAC-SHA256 over the nonce and all
the encrypted bytes, checked before a joined file is kept. To see that a file has not changed since it was locked,
the manifest keeps a keyed fingerprint (HMAC-SHA256 of the file under a third key), which says nothing without the key.

On this computer, after changing a carried file (a scene saved again, a map baked again):
    python tools/bigfiles.py split
    git add -A bigfiles .gitignore
    git commit
On another computer, after `git clone` or `git pull`:
    python tools/bigfiles.py join
`join` never writes over a file that is here and differs from the committed one, unless --force is given: the file
here may be the newer one. Nothing here needs more than Python 3.9 and its standard library.
"""
import argparse
import base64
import getpass
import hashlib
import hmac
import json
import os
import pathlib
import re
import secrets
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
BIG = ROOT / "bigfiles"
MANIFEST = BIG / "manifest.json"
CARRY = BIG / "carry.txt"
IGNORE = ROOT / ".gitignore"
PART = 45 * 1024 * 1024                 # bytes: the limit and the size of a part, under GitHub's warning at 50 MB
BLOCK = 5 * 1024 * 1024                 # bytes read at a time; a part is nine of them, so a locked part ends on a block
SCRYPT = {"n": 2 ** 16, "r": 8, "p": 1}
BEGIN = "# >>> tools/bigfiles.py: carried in parts under bigfiles/ (written by the tool: do not edit by hand)"
END = "# <<< tools/bigfiles.py"


def mb(n):
    return f"{n / 1048576.0:,.1f} MB"


# ---------------------------------------------------------------- what is carried

def pattern_re(pat):
    """A pattern of carry.txt as a regular expression over a path with forward slashes."""
    out, i = "", 0
    while i < len(pat):
        if pat.startswith("**/", i):
            out, i = out + "(?:.*/)?", i + 3
        elif pat.startswith("**", i):
            out, i = out + ".*", i + 2
        elif pat[i] == "*":
            out, i = out + "[^/]*", i + 1
        elif pat[i] == "?":
            out, i = out + "[^/]", i + 1
        else:
            out, i = out + re.escape(pat[i]), i + 1
    return re.compile(out + r"\Z")


class Rules:
    """bigfiles/carry.txt: the patterns that carry, those among them that lock, and those that take out again."""

    def __init__(self):
        if not CARRY.exists():
            sys.exit(f"{CARRY} is missing: it lists what is carried")
        self.take, self.locks, self.leave, self.key_from = [], [], [], []
        for line in CARRY.read_text(encoding="utf-8").splitlines():
            line = line.split("#", 1)[0].strip()
            if line.split(None, 1)[:1] == ["key-from"] and len(line.split(None, 1)) == 2:
                words = line.split()[1:]                     # the repository's address, then the key's path inside it
                inside = (words[1] if len(words) > 1 else "bigfiles.key").replace("\\", "/").strip("/")
                if ".." in inside.split("/") or not inside:
                    sys.exit(f"{CARRY}: the key's path in a key-from line must lie inside the repository: {line}")
                self.key_from.append((words[0], inside))
                continue
            line = line.replace("\\", "/")
            if not line:
                continue
            if line.startswith("!"):
                self.leave.append(line[1:].strip().lstrip("/"))
            elif line.split(None, 1)[0] == "lock" and len(line.split(None, 1)) == 2:
                pat = line.split(None, 1)[1].lstrip("/")
                self.take.append(pat)
                self.locks.append(pat)
            else:
                self.take.append(line.lstrip("/"))
        self._take = [pattern_re(p) for p in self.take]
        self._locks = [pattern_re(p) for p in self.locks]
        self._leave = [pattern_re(p) for p in self.leave]

    def listed(self, rel):
        return any(p.match(rel) for p in self._take) and not any(p.match(rel) for p in self._leave)

    def locked(self, rel):
        return any(p.match(rel) for p in self._locks) and not any(p.match(rel) for p in self._leave)

    def lock_named(self, rel):
        """True for a path a lock line names, taken out again or not: such a file must never be a plain git file."""
        return any(p.match(rel) for p in self._locks)

    def here(self):
        """The carried files on this disk that travel as parts: {path with forward slashes: size}."""
        out = {}
        for pat in self.take:
            head = pat.split("*", 1)[0].rsplit("/", 1)[0] if "*" in pat else pat
            base = ROOT / head
            files = [base] if base.is_file() else (p for p in base.rglob("*") if p.is_file()) if base.is_dir() else []
            for p in files:
                rel = p.relative_to(ROOT).as_posix()
                if rel.startswith("bigfiles/") or "/__pycache__/" in "/" + rel or rel.endswith(".joining") or not self.listed(rel):
                    continue
                size = p.stat().st_size
                if size > PART or self.locked(rel):
                    out[rel] = size
        return out


# ---------------------------------------------------------------- the manifest and the parts

def read_manifest():
    if not MANIFEST.exists():
        return {}, None
    doc = json.loads(MANIFEST.read_text(encoding="utf-8"))
    return {e["path"]: e for e in doc["files"]}, doc.get("lock")


def write_manifest(entries, lock):
    BIG.mkdir(exist_ok=True)
    doc = {"what": "files carried in parts by tools/bigfiles.py. A plain file: its size, SHA-256 and the sizes of its parts. "
                   "A locked file: its size, nonce, seal and keyed fingerprint; its parts are encrypted.",
           "part_bytes": PART, "block_bytes": BLOCK}
    if lock:
        doc["lock"] = lock
    doc["files"] = [entries[k] for k in sorted(entries)]
    MANIFEST.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8", newline="\n")


def part_paths(entry):
    ext = "lock" if entry.get("locked") else "part"
    return [BIG / f"{entry['path']}.{ext}{k:03d}" for k in range(1, len(entry["parts"]) + 1)]


def parts_whole(entry):
    return all(p.is_file() and p.stat().st_size == n for p, n in zip(part_paths(entry), entry["parts"]))


def drop_parts(rel):
    folder = (BIG / rel).parent
    if folder.is_dir():
        name = pathlib.PurePosixPath(rel).name
        for p in list(folder.glob(name + ".part[0-9][0-9][0-9]")) + list(folder.glob(name + ".lock[0-9][0-9][0-9]")):
            p.unlink()


def write_ignore(paths):
    """The marked block at the end of .gitignore: the files themselves, which travel as parts."""
    text = IGNORE.read_text(encoding="utf-8") if IGNORE.exists() else ""
    if BEGIN in text:
        text = text[:text.index(BEGIN)].rstrip("\n") + "\n"
    esc = lambda s: re.sub(r"([\\*?\[\]])", r"\\\1", s)
    block = [BEGIN] + ["/" + esc(p) for p in sorted(paths)] + [END]
    IGNORE.write_text(text.rstrip("\n") + "\n\n" + "\n".join(block) + "\n", encoding="utf-8", newline="\n")


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(BLOCK), b""):
            h.update(block)
    return h.hexdigest()


# ---------------------------------------------------------------- the key and the cipher

def key_file():
    p = pathlib.Path(os.environ.get("BIGFILES_KEY") or pathlib.Path.home() / ".sensory_triview" / "bigfiles.key").resolve()
    if ROOT in p.parents or p == ROOT:
        sys.exit(f"the key file {p} lies inside the project folder: keep it outside, it must never enter git")
    return p


def read_secret():
    p = key_file()
    if not p.is_file():
        return None
    lines = p.read_text(encoding="utf-8").strip().splitlines()
    return lines[0].strip() if lines else None


def write_secret(secret):
    p = key_file()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(secret + "\n", encoding="utf-8", newline="\n")
    try:
        os.chmod(p, 0o600)
    except OSError:
        pass
    return p


def new_secret():
    """160 random bits as eight groups of four letters and digits: short enough to type, far too long to guess."""
    s = base64.b32encode(secrets.token_bytes(20)).decode("ascii")
    return "-".join(s[i:i + 4] for i in range(0, 32, 4))


def stretch(secret, lock):
    return hashlib.scrypt(secret.encode("utf-8"), salt=bytes.fromhex(lock["salt"]), n=lock["n"], r=lock["r"], p=lock["p"],
                          maxmem=512 * 1024 * 1024, dklen=32)


def sub(master, label, more=b""):
    return hmac.new(master, label + more, hashlib.sha256).digest()


def key_check(master):
    return sub(master, b"bigfiles key check").hex()


class NoKey(Exception):
    pass


def quiet_git(*args, anonymous=False, cwd=None):
    """Run git without a window or a question. anonymous: with no stored sign-in, as a stranger would."""
    env = dict(os.environ)
    cmd = ["git"]
    if anonymous:
        env.update(GIT_TERMINAL_PROMPT="0", GCM_INTERACTIVE="never", GIT_ASKPASS="", SSH_ASKPASS="")
        cmd += ["-c", "credential.helper="]
    return subprocess.run(cmd + list(args), capture_output=True, env=env, cwd=cwd)


def open_to_strangers(url):
    """True when the place can be read with no sign-in at all: no key may ever be kept there."""
    return os.environ.get("BIGFILES_TEST_OPEN_KEY_PLACE") != "1" and quiet_git("ls-remote", url, anonymous=True).returncode == 0


def scrub(folder):
    import shutil
    shutil.rmtree(folder, onerror=lambda f, path, e: (os.chmod(path, 0o700), f(path)))


def fetch_secret(sources):
    """The key fetched from the first private place of carry.txt's `key-from` lines that gives it, and kept in the key file.
    A place is (the address of a private git repository, the key's path inside it)."""
    import tempfile
    for url, inside in sources:
        if open_to_strangers(url):
            print(f"NOTE  {url} can be read without signing in: no key is taken from there", flush=True)
            continue
        for branch in ([], ["--branch", "main"]):          # the repository's own main line first, then one named main
            tmp = tempfile.mkdtemp(prefix="bigfiles_key_")
            try:
                found = pathlib.Path(tmp) / inside
                if quiet_git("clone", "-q", "--depth", "1", *branch, url, tmp).returncode == 0 and found.is_file():
                    lines = found.read_text(encoding="utf-8").strip().splitlines()
                    if lines and lines[0].strip():
                        p = write_secret(lines[0].strip())
                        print(f"KEY   fetched from {url} ({inside}) with your sign-in and kept in {p}", flush=True)
                        return True
            finally:
                scrub(tmp)
    return False


def put_secret(url, inside):
    """The key of this computer put into the private repository `url` as the file `inside`. Whatever else the
    repository holds, other projects' keys among it, is left as it is: the repository is fetched, the one file is
    written, and the change is pushed on top without force."""
    import tempfile
    secret = read_secret()
    if secret is None:
        sys.exit(f"no key here to put there: {key_file()} is missing")
    if open_to_strangers(url):
        sys.exit(f"{url} can be read without signing in. A key there would open the locked files for everyone: nothing was sent")
    tmp = tempfile.mkdtemp(prefix="bigfiles_key_")

    def git(*args, must=True):
        r = quiet_git(*args, cwd=tmp)
        if must and r.returncode != 0:
            scrub(tmp)
            sys.exit(f"could not put the key into {url}: git {args[0]} said {r.stderr.decode('utf-8', 'replace').strip()[:300]}")
        return r

    try:
        git("init", "-q", "-b", "main")
        git("remote", "add", "origin", url)
        heads = git("ls-remote", "--heads", "origin").stdout.decode("utf-8", "replace").split()
        names = [h.split("refs/heads/", 1)[1] for h in heads if h.startswith("refs/heads/")]
        branch = "main" if "main" in names or not names else names[0]
        if names:                                     # the repository holds something already: build on it
            git("fetch", "-q", "origin", branch)
            git("checkout", "-q", "-B", branch, "FETCH_HEAD")
        target = pathlib.Path(tmp) / inside
        if target.is_file() and target.read_text(encoding="utf-8").strip().splitlines()[:1] == [secret]:
            print(f"KEY   {url} ({inside}) holds this key already", flush=True)
            return
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(secret + "\n", encoding="utf-8", newline="\n")
        readme = pathlib.Path(tmp) / "README.md"
        if not readme.exists():
            readme.write_text("Private keys for development projects, one folder a project. Keep this repository private.\n", encoding="utf-8", newline="\n")
            git("add", "README.md")
        git("add", inside)
        git("-c", "user.name=bigfiles", "-c", "user.email=bigfiles@localhost", "commit", "-q", "-m", f"the key of {inside}")
        git("push", "-q", "origin", f"HEAD:refs/heads/{branch}")
    finally:
        if os.path.isdir(tmp):
            scrub(tmp)
    print(f"KEY   put into {url} as {inside}", flush=True)


def master_for(lock, make=False, sources=()):
    """(master key, lock record). With make, a key file and a lock record are made when there are none.
    With no key file here, the private places of carry.txt's `key-from` lines are asked first."""
    secret = read_secret()
    if secret is None and lock is not None and sources and fetch_secret(sources):
        secret = read_secret()
    if secret is None:
        if not make or lock is not None:          # files are locked already: only their own key will do, never a new one
            raise NoKey(f"no key here: copy the key file to {key_file()}, or run `python tools/bigfiles.py key --set`"
                        + (f" (it could not be fetched from {', '.join(u for u, _ in sources)}: sign in to it first)" if sources else ""))
        p = write_secret(new_secret())
        secret = read_secret()
        print(f"KEY   a new key was made and kept in {p}. It is not in git. "
              + ("`python tools/bigfiles.py key --put` puts it into the private place of carry.txt." if sources else "Copy that file to your other computer."), flush=True)
    if lock is None:
        if not make:
            raise NoKey("the manifest holds no lock record")
        lock = dict(SCRYPT, kdf="scrypt", salt=secrets.token_bytes(16).hex())
        lock["check"] = key_check(stretch(secret, lock))
    master = stretch(secret, lock)
    if not hmac.compare_digest(key_check(master), lock["check"]):
        raise NoKey(f"the key in {key_file()} is not the one these files were locked with")
    return master, lock


def xor(a, b):
    return (int.from_bytes(a, "little") ^ int.from_bytes(b, "little")).to_bytes(len(a), "little")


def stream(enc_key, i, n):
    return hashlib.shake_256(enc_key + i.to_bytes(8, "big")).digest(n)


def keyed_fingerprint(master, path):
    h = hmac.new(sub(master, b"bigfiles fingerprint"), digestmod=hashlib.sha256)
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(BLOCK), b""):
            h.update(block)
    return h.hexdigest()


# ---------------------------------------------------------------- split

def cut_plain(rel, size):
    src, sizes = ROOT / rel, []
    with open(src, "rb") as fh:
        k = 0
        while True:
            k += 1
            dst, wrote = BIG / f"{rel}.part{k:03d}", 0
            with open(dst, "wb") as out:
                while wrote < PART:
                    block = fh.read(min(BLOCK, PART - wrote))
                    if not block:
                        break
                    out.write(block)
                    wrote += len(block)
            if wrote == 0:
                dst.unlink()
                break
            sizes.append(wrote)
            if wrote < PART:
                break
    assert sum(sizes) == size, (rel, sum(sizes), size)
    return {"path": rel, "bytes": size, "sha256": sha256_of(src), "parts": sizes}


def cut_locked(rel, size, master, keyed):
    src, sizes = ROOT / rel, []
    nonce = secrets.token_bytes(16)
    enc_key, mac_key = sub(master, b"bigfiles cipher", nonce), sub(master, b"bigfiles seal", nonce)
    seal = hmac.new(mac_key, nonce, hashlib.sha256)
    i = 0
    with open(src, "rb") as fh:
        k = 0
        while True:
            k += 1
            dst, wrote = BIG / f"{rel}.lock{k:03d}", 0
            with open(dst, "wb") as out:
                while wrote < PART:
                    block = fh.read(BLOCK)
                    if not block:
                        break
                    sealed = xor(block, stream(enc_key, i, len(block)))
                    i += 1
                    seal.update(sealed)
                    out.write(sealed)
                    wrote += len(sealed)
            if wrote == 0 and (k > 1 or size > 0):
                dst.unlink()
                break
            sizes.append(wrote)
            if wrote < PART:
                break
    assert sum(sizes) == size, (rel, sum(sizes), size)
    seal.update(size.to_bytes(8, "big"))
    return {"path": rel, "bytes": size, "locked": True, "nonce": nonce.hex(), "mac": seal.hexdigest(), "keyed": keyed, "parts": sizes}


def split(a):
    rules = Rules()
    here = rules.here()
    entries, lock = read_manifest()
    master = None
    if any(rules.locked(rel) for rel in here):
        if a.rekey:
            lock = None
        try:
            master, lock = master_for(lock, make=True, sources=rules.key_from)
        except NoKey as e:
            sys.exit(f"{e}\n(`split --rekey` locks everything again with the key that is here)")
    cut = kept = 0
    for rel, size in sorted(here.items()):
        old, locked = entries.get(rel), rules.locked(rel)
        if locked:
            keyed = keyed_fingerprint(master, ROOT / rel)
            if old and old.get("locked") and old["bytes"] == size and old["keyed"] == keyed and parts_whole(old) and not a.rekey:
                kept += 1
                continue
        elif old and not old.get("locked") and old["bytes"] == size and parts_whole(old) and old["sha256"] == sha256_of(ROOT / rel):
            kept += 1
            continue
        drop_parts(rel)
        (BIG / rel).parent.mkdir(parents=True, exist_ok=True)
        entries[rel] = cut_locked(rel, size, master, keyed) if locked else cut_plain(rel, size)
        cut += 1
        print(f"{'lock ' if locked else 'cut  '} {rel}: {mb(size)} into {len(entries[rel]['parts'])} part{'s' if len(entries[rel]['parts']) != 1 else ''}", flush=True)
    for rel in sorted(set(entries) - set(here)):
        if not rules.listed(rel):
            if a.prune:
                drop_parts(rel)
                del entries[rel]
                print(f"gone  {rel}: no longer listed in carry.txt, its parts removed", flush=True)
            else:
                print(f"NOTE  {rel}: no longer listed in carry.txt; its parts stay until `split --prune`", flush=True)
        elif not (ROOT / rel).exists():
            print(f"NOTE  {rel}: not on this disk; its parts stay as committed (run `join` to have it here)", flush=True)
        else:                                     # a plain file that has shrunk under the limit: git carries it as itself
            drop_parts(rel)
            del entries[rel]
            print(f"small {rel}: under the limit now, its parts removed", flush=True)
    if not any(e.get("locked") for e in entries.values()):
        lock = None
    write_manifest(entries, lock)
    write_ignore(entries)
    locked = [e for e in entries.values() if e.get("locked")]
    print(f"SPLIT DONE: {cut} cut, {kept} unchanged; {len(entries)} files of {mb(sum(e['bytes'] for e in entries.values()))} carried in "
          f"{sum(len(e['parts']) for e in entries.values())} parts, {len(locked)} of them locked ({mb(sum(e['bytes'] for e in locked))})", flush=True)


# ---------------------------------------------------------------- join

def join_one(e, master):
    """Write the file of a manifest entry from its parts. True when it is right and in place."""
    rel, dst = e["path"], ROOT / e["path"]
    dst.parent.mkdir(parents=True, exist_ok=True)
    tmp = dst.with_name(dst.name + ".joining")
    if e.get("locked"):
        nonce = bytes.fromhex(e["nonce"])
        enc_key, mac_key = sub(master, b"bigfiles cipher", nonce), sub(master, b"bigfiles seal", nonce)
        seal, i = hmac.new(mac_key, nonce, hashlib.sha256), 0
        with open(tmp, "wb") as out:
            for p in part_paths(e):
                with open(p, "rb") as fh:
                    for sealed in iter(lambda: fh.read(BLOCK), b""):
                        seal.update(sealed)
                        out.write(xor(sealed, stream(enc_key, i, len(sealed))))
                        i += 1
        seal.update(e["bytes"].to_bytes(8, "big"))
        right = hmac.compare_digest(seal.hexdigest(), e["mac"]) and tmp.stat().st_size == e["bytes"]
    else:
        h = hashlib.sha256()
        with open(tmp, "wb") as out:
            for p in part_paths(e):
                with open(p, "rb") as fh:
                    for block in iter(lambda: fh.read(BLOCK), b""):
                        out.write(block)
                        h.update(block)
        right = h.hexdigest() == e["sha256"] and tmp.stat().st_size == e["bytes"]
    if not right:
        tmp.unlink()
        return False
    tmp.replace(dst)
    return True


def same_as_committed(e, master):
    p = ROOT / e["path"]
    if p.stat().st_size != e["bytes"]:
        return False
    return hmac.compare_digest(keyed_fingerprint(master, p), e["keyed"]) if e.get("locked") else sha256_of(p) == e["sha256"]


def join(a):
    rules = Rules()
    entries, lock = read_manifest()
    master, why = None, None
    if any(e.get("locked") for e in entries.values()):
        try:
            master, lock = master_for(lock, sources=rules.key_from)
        except NoKey as e:
            why = str(e)
    made = whole = bad = nokey = 0
    for rel, e in sorted(entries.items()):
        dst = ROOT / rel
        if e.get("locked") and master is None:
            nokey += 1
            continue
        if dst.is_file():
            if same_as_committed(e, master):
                whole += 1
                continue
            if not a.force:
                bad += 1
                print(f"DIFFERS {rel}: the file here is not the committed one and is left as it is "
                      f"(`split` to commit this one, `join --force` to replace it)", flush=True)
                continue
        if not parts_whole(e):
            bad += 1
            print(f"PARTS MISSING {rel}: its parts under bigfiles/ are not all here; pull again", flush=True)
            continue
        if join_one(e, master):
            made += 1
            print(f"made  {rel}: {mb(e['bytes'])} from {len(e['parts'])} part{'s' if len(e['parts']) != 1 else ''}, "
                  f"{'unlocked and its seal checked' if e.get('locked') else 'fingerprint checked'}", flush=True)
        else:
            bad += 1
            print(f"FAILED {rel}: the parts do not give the committed file", flush=True)
    if nokey:
        print(f"LOCKED {nokey} files were left: {why}", flush=True)
    print(f"JOIN {'DONE' if not (bad or nokey) else 'INCOMPLETE'}: {made} made, {whole} already whole, {bad} not right, {nokey} waiting for the key", flush=True)
    if bad or nokey:
        sys.exit(1)


# ---------------------------------------------------------------- status, key, audit

def status(a):
    rules = Rules()
    here = rules.here()
    entries, lock = read_manifest()
    master = None
    if any(e.get("locked") for e in entries.values()):
        try:
            master, lock = master_for(lock, sources=rules.key_from)
        except NoKey as e:
            print(f"NOTE  {e}; locked files are compared by size only", flush=True)
    wrong = 0
    for rel in sorted(set(entries) | set(here)):
        e, p = entries.get(rel), ROOT / rel
        if e is None:
            state = "NOT CUT YET (run split)"
        elif bool(e.get("locked")) != rules.locked(rel) and rules.listed(rel):
            state = "LOCK CHANGED in carry.txt (run split)"
        elif not parts_whole(e):
            state = "PARTS MISSING"
        elif not p.is_file():
            state = "not on this disk (run join)"
        elif p.stat().st_size != e["bytes"]:
            state = "CHANGED since it was cut (run split)"
        elif not a.quick and (master is not None or not e.get("locked")) and not same_as_committed(e, master):
            state = "CHANGED since it was cut (run split)"
        else:
            state = "whole"
        wrong += state != "whole"
        kind = "locked" if (e or {}).get("locked") or (e is None and rules.locked(rel)) else "plain "
        if state != "whole" or not a.brief:
            print(f"{state:38s} {kind} {mb(e['bytes'] if e else here[rel]):>11s}  {rel}", flush=True)
    locked = [e for e in entries.values() if e.get("locked")]
    print(f"STATUS: {len(entries)} files of {mb(sum(e['bytes'] for e in entries.values()))} in the manifest, {len(locked)} of them locked; "
          f"{wrong} not whole here", flush=True)


def key(a):
    p = key_file()
    rules = Rules()
    entries, lock = read_manifest()
    if a.put:
        if not rules.key_from:
            sys.exit("carry.txt has no `key-from` line: it names the private place the key is kept in")
        put_secret(*rules.key_from[0])
    if not p.is_file() and not a.set and lock is not None and rules.key_from:
        fetch_secret(rules.key_from)
    if a.set:
        one = getpass.getpass("The key, one line (it is not shown): ").strip()
        if not one:
            sys.exit("nothing typed; the key file is as it was")
        if lock is None and one != getpass.getpass("Once more: ").strip():
            sys.exit("the two do not agree; the key file is as it was")
        if lock is not None and not hmac.compare_digest(key_check(stretch(one, lock)), lock["check"]):
            sys.exit("that is not the key these files were locked with; the key file is as it was\n"
                     "(to lock everything with a new key: put it in the key file by hand, then `split --rekey`)")
        write_secret(one)
    print(f"key file: {p} ({'there' if p.is_file() else 'NOT THERE'})", flush=True)
    if lock is None:
        print("nothing in the manifest is locked yet", flush=True)
    elif p.is_file():
        fits = hmac.compare_digest(key_check(stretch(read_secret(), lock)), lock["check"])
        print("it fits the locked files" if fits else "IT DOES NOT FIT the locked files", flush=True)
        if not fits:
            sys.exit(1)
    else:
        sys.exit(1)


def audit(a):
    """Nothing that a lock line names may be in git as itself or as plain parts. Exit code 1 if something is."""
    rules = Rules()
    entries, lock = read_manifest()
    tracked = subprocess.run(["git", "-C", str(ROOT), "ls-files", "-z"], capture_output=True, check=True).stdout.decode("utf-8").split("\0")
    faults = []
    for rel in filter(None, tracked):
        if rules.lock_named(rel):
            faults.append(f"in git as itself: {rel}")
        m = re.match(r"bigfiles/(.+)\.part\d{3}\Z", rel)
        if m and rules.lock_named(m.group(1)):
            faults.append(f"in git as a plain part: {rel}")
        if rel.endswith(".joining") or rel.endswith(".key"):
            faults.append(f"should not be in git: {rel}")
    for rel, e in entries.items():
        if rules.lock_named(rel) and not e.get("locked"):
            faults.append(f"listed to be locked but cut plain: {rel} (run split)")
    for rel, size in rules.here().items():
        if rules.locked(rel) and rel not in entries:
            faults.append(f"to be locked but not cut yet: {rel} (run split)")
    n = sum(1 for e in entries.values() if e.get("locked"))
    for f in faults:
        print("FAULT", f, flush=True)
    print(f"AUDIT {'PASSED' if not faults else 'FAILED'}: {n} locked files in the manifest, {len(faults)} faults", flush=True)
    if faults:
        sys.exit(1)


def main():
    ap = argparse.ArgumentParser(description="Big files and locked files carried through git in parts")
    ap.add_argument("what", choices=("split", "join", "status", "key", "audit"))
    ap.add_argument("--force", action="store_true", help="join: replace a file here that differs from the committed one")
    ap.add_argument("--prune", action="store_true", help="split: remove the parts of files that carry.txt no longer lists")
    ap.add_argument("--rekey", action="store_true", help="split: lock every locked file again with the key that is in the key file now")
    ap.add_argument("--quick", action="store_true", help="status: compare sizes only, do not read the files")
    ap.add_argument("--brief", action="store_true", help="status: list only what is not whole")
    ap.add_argument("--set", action="store_true", help="key: type the key in and keep it in the key file")
    ap.add_argument("--put", action="store_true", help="key: put this computer's key into the private place of carry.txt's key-from line")
    a = ap.parse_args()
    {"split": split, "join": join, "status": status, "key": key, "audit": audit}[a.what](a)


if __name__ == "__main__":
    main()
