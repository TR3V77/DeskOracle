"""
Generates a synthetic IT helpdesk ticket dataset modeled on realistic
enterprise support patterns (category mix, priority skew, resolution-time
distributions that vary by category and day of week).

Run: python data/generate_tickets.py
Output: data/tickets.csv
"""
import csv
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.categories import (
    ACCOUNT_ACCESS,
    CATEGORIES,
    EMAIL,
    HARDWARE,
    NETWORK_VPN,
    PRINTER,
    SECURITY,
    SOFTWARE,
)

random.seed(42)

# Per-category generation config (weight, description templates, priority
# distribution, resolution-time range). Keyed by the same category names
# backend.categories defines, so a category added here without being added
# there (or vice versa) fails loudly instead of silently drifting.
CATEGORY_CONFIG = {
    NETWORK_VPN: {
        "weight": 0.20,
        "descriptions": [
            "VPN keeps disconnecting every few minutes",
            "Cannot connect to VPN, authentication failed error",
            "Wi-Fi drops constantly in the east building",
            "Very slow network speeds on corporate Wi-Fi",
            "VPN client won't launch after latest update",
        ],
        "priority_weights": {"Low": 0.15, "Medium": 0.45, "High": 0.30, "Critical": 0.10},
        "resolution_hours": (1, 12),
    },
    ACCOUNT_ACCESS: {
        "weight": 0.18,
        "descriptions": [
            "Locked out of my account after password expired",
            "Need access to the shared finance drive for a project",
            "Forgot my password and self-service reset isn't working",
            "Requesting elevated access to the deployment pipeline",
            "New hire needs accounts provisioned before start date",
        ],
        "priority_weights": {"Low": 0.20, "Medium": 0.50, "High": 0.25, "Critical": 0.05},
        "resolution_hours": (0.5, 6),
    },
    HARDWARE: {
        "weight": 0.17,
        "descriptions": [
            "Laptop won't power on at all",
            "Battery drains fully within an hour",
            "Screen cracked after laptop bag fell",
            "Docking station won't detect external monitor",
            "Laptop fan is extremely loud and it's overheating",
        ],
        "priority_weights": {"Low": 0.10, "Medium": 0.35, "High": 0.40, "Critical": 0.15},
        "resolution_hours": (4, 72),
    },
    SOFTWARE: {
        "weight": 0.16,
        "descriptions": [
            "Need Adobe Acrobat installed for contract review",
            "Application keeps crashing on launch",
            "License activation error on design software",
            "Requesting install of project management tool",
            "Software freezes whenever I try to export a file",
        ],
        "priority_weights": {"Low": 0.30, "Medium": 0.45, "High": 0.20, "Critical": 0.05},
        "resolution_hours": (1, 24),
    },
    PRINTER: {
        "weight": 0.10,
        "descriptions": [
            "Printer on 3rd floor is offline",
            "Print jobs stuck in queue and won't clear",
            "Printer is printing blank pages",
            "Can't add the new printer to my laptop",
        ],
        "priority_weights": {"Low": 0.45, "Medium": 0.40, "High": 0.13, "Critical": 0.02},
        "resolution_hours": (0.5, 8),
    },
    EMAIL: {
        "weight": 0.11,
        "descriptions": [
            "Mailbox full, can't send or receive email",
            "Emails to external clients are bouncing back",
            "Outlook stuck in offline mode",
            "Not receiving any emails since this morning",
        ],
        "priority_weights": {"Low": 0.15, "Medium": 0.45, "High": 0.32, "Critical": 0.08},
        "resolution_hours": (1, 10),
    },
    SECURITY: {
        "weight": 0.08,
        "descriptions": [
            "Received a suspicious email asking for my password",
            "Think I clicked a phishing link by accident",
            "Antivirus is flagging a file I downloaded",
            "My laptop is acting strange after opening an attachment",
        ],
        "priority_weights": {"Low": 0.05, "Medium": 0.20, "High": 0.45, "Critical": 0.30},
        "resolution_hours": (0.5, 6),
    },
}

assert set(CATEGORY_CONFIG) == set(CATEGORIES), (
    "CATEGORY_CONFIG keys must match backend.categories.CATEGORIES exactly"
)

SATISFACTION_BY_PRIORITY_MISS = {
    # Rough model: tickets resolved slower than the category's median get lower CSAT.
    True: (2, 3.5),
    False: (3.5, 5.0),
}

START_DATE = datetime(2025, 3, 1)
NUM_DAYS = 210  # ~7 months of ticket history
TICKETS_PER_DAY_RANGE = (8, 28)

def weighted_choice(weight_dict):
    items = list(weight_dict.items())
    total = sum(w for _, w in items)
    r = random.uniform(0, total)
    upto = 0
    for item, w in items:
        upto += w
        if upto >= r:
            return item
    return items[-1][0]


def generate():
    rows = []
    ticket_id = 1000
    cat_names = list(CATEGORY_CONFIG.keys())
    cat_weights = [CATEGORY_CONFIG[c]["weight"] for c in cat_names]

    for day_offset in range(NUM_DAYS):
        date = START_DATE + timedelta(days=day_offset)
        weekday = date.weekday()  # 0=Mon
        if weekday >= 5:
            # Weekends: much lower volume
            n_tickets = random.randint(0, 4)
        else:
            n_tickets = random.randint(*TICKETS_PER_DAY_RANGE)
            if weekday == 0:
                # Monday VPN/network spike (people reconnecting after the weekend)
                n_tickets = int(n_tickets * 1.3)

        for _ in range(n_tickets):
            category = random.choices(cat_names, weights=cat_weights, k=1)[0]
            info = CATEGORY_CONFIG[category]
            description = random.choice(info["descriptions"])
            priority = weighted_choice(info["priority_weights"])

            lo, hi = info["resolution_hours"]
            # Critical/High priority tickets get worked faster relative to their category range
            if priority == "Critical":
                resolution_hours = round(random.uniform(lo, lo + (hi - lo) * 0.25), 1)
            elif priority == "High":
                resolution_hours = round(random.uniform(lo, lo + (hi - lo) * 0.5), 1)
            else:
                resolution_hours = round(random.uniform(lo + (hi - lo) * 0.3, hi), 1)

            category_median = (lo + hi) / 2
            missed_target = resolution_hours > category_median
            sat_lo, sat_hi = SATISFACTION_BY_PRIORITY_MISS[missed_target]
            satisfaction = round(random.uniform(sat_lo, sat_hi), 1)

            created_at = date + timedelta(
                hours=random.randint(7, 18), minutes=random.randint(0, 59)
            )

            rows.append(
                {
                    "ticket_id": ticket_id,
                    "created_at": created_at.strftime("%Y-%m-%d %H:%M"),
                    "category": category,
                    "priority": priority,
                    "description": description,
                    "resolution_time_hours": resolution_hours,
                    "satisfaction_score": satisfaction,
                }
            )
            ticket_id += 1

    return rows


def main():
    rows = generate()
    out_path = "data/tickets.csv"
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "ticket_id",
                "created_at",
                "category",
                "priority",
                "description",
                "resolution_time_hours",
                "satisfaction_score",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} tickets to {out_path}")


if __name__ == "__main__":
    main()
