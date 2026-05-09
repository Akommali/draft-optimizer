import pandas as pd
import matplotlib.pyplot as plt
import os
from vor import load_projections, calculate_vor
from draft_simulator import DraftSimulator

def run_simulation(draft_board, strategy):
    """
    Runs one full snake draft simulation using the given strategy.
    Returns the completed DraftSimulator object so we can inspect rosters.
    
    draft_board : DataFrame with VOR calculated
    strategy    : 'bpa', 'need', or 'vor'
    """
    # Create a fresh simulator for this strategy
    sim = DraftSimulator(draft_board, strategy=strategy)

    # Run the full 13 round snake draft
    sim.run_draft()

    return sim


def get_team_scores(sim):
    """
    Calculates the total projected points for each team's roster.
    
    sim : a completed DraftSimulator object
    Returns a list of 10 scores, one per team
    """
    team_scores = []

    for roster in sim.rosters:
        # Sum projected points for every player on this team's roster
        total = sum(player['projected_points'] for player in roster)
        team_scores.append(total)

    return team_scores


def print_results(sim, strategy):
    """
    Prints a readable summary of the draft results for one strategy.
    Shows each team's roster and total projected points.
    """
    print("\n" + "="*60)
    print("  STRATEGY: " + strategy.upper())
    print("="*60)

    team_scores = get_team_scores(sim)

    for i, roster in enumerate(sim.rosters):
        print("\nTeam " + str(i + 1) + " — Total: " + str(round(team_scores[i], 1)) + " pts")
        print("  " + "Name".ljust(25) + "Pos".ljust(5) + "Proj Pts".rjust(8) + "VOR".rjust(8))
        print("  " + "-"*50)
        for player in roster:
            name = player['name'].ljust(25)
            pos  = player['position'].ljust(5)
            pts  = str(round(player['projected_points'], 1)).rjust(8)
            vor  = str(round(player.get('vor', 0), 1)).rjust(8)
            print("  " + name + pos + pts + vor)


if __name__ == "__main__":
    # Step 1: Load player data and calculate VOR
    print("Loading player projections...")
    players = load_projections()
    draft_board = calculate_vor(players)
    print("Loaded " + str(len(draft_board)) + " players across 5 positions")

    # Step 2: Run all three simulations
    print("\nRunning simulations...")
    strategies = ['bpa', 'need', 'vor']
    simulations = {}

    for strategy in strategies:
        simulations[strategy] = run_simulation(draft_board, strategy)
        print("  " + strategy.upper() + " simulation complete")

    # Step 3: Print results for each strategy
    for strategy in strategies:
        print_results(simulations[strategy], strategy)

    # Step 4: Summary comparison
    print("\n" + "="*60)
    print("  STRATEGY COMPARISON SUMMARY")
    print("="*60)
    print("Strategy".ljust(10) + "Avg Score".rjust(10) + "Best Team".rjust(10) + "Worst Team".rjust(10))
    print("-"*45)

    for strategy in strategies:
        scores = get_team_scores(simulations[strategy])
        avg   = round(sum(scores) / len(scores), 1)
        best  = round(max(scores), 1)
        worst = round(min(scores), 1)
        print(strategy.upper().ljust(10) + str(avg).rjust(10) + str(best).rjust(10) + str(worst).rjust(10))