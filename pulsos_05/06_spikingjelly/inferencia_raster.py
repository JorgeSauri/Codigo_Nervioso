#!/usr/bin/env python3
"""Raster de una inferencia MNIST con la SNN entrenada. CC0."""
from __future__ import annotations

import argparse
import os

import matplotlib.pyplot as plt
import torch
from torchvision import datasets, transforms

from spikingjelly.activation_based import encoding, functional

from train import CSNN, SEMILLA as SEMILLA_CNN
from train_una_capa import CKPT_NAME, SEMILLA as SEMILLA_UC, UnaCapaSNN


def indice_primer_siete(data_root: str) -> int:
    ds = datasets.MNIST(data_root, train=False, download=True, transform=transforms.ToTensor())
    for i in range(len(ds)):
        if ds[i][1] == 7:
            return i
    return 0


def raster_cnn(model: CSNN, img: torch.Tensor, T: int) -> list[tuple[int, int]]:
    registro = []
    with torch.no_grad():
        functional.reset_net(model)
        x = img.unsqueeze(0)
        for _ in range(T):
            out = model(x)
            registro.append(out.squeeze(0).numpy())
    raster = []
    for t, spike_vec in enumerate(registro):
        for ni, val in enumerate(spike_vec):
            if val > 0.5:
                raster.append((t, ni))
    return raster


def raster_una_capa(
    model: UnaCapaSNN, encoder: encoding.PoissonEncoder, img: torch.Tensor, T: int
) -> list[tuple[int, int]]:
    raster = []
    with torch.no_grad():
        functional.reset_net(model)
        x = img.unsqueeze(0)
        for t in range(T):
            encoded = encoder(x)
            out = model(encoded).squeeze(0)
            for ni, val in enumerate(out.numpy()):
                if val > 0.5:
                    raster.append((t, ni))
    return raster


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--modelo", choices=["cnn", "una_capa"], default="cnn")
    ap.add_argument("--indice", type=int, default=None, help="muestra MNIST test; con una_capa por defecto primer 7")
    ap.add_argument("--T", type=int, default=None)
    ap.add_argument("--formato", choices=["16x9", "9x16"], default="16x9")
    ap.add_argument("--salida", default="salida/raster_inferencia.png")
    ap.add_argument("--checkpoint", default=None)
    args = ap.parse_args()

    data_root = os.path.join(os.path.dirname(__file__), "data")

    if args.modelo == "una_capa":
        torch.manual_seed(SEMILLA_UC)
        T = args.T if args.T is not None else 32
        idx = args.indice if args.indice is not None else indice_primer_siete(data_root)
        ckpt = args.checkpoint or os.path.join(os.path.dirname(args.salida) or "salida", CKPT_NAME)
        tfm = transforms.ToTensor()
        model = UnaCapaSNN()
        encoder = encoding.PoissonEncoder()
        titulo_extra = "una capa · Poisson"
    else:
        torch.manual_seed(SEMILLA_CNN)
        T = args.T if args.T is not None else 8
        idx = args.indice if args.indice is not None else 7
        ckpt = args.checkpoint or os.path.join(os.path.dirname(args.salida) or "salida", "modelo_mnist.pt")
        tfm = transforms.Compose([transforms.ToTensor(), transforms.Normalize((0.1307,), (0.3081,))])
        model = CSNN()
        encoder = None
        titulo_extra = "CNN"

    if os.path.isfile(ckpt):
        model.load_state_dict(torch.load(ckpt, map_location="cpu", weights_only=True))
    else:
        print(f"Advertencia: no hay checkpoint en {ckpt}; raster con pesos aleatorios.", flush=True)
    model.eval()

    ds = datasets.MNIST(data_root, train=False, download=True, transform=tfm)
    img, label = ds[idx]

    if args.modelo == "una_capa":
        raster = raster_una_capa(model, encoder, img, T)
    else:
        raster = raster_cnn(model, img, T)

    w, h = (16, 9) if args.formato == "16x9" else (9, 16)
    fig, axes = plt.subplots(2, 1, figsize=(w, h), gridspec_kw={"height_ratios": [1, 2]})
    axes[0].imshow(img.squeeze(), cmap="gray")
    axes[0].set_title(f"Muestra MNIST #{idx} (etiqueta {label}) · {titulo_extra}")
    axes[0].axis("off")
    if raster:
        ts, ns = zip(*raster)
        axes[1].scatter(ts, ns, s=40, c="#3ee0d0")
    axes[1].set_xlim(-0.5, T - 0.5)
    axes[1].set_xlabel("Paso de tiempo")
    axes[1].set_ylabel("Neurona de salida")
    axes[1].set_title("Raster de salida (sin convertir pulsos en energía)")
    axes[1].set_yticks(range(10))
    fig.tight_layout()
    os.makedirs(os.path.dirname(args.salida) or ".", exist_ok=True)
    fig.savefig(args.salida, dpi=160)
    plt.close(fig)
    print(f"Guardado: {args.salida} (modelo={args.modelo}, índice={idx}, T={T})", flush=True)


if __name__ == "__main__":
    main()