"""Dice, IoU, Precision, Recall for binary active-fire segmentation masks."""

from __future__ import annotations

import torch


def _binarize(pred: torch.Tensor, threshold: float) -> torch.Tensor:
    return (pred >= threshold).float()


def dice_score(pred: torch.Tensor, target: torch.Tensor, threshold: float = 0.5, eps: float = 1e-6) -> float:
    pred_b = _binarize(pred, threshold)
    intersection = (pred_b * target).sum()
    denom = pred_b.sum() + target.sum()
    return float((2 * intersection + eps) / (denom + eps))


def iou_score(pred: torch.Tensor, target: torch.Tensor, threshold: float = 0.5, eps: float = 1e-6) -> float:
    pred_b = _binarize(pred, threshold)
    intersection = (pred_b * target).sum()
    union = pred_b.sum() + target.sum() - intersection
    return float((intersection + eps) / (union + eps))


def precision_score(pred: torch.Tensor, target: torch.Tensor, threshold: float = 0.5, eps: float = 1e-6) -> float:
    pred_b = _binarize(pred, threshold)
    tp = (pred_b * target).sum()
    fp = (pred_b * (1 - target)).sum()
    return float((tp + eps) / (tp + fp + eps))


def recall_score(pred: torch.Tensor, target: torch.Tensor, threshold: float = 0.5, eps: float = 1e-6) -> float:
    pred_b = _binarize(pred, threshold)
    tp = (pred_b * target).sum()
    fn = ((1 - pred_b) * target).sum()
    return float((tp + eps) / (tp + fn + eps))


def all_metrics(pred: torch.Tensor, target: torch.Tensor, threshold: float = 0.5) -> dict[str, float]:
    return {
        "dice": dice_score(pred, target, threshold),
        "iou": iou_score(pred, target, threshold),
        "precision": precision_score(pred, target, threshold),
        "recall": recall_score(pred, target, threshold),
    }
