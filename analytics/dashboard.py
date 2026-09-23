"""
Generates a static PNG dashboard of ticket volume, resolution time, and
satisfaction trends from the synthetic dataset -- the kind of exploratory
analysis a helpdesk analytics rotation would produce to spot operational
patterns (e.g. Monday VPN spikes, slow hardware turnaround).

Run: python analytics/dashboard.py
Output: analytics/dashboard.png
"""
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "tickets.csv"
OUT_PATH = Path(__file__).resolve().parent / "dashboard.png"


def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH, parse_dates=["created_at"])
    df["date"] = df["created_at"].dt.date
    df["weekday"] = df["created_at"].dt.day_name()
    return df


def build_dashboard(df: pd.DataFrame):
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle("Danny -- IT Helpdesk Analytics Dashboard", fontsize=16, fontweight="bold")

    # 1. Daily ticket volume over time
    daily_volume = df.groupby("date").size()
    ax = axes[0, 0]
    ax.plot(daily_volume.index, daily_volume.values, linewidth=1, color="#2563eb")
    ax.set_title("Daily Ticket Volume")
    ax.set_xlabel("Date")
    ax.set_ylabel("Tickets")
    ax.tick_params(axis="x", rotation=45)

    # 2. Average resolution time by category
    avg_res = df.groupby("category")["resolution_time_hours"].mean().sort_values()
    ax = axes[0, 1]
    ax.barh(avg_res.index, avg_res.values, color="#16a34a")
    ax.set_title("Avg Resolution Time by Category (hrs)")
    ax.set_xlabel("Hours")

    # 3. Ticket volume by weekday
    weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    by_weekday = df["weekday"].value_counts().reindex(weekday_order)
    ax = axes[1, 0]
    colors = ["#dc2626" if day == "Monday" else "#94a3b8" for day in weekday_order]
    ax.bar(by_weekday.index, by_weekday.values, color=colors)
    ax.set_title("Ticket Volume by Day of Week")
    ax.tick_params(axis="x", rotation=45)

    # 4. Category mix (share of total tickets)
    cat_counts = df["category"].value_counts()
    ax = axes[1, 1]
    ax.pie(cat_counts.values, labels=cat_counts.index, autopct="%1.0f%%",
           textprops={"fontsize": 8})
    ax.set_title("Ticket Category Mix")

    fig.tight_layout(rect=[0, 0, 1, 0.96])
    fig.savefig(OUT_PATH, dpi=150)
    print(f"Dashboard saved to {OUT_PATH}")

    print("\nKey stats:")
    print(f"  Total tickets: {len(df)}")
    print(f"  Avg resolution time: {df['resolution_time_hours'].mean():.1f} hrs")
    print(f"  Avg satisfaction: {df['satisfaction_score'].mean():.2f} / 5")
    monday_avg = by_weekday.get("Monday", 0)
    other_avg = by_weekday.drop("Monday").mean()
    print(f"  Monday volume vs. other weekday avg: {monday_avg:.0f} vs {other_avg:.0f} "
          f"({(monday_avg / other_avg - 1):+.0%})")


if __name__ == "__main__":
    df = load_data()
    build_dashboard(df)
