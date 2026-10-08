"""Transfer-learning trainer: pretrained timm backbone -> single logit (AI probability).

    python scripts/train.py --config experiments/configs/convnext_tiny.yaml
    python scripts/train.py --config experiments/configs/convnext_tiny.yaml --set lr=3e-5 epochs=8
    python scripts/train.py --config ... --export models/detector_c     # copy best checkpoint for the app

Fits on split == train, selects/early-stops on split == validation. Never reads the test splits.
Each run writes experiments/<run_id>/ (config, log.csv, best.pt, metrics.json, val_predictions.csv, curves.png)
and appends a row to docs/experiments.md.
"""
from __future__ import annotations

import argparse
import io
import json
import math
import random
import shutil
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import yaml
from PIL import Image, ImageFilter
from torch import nn
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms

from common import ROOT, dataset_version, load_split, new_run_id, resolve, seed_everything

DEFAULTS = {
    "name": "convnext_tiny",
    "backbone": "convnext_tiny.fb_in22k_ft_in1k",
    "input_size": 224,
    "resize_ratio": 1.14,
    "batch_size": 32,
    "grad_accum": 1,
    "head_epochs": 2,
    "head_lr": 1e-3,
    "epochs": 10,
    "lr": 5e-5,
    "weight_decay": 0.05,
    "warmup_epochs": 1,
    "drop_rate": 0.2,
    "patience": 3,
    "select_metric": "roc_auc",
    "seed": 42,
    "num_workers": 4,
    "amp": True,
    "aug": {"crop_scale_min": 0.6, "rotation": 10, "brightness": 0.2, "contrast": 0.2,
            "jpeg_p": 0.5, "jpeg_quality": [60, 100], "blur_p": 0.1},
    "limit_train": None,
    "limit_val": None,
}


class RandomJPEG:
    """Re-encode as JPEG with random quality. Applied to both classes so format is not a shortcut."""

    def __init__(self, p: float, quality: tuple[int, int]):
        self.p, self.quality = p, quality

    def __call__(self, img: Image.Image) -> Image.Image:
        if random.random() >= self.p:
            return img
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=random.randint(*self.quality))
        buf.seek(0)
        return Image.open(buf).convert("RGB")


class RandomBlur:
    def __init__(self, p: float):
        self.p = p

    def __call__(self, img: Image.Image) -> Image.Image:
        return img.filter(ImageFilter.GaussianBlur(random.uniform(0.3, 1.2))) if random.random() < self.p else img


class ManifestDataset(Dataset):
    def __init__(self, df: pd.DataFrame, transform):
        self.paths = [str(resolve(p)) for p in df["path"]]
        self.labels = df["label"].astype(np.float32).to_numpy()
        self.transform = transform

    def __len__(self) -> int:
        return len(self.paths)

    def __getitem__(self, i):
        from app.services.preprocessing import to_rgb

        with Image.open(self.paths[i]) as im:
            img = to_rgb(im)
        return self.transform(img), self.labels[i]


