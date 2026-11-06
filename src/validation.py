"""Independent exhaustive checks on small artificial instances."""
from itertools import permutations, combinations
from math import inf, isfinite
from .scheduler import optimize_day

def exhaustive_minimum(jobs, prices, setup_minutes):
    best_cost = inf
    valid_plans = 0
    setup_slots = setup_minutes // 5

    # Try every job order and every increasing set of start times.
    for order in permutations(range(len(jobs))):
        for starts in combinations(
            range(len(prices)), len(jobs)
        ):
            previous_finish = 0
            total_cost = 0.0

            for position, job_type in enumerate(order):
                start = starts[position]
                profile = jobs[job_type]["profile_wh"]
                finish = start + len(profile)

                required_setup = setup_slots if position else 0

                # Reject overlaps, missing setup time or late completion.
                if (
                    start < previous_finish + required_setup
                    or finish > len(prices)
                ):
                    break

                total_cost += sum(
                    energy * prices[start + offset]
                    for offset, energy in enumerate(profile)
                )

                previous_finish = finish

            else:
                valid_plans += 1
                best_cost = min(best_cost, total_cost)

    return best_cost, valid_plans

def run_validation():
    jobs = [
        {"quantity": 1, "profile_wh": [10, 30]},
        {"quantity": 1, "profile_wh": [20]},
        {"quantity": 1, "profile_wh": [12, 8]},
    ]
    prices = [0.00008,0.00009,0.00004,0.00003,0.00007,0.00005,0.00010,0.00002,0.00006]
    cases = [
        ("variable_prices_no_setup", prices, 0),
        ("variable_prices_5min_setup", prices, 5),
        ("variable_prices_10min_setup", prices, 10),
        ("insufficient_capacity", prices, 15),
        ("constant_prices", [0.00005]*9, 5),
        ("mixed_sign_prices", [v if i%2 else -v for i,v in enumerate(prices)], 5),
    ]
    rows = []
    for name, profile, setup in cases:
        exhaustive, count = exhaustive_minimum(jobs, profile, setup)
        actual = optimize_day(jobs, profile, setup)["optimized_cost_eur"]
        if isfinite(exhaustive):
            assert actual is not None and abs(actual-exhaustive) < 1e-8
        else:
            assert actual is None
        rows.append({"test": name, "valid_plans_enumerated": count,
                     "exhaustive_cost_eur": exhaustive if isfinite(exhaustive) else None,
                     "dp_cost_eur": actual, "result": "PASS"})
    return rows
