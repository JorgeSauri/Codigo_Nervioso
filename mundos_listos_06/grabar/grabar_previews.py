#!/usr/bin/env python3
"""Captura previews deterministas (Playwright + FFmpeg). CC0."""
from __future__ import annotations

import argparse
import base64
import subprocess
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
ART = Path("/opt/cursor/artifacts")
ART.mkdir(parents=True, exist_ok=True)

SIMS = {
    "life": ("sim_1a_life", 15 * 60),
    "lenia": ("sim_1b_lenia", 16 * 60),
    "grayscott": ("sim_1c_grayscott", 14 * 60),
    "langton": ("sim_1e_langton", 12 * 60),
    "bees": ("sim_2_bees", 16 * 60),
    "boids": ("sim_3_boids", 17 * 60),
    "tero": ("sim_4_tero", 16 * 60),
    "jones": ("sim_4b_jones", 12 * 60),
    "pps": ("sim_5_pps", 14 * 60),
}

VERTICAL = ["lenia", "grayscott", "boids"]

CHROMIUM_ARGS = [
    "--use-gl=angle",
    "--use-angle=swiftshader",
    "--enable-unsafe-swiftshader",
]


def serve_url(base: str, sim_path: str, formato: str, w: int, h: int) -> str:
    q = f"capture=1&formato={formato}&fps=60&w={w}&h={h}&seed=6006"
    return f"{base}/{sim_path}/index.html?{q}"


def verify_center_brightness(page) -> float:
    return page.evaluate(
        """() => {
      if (window.__cnCapture?.verify) return window.__cnCapture.verify() ? 100 : 0;
      const c = document.getElementById('cn-canvas');
      const ctx = c.getContext('2d');
      const w = c.width, h = c.height;
      const d = ctx.getImageData((w/2)|0, (h/2)|0, 64, 64).data;
      let s = 0;
      for (let i = 0; i < d.length; i += 4) s += d[i] + d[i+1] + d[i+2];
      return s / (64 * 64 * 3);
    }"""
    )


def capture(name: str, frames: int, formato: str, w: int, h: int, base_url: str) -> Path:
    sim_path = SIMS[name][0]
    frames_dir = ROOT / "salida" / "frames" / f"{name}_{formato}"
    verify_png = ART / f"ep06_{name}_{formato}_verify.png"
    frames_dir.mkdir(parents=True, exist_ok=True)
    for old in frames_dir.glob("*.png"):
        old.unlink()
    url = serve_url(base_url, sim_path, formato, w, h)
    with sync_playwright() as p:
        browser = p.chromium.launch(args=CHROMIUM_ARGS)
        page = browser.new_page(viewport={"width": w, "height": h})
        page.on("pageerror", lambda e: print("pageerror:", e, file=sys.stderr))
        page.goto(url, wait_until="networkidle")
        page.wait_for_function("() => window.__cnCapture && window.__cnCapture.ready", timeout=180_000)
        data0 = page.evaluate("async () => await window.__cnCapture.pullFrame()")
        raw0 = base64.b64decode(data0.split(",", 1)[1])
        verify_png.write_bytes(raw0)
        bright = verify_center_brightness(page)
        print(f"verify {name} {formato}: brightness={bright:.1f} -> {verify_png}", file=sys.stderr)
        if bright < 15 and name in ("lenia", "grayscott"):
            raise RuntimeError(f"{name} frame vacío (brillo {bright:.1f})")
        out0 = frames_dir / "frame_000000.png"
        out0.write_bytes(raw0)
        for i in range(1, frames):
            data = page.evaluate("async () => await window.__cnCapture.pullFrame()")
            raw = base64.b64decode(data.split(",", 1)[1])
            (frames_dir / f"frame_{i:06d}.png").write_bytes(raw)
        browser.close()
    tag = "16x9" if formato == "16x9" else "9x16"
    mp4 = ART / f"ep06_{name}_{tag}_1080p60.mp4"
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-framerate", "60",
        "-i", str(frames_dir / "frame_%06d.png"),
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-preset", "slow", "-crf", "23",
        "-movflags", "+faststart",
        str(mp4),
    ]
    subprocess.run(cmd, check=True)
    mb = mp4.stat().st_size / (1024 * 1024)
    if mb > 15:
        tmp = mp4.with_suffix(".tmp.mp4")
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-i", str(mp4), "-c:v", "libx264",
             "-crf", "26", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(tmp)],
            check=True,
        )
        tmp.replace(mp4)
    return mp4


def export_check_frames(name: str, formato: str, mp4: Path) -> None:
    tag = "16x9" if formato == "16x9" else "9x16"
    dur = float(
        subprocess.check_output(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(mp4)],
            text=True,
        ).strip()
    )
    for label, ts in [("start", 0.25), ("mid", dur * 0.5), ("end", max(0.05, dur - 0.35))]:
        out = ART / f"ep06_{name}_{tag}_{label}.png"
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-ss", str(ts), "-i", str(mp4), "-frames:v", "1", str(out)],
            check=True,
        )
        print(f"check {name} {tag} {label}: {out}", file=sys.stderr)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", default=list(SIMS.keys()))
    ap.add_argument("--base", default="http://127.0.0.1:8766")
    args = ap.parse_args()
    for name in args.only:
        if name not in SIMS:
            print(f"omitido: {name}", file=sys.stderr)
            continue
        sec = min(18, max(10, SIMS[name][1] // 60))
        frames = sec * 60
        mp4 = capture(name, frames, "16x9", 1920, 1080, args.base)
        print(f"{mp4} ({mp4.stat().st_size / (1024 * 1024):.1f} MB)")
        if name in ("lenia", "tero", "bees"):
            export_check_frames(name, "16x9", mp4)
        if name in VERTICAL:
            mp4v = capture(name, frames, "9x16", 1080, 1920, args.base)
            print(f"{mp4v} ({mp4v.stat().st_size / (1024 * 1024):.1f} MB)")
            if name in ("lenia", "tero", "bees"):
                export_check_frames(name, "9x16", mp4v)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())