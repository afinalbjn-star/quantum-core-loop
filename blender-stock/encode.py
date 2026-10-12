import json
import os
import re
import shutil
import subprocess
import sys

FPS = int(os.environ.get("FPS", "30"))
EXPECTED_FRAMES = int(os.environ.get("EXPECTED_FRAMES", "150"))
FFMPEG = shutil.which("ffmpeg")
FFPROBE = shutil.which("ffprobe")

def discover_frames(src, prefix="frame_"):
    pat = re.compile(r"^%s(\d+)\.png$" % re.escape(prefix))
    found = []
    if not os.path.exists(src):
        return found
    for name in os.listdir(src):
        m = pat.match(name)
        if m:
            found.append(int(m.group(1)))
    return sorted(found)

def run(cmd):
    print("[encode] %s" % " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True)

def main():
    if not FFMPEG:
        sys.exit("ffmpeg not found on PATH")

    src = sys.argv[1] if len(sys.argv) > 1 else "render"
    outdir = sys.argv[2] if len(sys.argv) > 2 else "output"
    os.makedirs(outdir, exist_ok=True)

    numbers = discover_frames(src)
    if not numbers:
        sys.exit("no frames matching frame_####.png in %s" % src)

    first = numbers[0]
    count = len(numbers)
    print(f"[encode] Found {count} frames ({first}..{numbers[-1]})")

    prores_mov = os.path.join(outdir, "quantum_ai_core_prores4444_alpha.mov")
    webm_alpha = os.path.join(outdir, "quantum_ai_core_transparent.webm")
    preview_mp4 = os.path.join(outdir, "quantum_ai_core_preview_dark.mp4")
    contact_sheet = os.path.join(outdir, "quantum_core_contact_sheet.png")

    # 1. ProRes 4444 with Alpha (Adobe Stock Master Delivery)
    print("[encode] 1/4 Encoding Apple ProRes 4444 with Alpha...")
    run([
        FFMPEG, "-y",
        "-framerate", str(FPS),
        "-start_number", str(first),
        "-i", os.path.join(src, "frame_%04d.png"),
        "-frames:v", str(count),
        "-c:v", "prores_ks",
        "-profile:v", "4",  # 4 = ProRes 4444 (RGBA)
        "-pix_fmt", "yuva444p10le",
        "-vendor", "apl0",
        prores_mov
    ])

    # 2. WebM with VP9 Alpha (Web Transparent Video)
    print("[encode] 2/4 Encoding WebM VP9 with Alpha...")
    run([
        FFMPEG, "-y",
        "-framerate", str(FPS),
        "-start_number", str(first),
        "-i", os.path.join(src, "frame_%04d.png"),
        "-frames:v", str(count),
        "-c:v", "libvpx-vp9",
        "-pix_fmt", "yuva420p",
        "-b:v", "0",
        "-crf", "18",
        "-auto-alt-ref", "0",
        webm_alpha
    ])

    # 3. H.264 MP4 Preview (over Dark Slate Backdrop)
    print("[encode] 3/4 Encoding MP4 Preview with Dark Studio Backdrop...")
    run([
        FFMPEG, "-y",
        "-f", "lavfi", "-i", f"color=c=0x0b0e14:s=1920x1080:r={FPS}",
        "-framerate", str(FPS),
        "-start_number", str(first),
        "-i", os.path.join(src, "frame_%04d.png"),
        "-filter_complex", "[0:v][1:v]overlay=shortest=1",
        "-frames:v", str(count),
        "-c:v", "libx264",
        "-preset", "slow",
        "-crf", "16",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        preview_mp4
    ])

    # 4. Contact Sheet (Grid of 16 sample frames)
    print("[encode] 4/4 Generating Contact Sheet...")
    step = max(1, count // 16)
    sample_frames = [numbers[i] for i in range(0, count, step)][:16]
    run([
        FFMPEG, "-y",
        "-framerate", str(FPS),
        "-start_number", str(first),
        "-i", os.path.join(src, "frame_%04d.png"),
        "-filter_complex", "tile=4x4",
        "-frames:v", "1",
        contact_sheet
    ])

    print("[encode] ALL DELIVERY FILES READY IN:", outdir)
    for f in os.listdir(outdir):
        sz = os.path.getsize(os.path.join(outdir, f)) / (1024 * 1024)
        print(f" - {f} ({sz:.2f} MB)")

if __name__ == "__main__":
    main()
