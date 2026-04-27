# draft-optimizer

A fantasy football snake draft simulator and optimizer built for a 10-team standard scoring league.

Models three drafting strategies — Best Player Available, Positional Need, and Value Over Replacement (VOR) — and simulates full drafts to compare outcomes.

## Project Structure
- `main.py` — entry point, runs simulations and generates figures
- `vor.py` — VOR and scarcity index calculations
- `draft_simulator.py` — snake draft engine
- `strategies.py` — drafting strategy implementations
- `data/` — player projections and parameters
- `figures/` — output plots for analysis
