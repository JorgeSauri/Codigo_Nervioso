#!/usr/bin/env python3
"""Una capa LIF + Poisson en MNIST (tutorial lif_fc_mnist, CPU). CC0."""
from __future__ import annotations

import argparse
import json
import os
import time

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader
from torchvision import datasets, transforms

os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")

from spikingjelly.activation_based import encoding, functional, layer, neuron, surrogate

SEMILLA = 6007
CKPT_NAME = "modelo_una_capa.pt"


class UnaCapaSNN(nn.Module):
    """784 píxeles aplanados → 10 neuronas LIF (sin capas ocultas)."""

    def __init__(self, tau: float = 2.0) -> None:
        super().__init__()
        self.net = nn.Sequential(
            layer.Flatten(),
            layer.Linear(28 * 28, 10, bias=False),
            neuron.LIFNode(tau=tau, detach_reset=True, surrogate_function=surrogate.ATan()),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


def paso_temporal(
    model: UnaCapaSNN,
    encoder: encoding.PoissonEncoder,
    img: torch.Tensor,
    T: int,
) -> torch.Tensor:
    """Acumula salidas LIF durante T pasos con codificación de Poisson en cada paso."""
    out_acc = None
    for _ in range(T):
        encoded = encoder(img)
        out = model(encoded)
        out_acc = out if out_acc is None else out_acc + out
    assert out_acc is not None
    return out_acc


def train_epoch(
    model: UnaCapaSNN,
    encoder: encoding.PoissonEncoder,
    loader: DataLoader,
    optim: torch.optim.Optimizer,
    T: int,
) -> tuple[float, float]:
    model.train()
    total, correct, spikes = 0, 0, 0.0
    for img, label in loader:
        functional.reset_net(model)
        out_fr = paso_temporal(model, encoder, img, T)
        target = F.one_hot(label, 10).float()
        loss = F.mse_loss(out_fr / T, target)
        optim.zero_grad()
        loss.backward()
        optim.step()
        pred = out_fr.argmax(1)
        correct += (pred == label).sum().item()
        total += label.numel()
        spikes += out_fr.sum().item()
        functional.reset_net(model)
    return correct / max(total, 1), spikes / max(total, 1) / 10.0


@torch.no_grad()
def eval_epoch(
    model: UnaCapaSNN,
    encoder: encoding.PoissonEncoder,
    loader: DataLoader,
    T: int,
) -> tuple[float, float]:
    model.eval()
    total, correct, spikes = 0, 0, 0.0
    for img, label in loader:
        functional.reset_net(model)
        out_fr = paso_temporal(model, encoder, img, T)
        pred = out_fr.argmax(1)
        correct += (pred == label).sum().item()
        total += label.numel()
        spikes += out_fr.sum().item()
        functional.reset_net(model)
    return correct / max(total, 1), spikes / max(total, 1) / 10.0


def main() -> None:
    ap = argparse.ArgumentParser(description="MNIST: una capa LIF + Poisson")
    ap.add_argument("--epocas", type=int, default=2)
    ap.add_argument("--lote", type=int, default=128)
    ap.add_argument("--T", type=int, default=32, help="pasos de tiempo (como lif_fc_mnist)")
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--tau", type=float, default=2.0)
    ap.add_argument("--reporte", default="salida/metricas_una_capa.json")
    ap.add_argument("--checkpoint", default=None, help=f"por defecto junto al reporte / {CKPT_NAME}")
    args = ap.parse_args()

    torch.manual_seed(SEMILLA)
    device = torch.device("cpu")
    data_root = os.path.join(os.path.dirname(__file__), "data")
    tfm = transforms.ToTensor()
    train_set = datasets.MNIST(data_root, train=True, download=True, transform=tfm)
    test_set = datasets.MNIST(data_root, train=False, download=True, transform=tfm)
    train_loader = DataLoader(train_set, batch_size=args.lote, shuffle=True, num_workers=0)
    test_loader = DataLoader(test_set, batch_size=args.lote, shuffle=False, num_workers=0)

    model = UnaCapaSNN(tau=args.tau).to(device)
    encoder = encoding.PoissonEncoder()
    optim = torch.optim.Adam(model.parameters(), lr=args.lr)

    t0 = time.time()
    historia = []
    for ep in range(1, args.epocas + 1):
        acc_tr, sp_tr = train_epoch(model, encoder, train_loader, optim, args.T)
        acc_te, sp_te = eval_epoch(model, encoder, test_loader, args.T)
        historia.append(
            dict(
                epoca=ep,
                exactitud_entrenamiento=acc_tr,
                exactitud_prueba=acc_te,
                pulsos_promedio_neurona_entrenamiento=sp_tr,
                pulsos_promedio_neurona_prueba=sp_te,
            )
        )
        print(f"Época {ep}: train={acc_tr:.4f} test={acc_te:.4f} pulsos/neurona (test)={sp_te:.4f}")

    out_dir = os.path.dirname(args.reporte) or "."
    os.makedirs(out_dir, exist_ok=True)
    ckpt = args.checkpoint or os.path.join(out_dir, CKPT_NAME)
    torch.save(model.state_dict(), ckpt)

    ultima = historia[-1]
    res = dict(
        arquitectura="una_capa_lif_poisson",
        semilla=SEMILLA,
        segundos=round(time.time() - t0, 1),
        dispositivo="cpu",
        T=args.T,
        epocas=args.epocas,
        tau=args.tau,
        exactitud_prueba=ultima["exactitud_prueba"],
        pulsos_promedio_neurona_salida=ultima["pulsos_promedio_neurona_prueba"],
        historia=historia,
        checkpoint=ckpt,
    )
    with open(args.reporte, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2, ensure_ascii=False)
    print(
        f"Exactitud prueba: {res['exactitud_prueba']:.6f} | "
        f"épocas={args.epocas} T={args.T} semilla={SEMILLA} | "
        f"{res['segundos']} s | pulsos/neurona={res['pulsos_promedio_neurona_salida']:.4f}",
        flush=True,
    )
    print(f"Métricas: {args.reporte}", flush=True)


if __name__ == "__main__":
    main()