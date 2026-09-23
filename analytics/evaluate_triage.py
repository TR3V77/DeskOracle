"""
Evaluates the rule-based triage classifier against the synthetic ticket
dataset's known ground-truth category, producing an accuracy score,
precision/recall/F1 per category, and a confusion matrix.

The synthetic tickets were generated from category-specific description
templates (data/generate_tickets.py), so each ticket's true category is
known -- this lets us score the classifier the same way we'd score it
against a held-out labeled set in a real deployment.

Run: python analytics/evaluate_triage.py
Output: analytics/evaluation_report.txt, analytics/confusion_matrix.png
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.categories import CATEGORIES
from backend.triage import _fallback_classify


def evaluate():
    df = pd.read_csv(Path(__file__).resolve().parent.parent / "data" / "tickets.csv")

    predicted = []
    for desc in df["description"]:
        category, _ = _fallback_classify(desc)
        predicted.append(category)
    df["predicted_category"] = predicted

    correct = (df["category"] == df["predicted_category"]).sum()
    total = len(df)
    accuracy = correct / total

    rows = []
    confusion = pd.crosstab(df["category"], df["predicted_category"])

    for cat in CATEGORIES:
        tp = ((df["category"] == cat) & (df["predicted_category"] == cat)).sum()
        fp = ((df["category"] != cat) & (df["predicted_category"] == cat)).sum()
        fn = ((df["category"] == cat) & (df["predicted_category"] != cat)).sum()
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        support = (df["category"] == cat).sum()
        rows.append({
            "category": cat, "precision": round(precision, 3),
            "recall": round(recall, 3), "f1": round(f1, 3), "support": int(support),
        })

    metrics_df = pd.DataFrame(rows)

    report_path = Path(__file__).resolve().parent / "evaluation_report.txt"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("DeskOracle -- Rule-Based Classifier Evaluation\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Dataset: {total} tickets\n")
        f.write(f"Overall accuracy: {accuracy:.1%} ({correct}/{total})\n\n")
        f.write("Per-category precision / recall / F1:\n")
        f.write(metrics_df.to_string(index=False) + "\n\n")
        f.write("Confusion matrix (rows=actual, cols=predicted):\n")
        f.write(confusion.to_string() + "\n")

    print(f"Overall accuracy: {accuracy:.1%} ({correct}/{total})")
    print(metrics_df.to_string(index=False))
    print(f"\nFull report written to {report_path}")

    _plot_confusion(confusion)
    return accuracy, metrics_df, confusion


def _plot_confusion(confusion: pd.DataFrame):
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(8, 6))
    im = ax.imshow(confusion.values, cmap="Blues")
    ax.set_xticks(range(len(confusion.columns)))
    ax.set_yticks(range(len(confusion.index)))
    ax.set_xticklabels(confusion.columns, rotation=45, ha="right")
    ax.set_yticklabels(confusion.index)
    ax.set_xlabel("Predicted category")
    ax.set_ylabel("Actual category")
    ax.set_title("DeskOracle Classifier -- Confusion Matrix")

    for i in range(confusion.shape[0]):
        for j in range(confusion.shape[1]):
            val = confusion.values[i, j]
            if val > 0:
                ax.text(j, i, str(val), ha="center", va="center",
                        color="white" if val > confusion.values.max() / 2 else "black",
                        fontsize=8)

    fig.colorbar(im, ax=ax, label="Ticket count")
    fig.tight_layout()
    out_path = Path(__file__).resolve().parent / "confusion_matrix.png"
    fig.savefig(out_path, dpi=150)
    print(f"Confusion matrix saved to {out_path}")


if __name__ == "__main__":
    evaluate()
