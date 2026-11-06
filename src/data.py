"""Load the explicitly selected subset without editing source data."""
import json
from pathlib import Path

SLOT_MINUTES = 5
WORKDAY_START_MINUTES = 420
WORKDAY_END_MINUTES = 1380
SLOTS_PER_DAY = 192
SELECTION = [
    ("J1", "PRINTED RIBBON  PES", "Sublimation TM3"),
    ("J2", "BRAIDED ELASTIC", "Anti-Shrinkage TM2"),
    ("J3", "SMOOTH STRAP(A)", "Ironing TM1"),
]
MIX = {"J1": 2, "J2": 3, "J3": 1}

def load_case(path):
    source = json.loads(Path(path).read_text(encoding="utf-8"))
    products = {p["id"]: p for p in source["products"]}
    tasks = {t["id"]: t for t in source["tasks"]}
    modes = {m["id"]: m for m in source["task_modes"]}
    machine = next(m for m in source["machines"] if m["id"] == "MAQ120")
    jobs = []
    for job_id, product_name, mode_name in SELECTION:
        entries = products[product_name]["tasks"]
        if len(entries) != 1 or entries[0]["runs"] != 1:
            raise ValueError("Selected product must require a single task performed once.")
        if mode_name not in tasks[entries[0]["task"]]["task_modes"]:
            raise ValueError("Mode is incompatible with the required task.")
        if mode_name not in machine["task_modes"]:
            raise ValueError("Mode is not assigned to MAQ120.")
        quantity = sum(r["amount"] for r in source["product_requests"] if r["product"] == product_name)
        if quantity <= 0 or quantity != int(quantity):
            raise ValueError("Selected quantities must be positive integers.")
        profile = list(modes[mode_name]["power"])
        jobs.append({"job_type_id": job_id, "product": product_name,
                     "mode": mode_name, "quantity": int(quantity),
                     "profile_wh": profile, "duration_slots": len(profile),
                     "duration_minutes": len(profile) * SLOT_MINUTES,
                     "energy_kwh_per_unit": sum(profile) / 1000})
    prices = next(s["price"] for s in source["energy_sources"] if s["id"] == "Socket Energy")
    if len(prices) != 6 * SLOTS_PER_DAY:
        raise ValueError("Expected six complete 192-slot working-day profiles.")
    days = [prices[i:i+SLOTS_PER_DAY] for i in range(0,len(prices),SLOTS_PER_DAY)]
    assigned = {mode for m in source["machines"] for mode in m["task_modes"]}
    referenced = {mode for task in source["tasks"] for mode in task["task_modes"]}
    return jobs, days, sorted(referenced - assigned)
