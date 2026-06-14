
import csv
import os
import random

random.seed(42)

RESEARCH_AREAS = [
    "Mine Safety",
    "Environmental Rehabilitation",
    "Automation in Mining",
    "Underground Coal Gasification",
    "Coal Bed Methane",
    "Coal Quality Assessment",
    "Mine Waste Utilization",
    "General IT Infrastructure",
]

# Priority weighting roughly aligned with cil_moc_priority_areas.md

AREA_PRIORITY_WEIGHT = {
    "Mine Safety": 0.85,
    "Environmental Rehabilitation": 0.80,
    "Automation in Mining": 0.75,
    "Underground Coal Gasification": 0.65,
    "Coal Bed Methane": 0.55,
    "Coal Quality Assessment": 0.70,
    "Mine Waste Utilization": 0.65,
    "General IT Infrastructure": 0.30,
}

INSTITUTION_TYPES = ["academic", "cil_psu", "industry"]
INSTITUTION_WEIGHT = {"academic": 0.65, "cil_psu": 0.75, "industry": 0.55}

N_SAMPLES = 400

# Budget ceilings per institution type, per st_funding_guidelines.md
TPC_CEILING = {"academic": 200.0, "cil_psu": 350.0, "industry": 350.0}


def sample_proposal():
    area = random.choice(RESEARCH_AREAS)
    institution_type = random.choices(
        INSTITUTION_TYPES, weights=[0.5, 0.3, 0.2]
    )[0]

    duration_months = random.choice([12, 18, 24, 30, 36, 42, 48])
    ceiling = TPC_CEILING[institution_type]

    # Requested amount: usually within ceiling, occasionally over
    if random.random() < 0.85:
        requested_amount_lakhs = round(random.uniform(20, ceiling), 1)
    else:
        requested_amount_lakhs = round(random.uniform(ceiling, ceiling * 1.6), 1)

    num_objectives = random.randint(2, 7)

    # Approval probability model 
    prob = AREA_PRIORITY_WEIGHT[area] * 0.4
    prob += INSTITUTION_WEIGHT[institution_type] * 0.25

    # Penalize over-ceiling requests
    if requested_amount_lakhs > ceiling:
        over_ratio = requested_amount_lakhs / ceiling
        prob -= min(0.35, (over_ratio - 1) * 0.6)

    # Penalize very long durations (>36 months) per guideline Section 2.2
    if duration_months > 36:
        prob -= 0.10
    elif duration_months < 12:
        prob -= 0.05

    # Slight bonus for a focused objective count (3-5 sweet spot)
    if 3 <= num_objectives <= 5:
        prob += 0.05
    elif num_objectives >= 7:
        prob -= 0.05

    # Random noise to avoid a perfectly deterministic relationship
    prob += random.uniform(-0.12, 0.12)
    prob = max(0.02, min(0.98, prob))

    approved = 1 if random.random() < prob else 0

    return {
        "research_area": area,
        "requested_amount_lakhs": requested_amount_lakhs,
        "duration_months": duration_months,
        "institution_type": institution_type,
        "num_objectives": num_objectives,
        "approved": approved,
    }


def main():
    rows = [sample_proposal() for _ in range(N_SAMPLES)]
    out_path = os.path.join(os.path.dirname(__file__), "historical_proposals.csv")
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    approved_count = sum(r["approved"] for r in rows)
    print(f"Generated {len(rows)} rows -> {out_path}")
    print(f"Approved: {approved_count} ({approved_count/len(rows)*100:.1f}%), "
          f"Rejected: {len(rows)-approved_count} ({(len(rows)-approved_count)/len(rows)*100:.1f}%)")


if __name__ == "__main__":
    main()