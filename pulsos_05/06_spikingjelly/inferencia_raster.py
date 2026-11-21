#!/usr/bin/env python3
"""Raster de una inferencia MNIST con la SNN entrenada. CC0."""
from __future__ import annotations

import argparse
import os

import matplotlib.pyplot as plt
import torch
from torchvision import datasets, transforms

from spikingjelly.activation_based import functional, layer, neuron, surrogate
from train import CSNN, SEMILLA


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--indice", type=int, default=7)
    ap.add_argument("--T", type=int, default=8)
    ap.add_argument("--formato", choices=["16x9", "9x16"], default="16x9")
    ap.add_argument("--salida", default="salida/raster_inferencia.png")
    ap.add_argument("--checkpoint", default="salida/modelo_mnist.pt")
    args = ap.parse_args()

    torch.manual_seed(SEMILLA)
    model = CSNN()
    if os.path.isfile(args.checkpoint):
        model.load_state_dict(torch.load(args.checkpoint, map_location="cpu", weights_only=True))
    model.eval()

    tfm = transforms.Compose([transforms.ToTensor(), transforms.Normalize((0.1307,), (0.3081,))])
    ds = datasets.MNIST(os.path.join(os.path.dirname(__file__), "data"), train=False, download=True, transform=tfm)
    img, label = ds[args.indice]

    registro = []
    with torch.no_grad():
        functional.reset_net(model)
        x = img.unsqueeze(0)
        for t in range(args.T):
            out = model(x)
            registro.append(out.squeeze(0).numpy())

    raster = []
    for t, spike_vec in enumerate(registro):
        for ni, val in enumerate(spike_vec):
            if val > 0.5:
                raster.append((t, ni))

    w, h = (16, 9) if args.formato == "16x9" else (9, 16)
    fig, axes = plt.subplots(2, 1, figsize=(w, h), gridspec_kw={"height_ratios": [1, 2]})
    axes[0].imshow(img.squeeze(), cmap="gray")
    axes[0].set_title(f"Muestra MNIST #{args.indice} (etiqueta {label})")
    axes[0].axis("off")
    if raster:
        ts, ns = zip(*raster)
        axes[1].scatter(ts, ns, s=40, c="#3ee0d0")
    axes[1].set_xlabel("Paso de tiempo")
    axes[1].set_ylabel("Neurona de salida")
    axes[1].set_title("Raster de salida (sin convertir pulsos en energía)")
    axes[1].set_yticks(range(10))
    fig.tight_layout()
    os.makedirs(os.path.dirname(args.salida) or ".", exist_ok=True)
    fig.savefig(args.salida, dpi=160)
    print(f"Guardado: {args.salida}", flush=True)


if __name__ == "__main__":
    main()