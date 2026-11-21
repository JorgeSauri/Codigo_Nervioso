#!/usr/bin/env python3
"""SNN pequeña LIF + gradiente sustituto en MNIST (CPU). CC0."""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import datasets, transforms

# Fuerza CPU
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")

from spikingjelly.activation_based import functional, layer, neuron, surrogate

SEMILLA = 6006


class CSNN(nn.Module):
    def __init__(self, tau: float = 2.0) -> None:
        super().__init__()
        self.net = nn.Sequential(
            layer.Conv2d(1, 16, 5, 1, 2, bias=False),
            layer.BatchNorm2d(16),
            neuron.LIFNode(tau=tau, detach_reset=True, surrogate_function=surrogate.ATan()),
            layer.MaxPool2d(2, 2),
            layer.Conv2d(16, 32, 5, 1, 2, bias=False),
            layer.BatchNorm2d(32),
            neuron.LIFNode(tau=tau, detach_reset=True, surrogate_function=surrogate.ATan()),
            layer.MaxPool2d(2, 2),
            layer.Flatten(),
            nn.Linear(32 * 7 * 7, 10, bias=False),
            neuron.LIFNode(tau=tau, detach_reset=True, surrogate_function=surrogate.ATan()),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


def train_epoch(model, loader, optim, device, T: int) -> tuple[float, float]:
    model.train()
    total, correct, spikes = 0, 0, 0.0
    for img, label in loader:
        functional.reset_net(model)
        img = img.to(device)
        label = label.to(device)
        out_acc = None
        for _ in range(T):
            out = model(img)
            out_acc = out if out_acc is None else out_acc + out
        assert out_acc is not None
        pred = out_acc.argmax(1)
        correct += (pred == label).sum().item()
        total += label.numel()
        spikes += out_acc.detach().sum().item()
        loss = nn.functional.cross_entropy(out_acc, label)
        optim.zero_grad()
        loss.backward()
        optim.step()
    return correct / max(total, 1), spikes / max(total, 1)


@torch.no_grad()
def eval_epoch(model, loader, device, T: int) -> tuple[float, float]:
    model.eval()
    total, correct, spikes = 0, 0, 0.0
    for img, label in loader:
        functional.reset_net(model)
        img = img.to(device)
        label = label.to(device)
        out_acc = None
        for _ in range(T):
            out = model(img)
            out_acc = out if out_acc is None else out_acc + out
        assert out_acc is not None
        pred = out_acc.argmax(1)
        correct += (pred == label).sum().item()
        total += label.numel()
        spikes += out_acc.sum().item()
    return correct / max(total, 1), spikes / max(total, 1) / 10.0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--epocas", type=int, default=2)
    ap.add_argument("--lote", type=int, default=128)
    ap.add_argument("--T", type=int, default=8, help="pasos de tiempo por muestra")
    ap.add_argument("--reporte", default="salida/metricas.json")
    args = ap.parse_args()

    torch.manual_seed(SEMILLA)
    device = torch.device("cpu")

    tfm = transforms.Compose([transforms.ToTensor(), transforms.Normalize((0.1307,), (0.3081,))])
    data_root = os.path.join(os.path.dirname(__file__), "data")
    train_set = datasets.MNIST(data_root, train=True, download=True, transform=tfm)
    test_set = datasets.MNIST(data_root, train=False, download=True, transform=tfm)
    train_loader = DataLoader(train_set, batch_size=args.lote, shuffle=True, num_workers=0)
    test_loader = DataLoader(test_set, batch_size=args.lote, shuffle=False, num_workers=0)

    model = CSNN().to(device)
    optim = torch.optim.Adam(model.parameters(), lr=1e-3)

    t0 = time.time()
    historia = []
    for ep in range(1, args.epocas + 1):
        acc_tr, _ = train_epoch(model, train_loader, optim, device, args.T)
        acc_te, spn = eval_epoch(model, test_loader, device, args.T)
        historia.append(dict(epoca=ep, exactitud_entrenamiento=acc_tr, exactitud_prueba=acc_te, pulsos_promedio_neurona=spn))
        print(f"Época {ep}: train={acc_tr:.3f} test={acc_te:.3f} pulsos/neurona={spn:.2f}")

    os.makedirs(os.path.dirname(args.reporte) or ".", exist_ok=True)
    ckpt = os.path.join(os.path.dirname(args.reporte) or ".", "modelo_mnist.pt")
    torch.save(model.state_dict(), ckpt)
    res = dict(
        semilla=SEMILLA,
        segundos=round(time.time() - t0, 1),
        dispositivo="cpu",
        T=args.T,
        epocas=args.epocas,
        historia=historia,
        checkpoint=ckpt,
    )
    with open(args.reporte, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2, ensure_ascii=False)
    print(f"Métricas: {args.reporte}", flush=True)


if __name__ == "__main__":
    main()