def build_transforms(cfg: dict, mean, std):
    a, size = cfg["aug"], cfg["input_size"]
    train = transforms.Compose([
        RandomJPEG(a["jpeg_p"], tuple(a["jpeg_quality"])),
        RandomBlur(a["blur_p"]),
        transforms.RandomResizedCrop(size, scale=(a["crop_scale_min"], 1.0)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(a["rotation"]),
        transforms.ColorJitter(brightness=a["brightness"], contrast=a["contrast"]),
        transforms.ToTensor(),
        transforms.Normalize(mean, std),
    ])
    val = transforms.Compose([
        transforms.Resize(int(size * cfg["resize_ratio"])),
        transforms.CenterCrop(size),
        transforms.ToTensor(),
        transforms.Normalize(mean, std),
    ])
    return train, val


def seed_worker(worker_id: int) -> None:
    seed = torch.initial_seed() % 2 ** 32
    np.random.seed(seed)
    random.seed(seed)


@torch.no_grad()
def predict(model, loader, device, amp: bool) -> tuple[np.ndarray, np.ndarray, float]:
    model.eval()
    probs, labels, loss_sum = [], [], 0.0
    loss_fn = nn.BCEWithLogitsLoss(reduction="sum")
    for x, y in loader:
        x, y = x.to(device, non_blocking=True), y.to(device)
        with torch.autocast(device.type, enabled=amp and device.type == "cuda"):
            logits = model(x).squeeze(1)
        loss_sum += loss_fn(logits.float(), y).item()
        probs.append(torch.sigmoid(logits.float()).cpu().numpy())
        labels.append(y.cpu().numpy())
    return np.concatenate(probs), np.concatenate(labels), loss_sum / len(loader.dataset)


def train_epochs(model, params, lr, epochs, warmup, cfg, loaders, device, log, run_dir, state):
    from evaluation.metrics import binary_metrics

    optimizer = torch.optim.AdamW(params, lr=lr, weight_decay=cfg["weight_decay"])
    steps_per_epoch = math.ceil(len(loaders["train"]) / cfg["grad_accum"])
    total, warm = epochs * steps_per_epoch, warmup * steps_per_epoch
    schedule = torch.optim.lr_scheduler.LambdaLR(optimizer, lambda s: (s + 1) / max(1, warm) if s < warm else
                                                 0.5 * (1 + math.cos(math.pi * (s - warm) / max(1, total - warm))))
    scaler = torch.amp.GradScaler(enabled=cfg["amp"] and device.type == "cuda")
    loss_fn = nn.BCEWithLogitsLoss()

    for _ in range(epochs):
        state["epoch"] += 1
        model.train()
        if state["stage"] == "head":  # frozen backbone: keep its BatchNorm statistics frozen too
            model.eval()
            model.get_classifier().train()
        t0, run_loss, correct, seen = time.time(), 0.0, 0, 0
        optimizer.zero_grad(set_to_none=True)
        for step, (x, y) in enumerate(loaders["train"]):
            x, y = x.to(device, non_blocking=True), y.to(device)
            with torch.autocast(device.type, enabled=cfg["amp"] and device.type == "cuda"):
                logits = model(x).squeeze(1)
                loss = loss_fn(logits.float(), y) / cfg["grad_accum"]
            scaler.scale(loss).backward()
            if (step + 1) % cfg["grad_accum"] == 0 or step + 1 == len(loaders["train"]):
                scaler.step(optimizer)
                scaler.update()
                optimizer.zero_grad(set_to_none=True)
                schedule.step()
            run_loss += loss.item() * cfg["grad_accum"] * len(y)
            correct += ((logits.detach() > 0).float() == y).sum().item()
            seen += len(y)

        probs, labels, val_loss = predict(model, loaders["val"], device, cfg["amp"])
        m = binary_metrics(labels, probs)
        row = {"epoch": state["epoch"], "stage": state["stage"], "train_loss": run_loss / seen, "train_acc": correct / seen,
               "val_loss": val_loss, "val_acc": m["accuracy"], "val_f1": m["f1"], "val_roc_auc": m["roc_auc"],
               "lr": optimizer.param_groups[0]["lr"], "seconds": round(time.time() - t0, 1)}
        log.append(row)
        pd.DataFrame(log).to_csv(run_dir / "log.csv", index=False)
        print(" ".join(f"{k}={v:.4f}" if isinstance(v, float) else f"{k}={v}" for k, v in row.items()), flush=True)

        score = m[cfg["select_metric"]]
        if score > state["best"]:
            state.update(best=score, best_epoch=state["epoch"], stale=0, best_probs=probs)
            torch.save({"model": model.state_dict()}, run_dir / "best.pt")
        else:
            state["stale"] += 1
            if state["stage"] == "finetune" and state["stale"] >= cfg["patience"]:
                print(f"Early stopping: no {cfg['select_metric']} improvement for {cfg['patience']} epochs")
                return


def plot_curves(log: list[dict], path: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    df = pd.DataFrame(log)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 3.5))
    a1.plot(df["epoch"], df["train_loss"], label="train"); a1.plot(df["epoch"], df["val_loss"], label="validation")
    a1.set_title("Loss"); a1.set_xlabel("epoch"); a1.legend()
    a2.plot(df["epoch"], df["train_acc"], label="train"); a2.plot(df["epoch"], df["val_acc"], label="validation")
    a2.set_title("Accuracy"); a2.set_xlabel("epoch"); a2.legend()
    fig.tight_layout(); fig.savefig(path, dpi=130); plt.close(fig)


def append_experiment_row(run_id: str, cfg: dict, metrics: dict) -> None:
    path = ROOT / "docs" / "experiments.md"
    if not path.exists():
        path.write_text("# Experiments\n\n| Experiment ID | Dataset version | Model version | Parameters | Seed | Date | "
                        "Validation score | Test score |\n|---|---|---|---|---|---|---|---|\n", encoding="utf-8")
    params = f"lr={cfg['lr']}, bs={cfg['batch_size']}x{cfg['grad_accum']}, epochs<={cfg['epochs']}, wd={cfg['weight_decay']}"
    b = metrics["binary@0.5"]
    with path.open("a", encoding="utf-8") as f:
        f.write(f"| {run_id} | {metrics['dataset_version']} | {cfg['backbone']} | {params} | {cfg['seed']} | "
                f"{run_id[:8]} | acc {b['accuracy']:.4f}, F1 {b['f1']:.4f}, AUC {b['roc_auc']:.4f} | — |\n")


def parse_override(text: str):
    key, value = text.split("=", 1)
    return key, yaml.safe_load(value)


