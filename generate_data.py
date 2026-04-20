import pandas as pd
import numpy as np
import os

np.random.seed(42)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

periods = [f"2023-{str(m).zfill(2)}" for m in range(1, 13)]

departments = {
    "Sales": ["Product Revenue", "Service Revenue", "Subscription Revenue", "Sales Commissions", "Cost of Goods Sold", "Sales Travel & Entertainment", "Customer Discounts & Refunds"],
    "Marketing": ["Digital Advertising", "Content & SEO", "Events & Sponsorships", "PR & Communications", "Marketing Headcount", "Brand & Design"],
    "Operations": ["Salaries & Benefits", "Rent & Facilities", "Software & Tools", "IT Infrastructure", "Logistics & Shipping", "Equipment & Maintenance"],
    "Finance": ["Salaries & Benefits", "Audit & Compliance", "Banking & Fees", "Insurance", "Legal & Professional Services"],
    "HR": ["Salaries & Benefits", "Recruiting & Hiring", "Training & Development", "Employee Benefits & Perks", "HR Software"],
    "R&D": ["Engineering Salaries", "Research Materials", "Cloud Infrastructure", "Patents & Licensing", "Contractor & Consulting"]
}

base_budgets = {
    "Sales": {"Product Revenue": 850000, "Service Revenue": 320000, "Subscription Revenue": 180000, "Sales Commissions": 85000, "Cost of Goods Sold": 310000, "Sales Travel & Entertainment": 22000, "Customer Discounts & Refunds": 18000},
    "Marketing": {"Digital Advertising": 65000, "Content & SEO": 18000, "Events & Sponsorships": 28000, "PR & Communications": 12000, "Marketing Headcount": 95000, "Brand & Design": 14000},
    "Operations": {"Salaries & Benefits": 180000, "Rent & Facilities": 35000, "Software & Tools": 22000, "IT Infrastructure": 18000, "Logistics & Shipping": 45000, "Equipment & Maintenance": 12000},
    "Finance": {"Salaries & Benefits": 95000, "Audit & Compliance": 15000, "Banking & Fees": 4000, "Insurance": 8000, "Legal & Professional Services": 12000},
    "HR": {"Salaries & Benefits": 75000, "Recruiting & Hiring": 18000, "Training & Development": 8000, "Employee Benefits & Perks": 22000, "HR Software": 5000},
    "R&D": {"Engineering Salaries": 220000, "Research Materials": 15000, "Cloud Infrastructure": 28000, "Patents & Licensing": 8000, "Contractor & Consulting": 35000}
}

seasonal = [0.85, 0.88, 0.95, 0.98, 1.02, 1.05, 1.08, 1.10, 1.05, 1.02, 1.12, 1.20]

budget_rows, actual_rows = [], []

for period_idx, period in enumerate(periods):
    season = seasonal[period_idx]
    for dept, items in departments.items():
        for item in items:
            base = base_budgets[dept][item]
            budget_amt = round(base * season * np.random.uniform(0.97, 1.03), 2)

            if dept == "Sales" and "Revenue" in item:
                variance_pct = np.random.uniform(-0.08, 0.12)
                if period in ["2023-03", "2023-09", "2023-12"]:
                    variance_pct = np.random.uniform(0.08, 0.18)
                if period in ["2023-01", "2023-07"]:
                    variance_pct = np.random.uniform(-0.12, -0.04)
            elif dept == "Marketing" and item == "Digital Advertising":
                variance_pct = np.random.uniform(0.08, 0.22)
            elif dept == "R&D" and item == "Cloud Infrastructure":
                variance_pct = 0.02 * period_idx + np.random.uniform(-0.02, 0.05)
            elif dept == "Operations" and item == "Logistics & Shipping":
                variance_pct = np.random.uniform(-0.05, 0.05)
                if period in ["2023-10", "2023-11", "2023-12"]:
                    variance_pct = np.random.uniform(0.15, 0.28)
            elif item in ["Salaries & Benefits", "Engineering Salaries"]:
                variance_pct = np.random.uniform(-0.03, 0.03)
            else:
                variance_pct = np.random.uniform(-0.10, 0.10)

            actual_amt = round(budget_amt * (1 + variance_pct), 2)
            budget_rows.append({"period": period, "department": dept, "line_item": item, "amount": budget_amt})
            actual_rows.append({"period": period, "department": dept, "line_item": item, "amount": actual_amt})

budget_df = pd.DataFrame(budget_rows)
actual_df = pd.DataFrame(actual_rows)

budget_df.to_csv(os.path.join(BASE_DIR, "sample_data/budget.csv"), index=False)
actual_df.to_csv(os.path.join(BASE_DIR, "sample_data/actual.csv"), index=False)

print(f"✅ Generated {len(actual_df)} rows of actual data")
print(f"✅ Generated {len(budget_df)} rows of budget data")
print(f"✅ Periods: 12 months (2023-01 to 2023-12)")
print(f"✅ Departments: {actual_df['department'].nunique()} departments")
print(f"✅ Line items: {actual_df['line_item'].nunique()} unique line items")
print("✅ Files saved to sample_data/")