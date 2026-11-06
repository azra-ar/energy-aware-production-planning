# Methodology

## Research question

How much can time-dependent electricity pricing reduce the selected production system's energy cost while meeting its working-day limit and product-change setup requirements?

## Scope and data preparation

The model selects three separate single-task products supported by MAQ120. Each selected product requires one execution of one task per source production unit. The selected mode profiles are Sublimation TM3, Anti-Shrinkage TM2 and Ironing TM1. Quantities are aggregated from matching source requests. Alternative Ironing machines are not optimized.

Each source energy-profile element is treated as Wh consumed during a five-minute interval, not as an instantaneous kW value. Grid price entries are treated as EUR/Wh; multiplying the price by 1000 converts it to EUR/kWh. Cost is the sum of interval energy times interval price. A job crossing a price change retains its own variable energy profile.

The 1152 price entries represent six working days of 192 five-minute slots. The 07:00–23:00 day is followed by an overnight break omitted from this working-time sequence. Daily slices are not interpreted as consecutive 24-hour days. Each experiment finishes within its own day.

## Exact discrete optimization

A state is `(t, r, last)`: the next available five-minute slot, the tuple of remaining product quantities, and the previously produced product type. Units within a product type are interchangeable because they have identical profiles, availability and completion requirements.

At each state, the model considers waiting one slot or producing one remaining unit. Changing product type occupies the selected number of setup slots immediately before that production job. The first job requires no setup. Production and setup cannot overlap; jobs are not interrupted. Waiting does not reset the previous product type.

For a job type i with profile e, its start cost at slot s is the sum of `e[k] * price[s+k]` over its processing intervals. The value of a state is the minimum of the available action cost plus the minimum continuation cost. The terminal state with no remaining demand has cost zero. States with insufficient processing time remaining are infeasible. Memoization reuses equivalent states; each solve creates a fresh cache tied to its own inputs.

These states and actions cover all permitted schedules on the chosen grid. Optimal substructure supports the dynamic-programming recurrence. Exactness applies only to this model: no claim is made for omitted operational restrictions or continuous-time solutions.

## Comparisons and experiments

1. Original grouped reference: products in J1–J2–J3 order starting at 07:00, with no deliberate waiting.
2. Best grouped reference: the cheapest of six product-group orders, also starting at 07:00 without deliberate waiting. This benchmark uses the price profile when selecting its order.
3. Flexible optimization: individual production units can be interleaved and waiting inserted, subject to setup time and the 23:00 completion limit.

Original-demand experiments use quantities 10, 15 and 4. The workload experiment uses the separate controlled mix 2:3:1 multiplied by levels 1 through 5, with a level-6 overload check. The setup experiment uses 0, 5, 10 and 15 minutes on the first price day. The main daily and workload comparisons use five-minute setups.

Processing utilization is processing minutes divided by 960 available minutes. It excludes setup. For the highest feasible controlled workload, 950 production minutes plus at least two five-minute setups consume the entire day.

Savings are `(reference cost - optimized cost) / reference cost`. Combined percentages use summed costs. Percentages are omitted when the reference is nonpositive or the comparison is infeasible. Reductions in absolute EUR and percentages should both be interpreted.

## Validation

The educational notebook and module reproduce each other's first-day costs. Six small artificial cases independently enumerate job permutations and valid start-time combinations: variable prices with three setup lengths, insufficient capacity, constant prices and mixed-sign prices. Separate tests cover changing inputs between solves, source quantities, the excluded unassigned mode and overload handling.

The first notebook reconstructs full schedules for zero and five-minute setups and verifies quantities, time continuity, energy and cost. These schedule checks were also independently compared with the source profiles before packaging. A small finite test suite supports implementation confidence but is not a proof of all possible inputs.

## Practical boundaries

The model assumes full-day price knowledge and is therefore a deterministic retrospective benchmark. Real operation needs appropriate day-ahead information or a rolling-horizon approach. Zero setup/idle energy, no initial setup and all jobs ready at 07:00 are explicit simplifying assumptions. Setup durations are not measured company parameters.

The two selected single-task products and the chosen single-task strap avoid unverified internal route ordering. Global source constraints involving Harden processes do not involve the selected task set. No inference that the source task-list position is a precedence rule is used.

The small absolute costs do not establish an economically attractive implementation. Total electricity bills, labour, deployment costs, tariffs, uncertain orders and physical interpretation of production units remain outside this model.