def main() -> None:
    import timm
    from evaluation.metrics import evaluate

    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config")
    ap.add_argument("--set", nargs="*", default=[], type=parse_override, help="override config keys: lr=3e-5")
    ap.add_argument("--export", help="copy the best checkpoint + model_info.json into this models/ folder")
    args = ap.parse_args()

    cfg = json.loads(json.dumps(DEFAULTS))
    if args.config:
        cfg.update(yaml.safe_load(resolve(args.config).read_text()) or {})
    cfg.update(dict(args.set))
    seed_everything(cfg["seed"])

    run_id = new_run_id(cfg["name"])
    run_dir = ROOT / "experiments" / run_id
    run_dir.mkdir(parents=True)
    cfg["dataset_version"] = dataset_version()
    (run_dir / "config.yaml").write_text(yaml.safe_dump(cfg, sort_keys=False))

    train_df, val_df = load_split("train"), load_split("validation")
    if cfg["limit_train"]:
        train_df = train_df.sample(n=min(cfg["limit_train"], len(train_df)), random_state=cfg["seed"])
    if cfg["limit_val"]:
        val_df = val_df.sample(n=min(cfg["limit_val"], len(val_df)), random_state=cfg["seed"])
    print(f"Run {run_id}: train={len(train_df)} validation={len(val_df)} dataset={cfg['dataset_version']}")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = timm.create_model(cfg["backbone"], pretrained=True, num_classes=1, drop_rate=cfg["drop_rate"]).to(device)
    data_cfg = timm.data.resolve_data_config({}, model=model)
    mean, std = list(data_cfg["mean"]), list(data_cfg["std"])
    train_tf, val_tf = build_transforms(cfg, mean, std)
    g = torch.Generator().manual_seed(cfg["seed"])
    common_kw = dict(num_workers=cfg["num_workers"], pin_memory=device.type == "cuda",
                     persistent_workers=cfg["num_workers"] > 0, worker_init_fn=seed_worker)
    loaders = {
        "train": DataLoader(ManifestDataset(train_df, train_tf), batch_size=cfg["batch_size"], shuffle=True,
                            drop_last=len(train_df) > cfg["batch_size"], generator=g, **common_kw),
        "val": DataLoader(ManifestDataset(val_df, val_tf), batch_size=cfg["batch_size"] * 2, **common_kw),
    }

    log: list[dict] = []
    state = {"epoch": 0, "best": -1.0, "best_epoch": 0, "stale": 0, "best_probs": None, "stage": "head"}
    head = model.get_classifier()
    if cfg["head_epochs"] > 0:
        for p in model.parameters():
            p.requires_grad = False
        for p in head.parameters():
            p.requires_grad = True
        train_epochs(model, head.parameters(), cfg["head_lr"], cfg["head_epochs"], 0, cfg, loaders, device, log, run_dir, state)
    for p in model.parameters():
        p.requires_grad = True
    state.update(stage="finetune", stale=0)
    train_epochs(model, model.parameters(), cfg["lr"], cfg["epochs"], cfg["warmup_epochs"], cfg, loaders, device, log, run_dir, state)

    preds = val_df[["path", "label", "generator", "split"]].assign(model=run_id, ai_probability=state["best_probs"])
    preds.to_csv(run_dir / "val_predictions.csv", index=False)
    metrics = evaluate(preds)
    metrics.update(best_epoch=state["best_epoch"], dataset_version=cfg["dataset_version"], run_id=run_id)
    (run_dir / "metrics.json").write_text(json.dumps(metrics, indent=2))
    plot_curves(log, run_dir / "curves.png")
    append_experiment_row(run_id, cfg, metrics)

    info = {"type": "timm", "backbone": cfg["backbone"], "input_size": cfg["input_size"],
            "resize_ratio": cfg["resize_ratio"], "mean": mean, "std": std, "checkpoint": "best.pt",
            "label_mapping": {"0": "REAL", "1": "AI_GENERATED"}, "output": "sigmoid(logit) = ai_probability",
            "run_id": run_id, "dataset_version": cfg["dataset_version"]}
    (run_dir / "model_info.json").write_text(json.dumps(info, indent=2))
    b = metrics["binary@0.5"]
    print(f"\nBest epoch {state['best_epoch']}: val acc {b['accuracy']:.4f} F1 {b['f1']:.4f} AUC {b['roc_auc']:.4f}")
    last = log[-1]
    if last["train_acc"] - last["val_acc"] > 0.08:
        print("NOTE: train accuracy is far above validation accuracy - likely overfitting (see aid-train-detector).")

    if args.export:
        target = resolve(args.export)
        target.mkdir(parents=True, exist_ok=True)
        shutil.copy2(run_dir / "best.pt", target / "best.pt")
        shutil.copy2(run_dir / "model_info.json", target / "model_info.json")
        print(f"Exported to {target} (add it to models/ensemble/ensemble_config.json as type 'timm')")
    print(f"Run directory: {run_dir}")


if __name__ == "__main__":
    main()
