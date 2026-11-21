"""The man (rung 3): put the generator's asset packs into the add-on's own data folder for this user, and list what they hold.

    blender -b --python tools/man_packs.py -- assets/open/zips

Needed once on each computer before `rungs/rung3.py man` can build him: the generator MPFB (a Blender extension,
installed for the user from extensions.blender.org) finds skins, eyes, teeth, brows, lashes and clothes only there.
A pack that is in already is not unpacked again.
The zips are data from the network: opened with the standard zipfile through the add-on's own extractor, never run."""
import os
import pathlib
import sys
import traceback
import zipfile

import addon_utils
import bpy

try:
    zips = pathlib.Path(sys.argv[sys.argv.index("--") + 1])
    addon_utils.enable("bl_ext.blender_org.mpfb", default_set=True)
    from bl_ext.blender_org.mpfb.services import LocationService
    from bl_ext.blender_org.mpfb.services.assetservice import AssetService
    data_dir = pathlib.Path(LocationService.get_user_data())
    data_dir.mkdir(parents=True, exist_ok=True)
    print("PACKS user data:", data_dir, flush=True)
    marker = data_dir / "rung3_packs_installed.txt"
    done = set(marker.read_text(encoding="utf-8").split()) if marker.exists() else set()
    for z in sorted(zips.glob("*.zip")):
        if z.name in done:
            print("PACKS already in:", z.name, flush=True)
            continue
        check = AssetService.check_asset_pack_zip(str(z))
        if check is not None:
            print("PACKS check says", check, "for", z.name, "- trying the add-on's own fix", flush=True)
            res = AssetService.fix_and_extract_asset_pack_zip(str(z), str(data_dir))
            if res is not None:
                print("PACKS FAILED", z.name, res, flush=True)
                continue
        else:
            with zipfile.ZipFile(z, "r") as zf:
                root = os.path.realpath(data_dir)
                for n in zf.namelist():
                    target = os.path.realpath(os.path.join(root, n))
                    if not target.startswith(root):
                        raise RuntimeError(f"{z.name}: a path leaves the data folder: {n}")
                zf.extractall(data_dir)
        done.add(z.name)
        marker.write_text("\n".join(sorted(done)), encoding="utf-8")
        print("PACKS installed:", z.name, flush=True)
    AssetService.update_all_asset_lists()
    for sub in sorted(p for p in data_dir.iterdir() if p.is_dir()):
        kinds = {}
        for ext in ("mhmat", "mhclo", "proxy", "mhskel", "bvh", "json"):
            files = sorted(sub.rglob(f"*.{ext}"))
            if files:
                kinds[ext] = files
        if not kinds:
            continue
        for ext, files in kinds.items():
            names = [f.stem for f in files]
            print(f"PACKS {sub.name} .{ext} ({len(names)}): " + ", ".join(names[:90]), flush=True)
    print("PACKS DONE", flush=True)
except Exception:
    traceback.print_exc()
    sys.exit(1)
