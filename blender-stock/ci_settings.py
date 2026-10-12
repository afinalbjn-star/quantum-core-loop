import os
import bpy

FRAME_START = int(os.environ.get("START_FRAME", "1"))
FRAME_END = int(os.environ.get("END_FRAME", "150"))
SAMPLES = int(os.environ.get("SAMPLES", "32"))
ENGINE = os.environ.get("ENGINE", "cycles")
FRAMES_DIR = os.environ.get("FRAMES_DIR", "render")
RES_X = int(os.environ.get("RES_X", "1920"))
RES_Y = int(os.environ.get("RES_Y", "1080"))
FPS = int(os.environ.get("FPS", "30"))

scene = bpy.context.scene
render = scene.render

render.engine = "CYCLES" if ENGINE == "cycles" else "BLENDER_EEVEE"
render.resolution_x = RES_X
render.resolution_y = RES_Y
render.resolution_percentage = 100
render.fps = FPS
render.fps_base = 1.0

scene.frame_start = FRAME_START
scene.frame_end = FRAME_END

# Critical: 100% Transparent Alpha Channel
render.film_transparent = True
render.image_settings.file_format = "PNG"
render.image_settings.color_mode = "RGBA"
render.image_settings.color_depth = "16"
render.image_settings.compression = 15
render.use_overwrite = True
render.use_file_extension = True
render.use_placeholder = False

render.filepath = os.path.join(FRAMES_DIR, "frame_")

if render.engine == "CYCLES":
    cy = scene.cycles
    cy.device = "CPU"
    cy.samples = SAMPLES
    cy.preview_samples = 16
    cy.use_adaptive_sampling = True
    cy.adaptive_threshold = 0.015
    cy.use_denoising = True
    cy.max_bounces = 6
    cy.diffuse_bounces = 3
    cy.glossy_bounces = 3
    cy.transmission_bounces = 4
elif hasattr(scene, 'eevee'):
    scene.eevee.use_raytracing = True
    if hasattr(scene.eevee, 'taa_render_samples'):
        scene.eevee.taa_render_samples = SAMPLES

print(f"[CI_SETTINGS] Configured: {render.engine}, {RES_X}x{RES_Y} @ {FPS}fps, Frames {FRAME_START}..{FRAME_END}, RGBA 16-bit Alpha")
