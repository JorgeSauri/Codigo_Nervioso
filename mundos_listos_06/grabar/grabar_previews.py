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

VERTICAL = ["grayscott", "boids"]


def serve_url(base: str, sim_path: str, formato: str, w: int, h: int) -> str:
    q = f"capture=1&formato={formato}&fps=60&w={w}&h={h}&seed=6006"
    return f"{base}/{sim_path}/index.html?{q}"


def capture(name: str, frames: int, formato: str, w: int, h: int, base_url: str) -> Path:
    sim_path = SIMS[name][0]
    frames_dir = ROOT / "salida" / "frames" / f"{name}_{formato}"
    frames_dir.mkdir(parents=True, exist_ok=True)
    for old in frames_dir.glob("*.png"):
        old.unlink()
    url = serve_url(base_url, sim_path, formato, w, h)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": w, "height": h})
        page.on("pageerror", lambda e: print("pageerror:", e, file=sys.stderr))
        page.goto(url, wait_until="networkidle")
        page.wait_for_function("() => window.__cnCapture && window.__cnCapture.ready", timeout=30_000)
        for i in range(frames):
            data = page.evaluate("async () => await window.__cnCapture.pullFrame()")
            raw = base64.b64decode(data.split(",", 1)[1])
            out = frames_dir / f"frame_{i:06d}.png"
            out.write_bytes(raw)
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
    return mp4


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", default=list(SIMS.keys()))
    ap.add_argument("--base", default="http://127.0.0.1:8766")
    args = ap.parse_args()
    made = []
    for name in args.only:
        if name not in SIMS:
            print(f"omitido: {name}", file=sys.stderr)
            continue
        sec = min(18, max(10, SIMS[name][1] // 60))
        frames = sec * 60
        mp4 = capture(name, frames, "16x9", 1920, 1080, args.base)
        made.append(mp4)
        sz = mp4.stat().st_size / (1024 * 1024)
        print(f"{mp4} ({sz:.1f} MB)")
        if name in VERTICAL:
            mp4v = capture(name, frames, "9x16", 1080, 1920, args.base)
            made.append(mp4v)
            print(f"{mp4v} ({mp4v.stat().st_size / (1024 * 1024):.1f} MB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())