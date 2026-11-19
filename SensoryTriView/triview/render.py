"""Engine settings, timed renders, GPU memory sampling and an exposure search."""
import json
import math
import os
import subprocess
import threading
import time

import bpy
import numpy as np

NVIDIA_SMI = "nvidia-smi"


class GpuMonitor:
    """Samples nvidia-smi's used memory on a thread while a render runs.

    Reports the baseline before the render and the peak during it, in MiB, or None
    when nvidia-smi cannot be run.
    """

    def __init__(self, interval=0.5):
        self.interval = interval
        self.samples = []
        self.baseline = None
        self._stop = threading.Event()
        self._thread = None

    @staticmethod
    def query():
        try:
            r = subprocess.run([NVIDIA_SMI, "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
                               capture_output=True, text=True, timeout=5,
                               creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            return int(r.stdout.strip().splitlines()[0])
        except Exception:
            return None

    def start(self):
        self.baseline = self.query()
        if self.baseline is None:
            return self

        def run():
            while not self._stop.is_set():
                v = self.query()
                if v is not None:
                    self.samples.append(v)
                self._stop.wait(self.interval)

        self._thread = threading.Thread(target=run, daemon=True)
        self._thread.start()
        return self

    def stop(self):
        if self._thread is not None:
            self._stop.set()
            self._thread.join(timeout=10)
        v = self.query()
        if v is not None:
            self.samples.append(v)
        return {"baseline_mb": self.baseline, "peak_mb": max(self.samples) if self.samples else None}


def enable_gpu(device_type="OPTIX"):
    """Switch Cycles to the given device type and use only devices of that type."""
    prefs = bpy.context.preferences.addons["cycles"].preferences
    prefs.compute_device_type = device_type
    prefs.get_devices()
    used = []
    for d in prefs.devices:
        d.use = d.type == device_type
        if d.use:
            used.append(d.name)
    print(f"render: {device_type} devices in use: {used}", flush=True)
    return used


def setup_cycles(scene, samples=128, adaptive=True, denoise=True, device_type="OPTIX", view_transform="AgX"):
    scene.render.engine = "CYCLES"
    used = enable_gpu(device_type)
    c = scene.cycles
    c.device = "GPU" if used else "CPU"
    c.samples = samples
    c.use_adaptive_sampling = adaptive
    c.adaptive_threshold = 0.01
    c.use_denoising = denoise
    if denoise:
        try:
            c.denoiser = "OPTIX"
        except TypeError:
            c.denoiser = "OPENIMAGEDENOISE"
        c.denoising_use_gpu = True
    scene.view_settings.view_transform = view_transform
    scene.view_settings.look = "None"
    return used


def setup_eevee(scene, samples=64, view_transform="Standard"):
    scene.render.engine = "BLENDER_EEVEE"
    scene.eevee.taa_render_samples = samples
    scene.eevee.use_raytracing = False
    scene.eevee.use_shadows = False
    scene.view_settings.view_transform = view_transform
    scene.view_settings.look = "None"


def set_output(scene, size, path, color_mode="RGB", depth="8"):
    scene.render.resolution_x, scene.render.resolution_y = int(size[0]), int(size[1])
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = color_mode
    scene.render.image_settings.color_depth = depth
    scene.render.filepath = str(path)


def image_stats(path):
    """Mean display value and the fractions of dark and bright pixels of a rendered PNG."""
    try:
        img = bpy.data.images.load(str(path), check_existing=False)
    except Exception as e:
        return {"mean": None, "error": str(e)}
    try:
        w, h = img.size
        ch = img.channels
        arr = np.empty(w * h * ch, dtype=np.float32)
        img.pixels.foreach_get(arr)
        rgb = arr.reshape(h, w, ch)[:, :, :3]
        lum = rgb.mean(axis=2)
        return {
            "mean": round(float(lum.mean()), 4),
            "p99": round(float(np.percentile(lum, 99)), 4),
            "max": round(float(lum.max()), 4),
            "dark_fraction": round(float((lum < 0.02).mean()), 4),
            "bright_fraction": round(float((lum > 0.9).mean()), 4),
        }
    finally:
        bpy.data.images.remove(img)


def render_view(scene, camera, size, path, exposure=None, hide_from_camera=(), label=None, quiet=False):
    """Render one still of scene through camera at size to path and time it."""
    scene.camera = camera
    set_output(scene, size, path)
    if exposure is not None:
        scene.view_settings.exposure = exposure
    saved = [(o, o.visible_camera) for o in hide_from_camera]
    for o in hide_from_camera:
        o.visible_camera = False
    mon = GpuMonitor().start()
    t0 = time.perf_counter()
    try:
        bpy.ops.render.render(write_still=True, scene=scene.name)
    finally:
        for o, v in saved:
            o.visible_camera = v
    seconds = time.perf_counter() - t0
    gpu = mon.stop()
    info = {
        "view": label or camera.name,
        "scene": scene.name,
        "engine": scene.render.engine,
        "size": [int(size[0]), int(size[1])],
        "seconds": round(seconds, 2),
        "exposure": round(float(scene.view_settings.exposure), 3),
        "gpu": gpu,
        "path": str(path),
    }
    info.update(image_stats(path))
    if not quiet:
        print("RENDER:", json.dumps(info), flush=True)
    return info


def find_exposure(scene, camera, target, size=(320, 144), samples=16, start=None, iterations=4,
                  hide_from_camera=(), tmp_dir=None, lo=-6.0, hi=14.0, tolerance=0.12, metric="mean"):
    """Nudge the view exposure until a small preview's display value reaches target.

    metric is "mean" (the whole frame's average: a room seen from a corner) or "p99" (the
    brightest percent: an eye on a phone screen, which sets its own exposure). The concept
    wants the room lit by the sky alone and the exposure raised rather than lights added,
    so the exposure is found rather than guessed. Works for either engine.
    """
    is_cycles = scene.render.engine == "CYCLES"
    if is_cycles:
        saved = (scene.cycles.samples, scene.cycles.use_denoising)
        scene.cycles.samples = samples
        scene.cycles.use_denoising = False
    else:
        saved = scene.eevee.taa_render_samples
        scene.eevee.taa_render_samples = max(4, samples // 2)
    exp = scene.view_settings.exposure if start is None else start
    tmp_dir = tmp_dir or bpy.app.tempdir
    path = os.path.join(str(tmp_dir), f"exposure_probe_{camera.name}.png")
    try:
        for i in range(iterations):
            info = render_view(scene, camera, size, path, exposure=exp, hide_from_camera=hide_from_camera,
                               label=f"exposure_probe:{camera.name}", quiet=True)
            value = info.get(metric) or 0.0
            if value <= 1e-5:
                step = 2.0
            elif value >= 0.995 and metric != "mean":
                step = -1.0  # clipped: the measure says nothing yet, come down a stop
            else:
                step = math.log2(target / value) * 0.9
            print(f"exposure: {camera.name} pass {i} exposure {exp:+.2f} {metric} {value:.4f} target {target:.3f}",
                  flush=True)
            if abs(step) < math.log2(1.0 + tolerance):
                break
            exp = min(hi, max(lo, exp + step))
    finally:
        if is_cycles:
            scene.cycles.samples, scene.cycles.use_denoising = saved
        else:
            scene.eevee.taa_render_samples = saved
        try:
            os.remove(path)
        except OSError:
            pass
    scene.view_settings.exposure = exp
    return exp


def bloom_compositor(scene, threshold=1.0, strength=0.35, size=0.6, quality="High"):
    """Glare bloom through the 5.2 compositor: a node group on scene.compositing_node_group
    whose output is a Group Output node (the old Composite node no longer exists)."""
    ng = bpy.data.node_groups.new(f"{scene.name}_Compositor", "CompositorNodeTree")
    ng.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    rl = ng.nodes.new("CompositorNodeRLayers")
    try:
        rl.scene = scene
    except Exception as e:
        print("render: could not set Render Layers scene:", e, flush=True)
    glare = ng.nodes.new("CompositorNodeGlare")
    glare.inputs["Type"].default_value = "Bloom"
    glare.inputs["Quality"].default_value = quality
    glare.inputs["Threshold"].default_value = threshold
    glare.inputs["Strength"].default_value = strength
    glare.inputs["Size"].default_value = size
    out = ng.nodes.new("NodeGroupOutput")
    ng.links.new(rl.outputs["Image"], glare.inputs["Image"])
    ng.links.new(glare.outputs["Image"], out.inputs["Image"])
    rl.location = (-400, 0)
    glare.location = (0, 0)
    out.location = (300, 0)
    scene.compositing_node_group = ng
    scene.render.use_compositing = True
    return ng


def disable_compositor(scene):
    scene.render.use_compositing = False
    scene.compositing_node_group = None
