# Sensory Tri-View: the working folder

What this folder holds is said at the top of `.gitignore`. This page says how to stand the folder up on another computer.

## After a clone or a pull

```
python tools/bigfiles.py join
```

Big files and locked files travel in parts under `bigfiles`. This writes each one where it belongs and checks it. Any Python from 3.9 on will do, with nothing added to it.

To see what is whole and what is missing:

```
python tools/bigfiles.py status
```

## The key

The scanned head the man's skin comes from, and the two scenes that carry its maps, are in git only as encrypted parts. Without the key those parts are noise, so they can sit in a public repository while the files themselves are given to no one. The scan is free to use with credit to Digital Reality Lab, but its files may not be given on.

The key is one line of text in one small file, kept outside this folder and never in git:

```
<your home folder>/.sensory_triview/bigfiles.key
```

On another computer, do one of these once, before `join`:

- Copy that file to the same place there.
- Or run `python tools/bigfiles.py key --set` there and type or paste its one line.

Keep a copy of the key somewhere safe. Without it the locked files in git cannot be opened, and the files on a computer that has them are then the only copies.

## Before a commit, after a carried file has changed

```
python tools/bigfiles.py split
git add -A bigfiles .gitignore
```

Then commit as usual. A new scene of record or a new folder of assets needs its own line in `bigfiles/carry.txt` first. A line that starts with `lock` there means its files are encrypted.

Before anything goes to a public repository:

```
python tools/bigfiles.py audit
```

It fails if a file that must be locked is in git unlocked. The export to the Diagrams repository runs it by itself.

## What the computer needs

- Blender 5.2.3 at `C:\Program Files\Blender Foundation\Blender 5.2\blender.exe`. The tools take that path from `tools/dev_showcase.py`.
- A graphics card that Cycles can use. A frame of the man takes up to 3.8 GB of graphics memory.
- Python with numpy, scipy and Pillow, for the tools that run outside Blender.
- FFmpeg on the path, for the videos.

## The man of rung 3

`scenes/rung3_man_c.blend` holds him alone and `scenes/rung3_sill_c.blend` holds him at the sill, both as he passed, with all his pictures inside the files. They render as they are. A check that everything arrived, with the full path of this folder in place of `<folder>`:

```
blender -b --python <folder>/rungs/rung3.py -- still --view third --frame 1996 --blend <folder>/scenes/rung3_sill_c.blend --samples 64 --exposure-offset -1.5 --denoiser oidn --look <folder>/renders/rung3/check_third_1996.png
```

Building him anew needs two things more:

- The generator MPFB, a Blender extension from extensions.blender.org, installed for the user. Version 2.0.18 was used.
- Its asset packs put where it finds them, once on each computer:

```
blender -b --python <folder>/tools/man_packs.py -- <folder>/assets/open/zips
```

## What does not travel

- Pictures, frames and videos under `renders`. They are rendered again. The True-Person view's own inputs under `renders/rung2p` are among them, and `tools/run_rung2.py` makes them.
- Copies of what a zip beside them already holds. `bigfiles/carry.txt` ends with the lines that unzip them again.
- The key.
- The notes and the memory that Claude's sessions keep outside this folder. The notes of each rung are copied into `scratch`.
