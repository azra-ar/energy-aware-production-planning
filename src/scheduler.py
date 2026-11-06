"""Exact single-machine scheduling on a discrete time grid.

The numerical solver is extracted from the verified research notebook.
It assumes zero setup/idle energy, no initial setup and identical units
within each product type. Its inputs are copied per call.
"""
from functools import lru_cache
from itertools import permutations, combinations
from math import inf, isfinite

def optimize_day(
    job_types,
    prices_eur_per_wh,
    setup_minutes=5,
    slot_minutes=5,
):
    # Validate and copy the inputs.
    assert isinstance(slot_minutes, int) and slot_minutes > 0
    assert setup_minutes >= 0
    assert setup_minutes % slot_minutes == 0
    assert job_types and prices_eur_per_wh

    prices = tuple(float(p) for p in prices_eur_per_wh)
    profiles = tuple(
        tuple(job["profile_wh"]) for job in job_types
    )
    quantities = tuple(job["quantity"] for job in job_types)

    assert all(isfinite(p) for p in prices)
    assert all(
        isinstance(q, int) and q >= 0 for q in quantities
    )
    assert all(
        profile and all(isfinite(e) and e >= 0 for e in profile)
        for profile in profiles
    )

    durations = tuple(len(profile) for profile in profiles)
    horizon = len(prices)
    preparation_slots = int(setup_minutes / slot_minutes)

    # Cost of starting each product type at each possible time.
    start_costs = []

    for profile in profiles:
        start_costs.append(tuple(
            sum(
                energy * prices[start + offset]
                for offset, energy in enumerate(profile)
            )
            if start + len(profile) <= horizon else inf
            for start in range(horizon + 1)
        ))

    # Find the minimum cost under the production constraints.
    @lru_cache(maxsize=None)
    def solve(time_slot, remaining, last_type):
        if not any(remaining):
            return 0.0

        required_slots = sum(
            q * d for q, d in zip(remaining, durations)
        )

        if time_slot + required_slots > horizon:
            return inf

        best_cost = solve(
            time_slot + 1, remaining, last_type
        )

        for kind, quantity in enumerate(remaining):
            if quantity == 0:
                continue

            change_required = (
                last_type != -1 and last_type != kind
            )

            start = time_slot + (
                preparation_slots if change_required else 0
            )
            finish = start + durations[kind]

            if finish > horizon:
                continue

            next_remaining = list(remaining)
            next_remaining[kind] -= 1

            candidate_cost = (
                start_costs[kind][start]
                + solve(
                    finish, tuple(next_remaining), kind
                )
            )

            best_cost = min(best_cost, candidate_cost)

        return best_cost

    optimal_cost = solve(0, quantities, -1)

    # Reference: original product order, no deliberate waiting.
    time_slot = 0
    previous_type = -1
    reference_cost = 0.0

    for kind, quantity in enumerate(quantities):
        for _ in range(quantity):
            if previous_type != -1 and previous_type != kind:
                time_slot += preparation_slots

            if time_slot + durations[kind] > horizon:
                reference_cost = inf
                break

            reference_cost += start_costs[kind][time_slot]
            time_slot += durations[kind]
            previous_type = kind

        if not isfinite(reference_cost):
            break

    comparable = (
        isfinite(optimal_cost) and isfinite(reference_cost)
    )

    if comparable:
        assert optimal_cost <= reference_cost + 0.000000001

    result = {
        "setup_minutes": setup_minutes,
        "optimized_feasible": isfinite(optimal_cost),
        "reference_feasible": isfinite(reference_cost),
        "reference_cost_eur": (
            reference_cost if isfinite(reference_cost) else None
        ),
        "optimized_cost_eur": (
            optimal_cost if isfinite(optimal_cost) else None
        ),
        "savings_eur": (
            reference_cost - optimal_cost
            if comparable else None
        ),
        "savings_percent": (
            (reference_cost - optimal_cost)
            / reference_cost * 100
            if comparable and reference_cost > 0 else None
        ),
        "states_evaluated": solve.cache_info().currsize,
    }

    solve.cache_clear()
    return result

def grouped_order_cost(
    ordered_jobs,
    prices,
    setup_minutes=5,
    slot_minutes=5,
):
    preparation_slots = setup_minutes // slot_minutes
    current_slot = 0
    previous_mode = None
    total_cost = 0.0

    for job in ordered_jobs:
        if job["quantity"] == 0:
            continue

        if (
            previous_mode is not None
            and previous_mode != job["mode"]
        ):
            current_slot += preparation_slots

        profile = job["profile_wh"]

        for _ in range(job["quantity"]):
            if current_slot + len(profile) > len(prices):
                return inf

            total_cost += sum(
                energy * prices[current_slot + offset]
                for offset, energy in enumerate(profile)
            )

            current_slot += len(profile)

        previous_mode = job["mode"]

    return total_cost
