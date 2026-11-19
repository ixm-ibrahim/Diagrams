"""triview: scene builders, the engine and render helpers for the Sensory Tri-View piece.

Everything here runs inside Blender's own Python (blender.exe -b --python ...), except
that engine.py and tags.py are kept free of Blender objects so the rules can move to
another host later. The modules are kept apart from any one rung so later rungs reuse them:

- geo:        mesh construction with bmesh (no edit-mode operators, which fail headless)
- materials:  Cycles and EEVEE materials built from nodes, and the model's shared shading
- figure:     the stand-in mannequin's joint tables and poses (rung 0's still figure)
- body:       the mannequin animated over the whole chain: joint Empties, constrained limbs,
              the motion schedule, the phone and the blanket
- room:       the photoreal room with the man, the phone and the cameras, still (rung 0) or
              animated with every surface tagged (rung 1)
- tags:       the vocabulary the art and the engine share: regions, body parts, chains, colours
- engine:     the rules: the True-Person view computed per frame from the scene state and the
              sense timeline, as a FrameState the art draws
- mindscene:  the True-Person art for rung 1: the ghost, the soul, the model's plates and the
              pools of signal primitives, and the bake of FrameStates into keyframes
- mind:       rung 0's hand-drawn model (kept so rung 0 still runs)
- cameras:    the Third-Person camera's road, the First-Person camera on the eyes, and the
              camera roads of the four moves (rung 2); no Blender objects
- eye:        the First-Person eye's behaviours: closures and blinks, the eye's own exposure
              over the dawn, the lit eyelids, the edge tint (rung 2); no Blender objects
- anim:       bulk keyframe writing on 5.2's slotted actions, and motion helpers
- render:     engine settings, timed renders, GPU memory sampling, exposure search, bloom

Axes: x east, y north, z up, metres. The room's floor corner is the origin.
"""

__version__ = "0.3.0"
