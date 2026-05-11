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

def get_starter_scores(sim):
    """
    Calculates each team's score using only their starting lineup.
    Starters are the best projected players at each position up to
    the starting limit, just like setting your lineup each week.

    Starting slots: 1 QB, 2 RB, 2 WR, 1 TE, 1 K = 7 starters total

    sim : a completed DraftSimulator object
    Returns a list of 10 scores, one per team
    """

    # How many starters each position gets
    starter_slots = {
        'QB': 1,
        'RB': 2,
        'WR': 2,
        'TE': 1,
        'K':  1,
    }

    team_scores = []

    for roster in sim.rosters:
        # Convert roster list to a DataFrame so we can sort and filter easily
        # This is the same structure as our player pool DataFrame
        roster_df = pd.DataFrame(roster)

        starter_total = 0

        for pos, slots in starter_slots.items():
            # Get all players at this position on the roster
            pos_players = roster_df[roster_df['position'] == pos]

            # Sort by projected points and take only the top starters
           
            top_starters = pos_players.sort_values(
                'projected_points', ascending=False
            ).head(slots)

            # Add their projected points to this team's starter total
            starter_total = starter_total + top_starters['projected_points'].sum()

        team_scores.append(starter_total)

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

def generate_figures(simulations):
    """
    Generates and saves bar chart figures comparing the three draft strategies.
    All figures saved to the figures/ folder for use in the paper.

    We use bar charts throughout for consistency and clarity.
    Each figure isolates one aspect of strategy comparison.
    """
    strategies  = ['bpa', 'need', 'vor']
    labels      = ['BPA', 'NEED', 'VOR']
    colors      = ['#e74c3c', '#3498db', '#2ecc71']  # red, blue, green

    # --- FIGURE 1: Average Starter Score per Strategy ---
    # The core result — which strategy builds the best team on average
    avg_scores = []
    for strategy in strategies:
        scores = get_starter_scores(simulations[strategy])
        avg_scores.append(round(sum(scores) / len(scores), 1))

    plt.figure(figsize=(8, 5))
    bars = plt.bar(labels, avg_scores, color=colors, alpha=0.8, edgecolor='black')

    # Add value labels on top of each bar
    for bar, val in zip(bars, avg_scores):
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 3,
            str(val),
            ha='center',
            va='bottom',
            fontweight='bold'
        )

    plt.title('Average Starter Score by Draft Strategy')
    plt.xlabel('Draft Strategy')
    plt.ylabel('Average Total Starter Projected Points')
    plt.ylim(1100, 1420)
    plt.grid(axis='y', linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.savefig(os.path.join('figures', 'figure1_avg_starter_scores.png'), dpi=150)
    plt.close()
    print("Saved figure1_avg_starter_scores.png")

    # --- FIGURE 2: Best and Worst Team per Strategy ---
    # Shows variance — how much does the strategy protect against bad outcomes
    best_scores  = []
    worst_scores = []
    for strategy in strategies:
        scores = get_starter_scores(simulations[strategy])
        best_scores.append(round(max(scores), 1))
        worst_scores.append(round(min(scores), 1))

    # Grouped bar chart — two bars per strategy (best and worst)
    x      = range(len(labels))
    width  = 0.35  # width of each bar

    plt.figure(figsize=(9, 5))
    bars1 = plt.bar(
        [i - width/2 for i in x],
        best_scores,
        width,
        label='Best Team',
        color=colors,
        alpha=0.9,
        edgecolor='black'
    )
    bars2 = plt.bar(
        [i + width/2 for i in x],
        worst_scores,
        width,
        label='Worst Team',
        color=colors,
        alpha=0.4,
        edgecolor='black'
    )

    # Add value labels
    for bar, val in zip(bars1, best_scores):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 3,
                 str(val), ha='center', va='bottom', fontsize=9, fontweight='bold')
    for bar, val in zip(bars2, worst_scores):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 3,
                 str(val), ha='center', va='bottom', fontsize=9, fontweight='bold')

    plt.title('Best and Worst Team Score by Draft Strategy')
    plt.xlabel('Draft Strategy')
    plt.ylabel('Total Starter Projected Points')
    plt.xticks(list(x), labels)
    plt.legend()
    plt.ylim(1000, 1520)
    plt.grid(axis='y', linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.savefig(os.path.join('figures', 'figure2_best_worst_scores.png'), dpi=150)
    plt.close()
    print("Saved figure2_best_worst_scores.png")

    # --- FIGURE 3: VOR Drop-off Curves by Position ---
    # Shows how quickly player value drops at each position
    # This is the mathematical justification for why VOR matters
    players = load_projections()
    board   = calculate_vor(players)

    pos_colors = {
        'QB': '#e74c3c',
        'RB': '#3498db',
        'WR': '#2ecc71',
        'TE': '#f39c12',
        'K':  '#9b59b6'
    }

    plt.figure(figsize=(12, 6))

    for pos in ['QB', 'RB', 'WR', 'TE', 'K']:
        pos_players = board[board['position'] == pos].sort_values(
            'projected_points', ascending=False
        ).reset_index(drop=True)

        plt.plot(
            range(1, len(pos_players) + 1),
            pos_players['projected_points'].tolist(),
            label=pos,
            color=pos_colors[pos],
            linewidth=2
        )

    plt.title('Player Value Drop-off by Position (2025 Projections)')
    plt.xlabel('Player Rank Within Position')
    plt.ylabel('Projected Fantasy Points')
    plt.legend()
    plt.grid(linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.savefig(os.path.join('figures', 'figure3_dropoff_curves.png'), dpi=150)
    plt.close()
    print("Saved figure3_dropoff_curves.png")

    # --- FIGURE 4: VOR Values by Position (Top 10 players each) ---
    # Bar chart showing VOR for top 10 players at each position
    # Illustrates positional scarcity visually
    plt.figure(figsize=(14, 6))

    pos_list   = ['QB', 'RB', 'WR', 'TE', 'K']
    bar_width  = 0.15
    x_base     = range(10)  # top 10 players per position

    for i, pos in enumerate(pos_list):
        pos_players = board[board['position'] == pos].sort_values(
            'vor', ascending=False
        ).head(10).reset_index(drop=True)

        x_pos = [j + i * bar_width for j in x_base]
        plt.bar(
            x_pos,
            pos_players['vor'].tolist(),
            width=bar_width,
            label=pos,
            color=list(pos_colors.values())[i],
            alpha=0.8,
            edgecolor='black'
        )

    plt.title('Top 10 VOR Values by Position')
    plt.xlabel('Player Rank Within Position')
    plt.ylabel('Value Over Replacement (VOR)')
    plt.xticks(
        [j + bar_width * 2 for j in x_base],
        [str(i+1) for i in x_base]
    )
    plt.legend()
    plt.grid(axis='y', linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.savefig(os.path.join('figures', 'figure4_vor_by_position.png'), dpi=150)
    plt.close()
    print("Saved figure4_vor_by_position.png")


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

    # Step 4: Summary comparison using starter scores only
    print("\n" + "="*60)
    print("  STRATEGY COMPARISON SUMMARY (STARTERS ONLY)")
    print("="*60)
    print("Strategy".ljust(10) + "Avg Score".rjust(10) + "Best Team".rjust(10) + "Worst Team".rjust(10))
    print("-"*45)

    for strategy in strategies:
        scores = get_starter_scores(simulations[strategy])
        avg    = round(sum(scores) / len(scores), 1)
        best   = round(max(scores), 1)
        worst  = round(min(scores), 1)
        print(strategy.upper().ljust(10) + str(avg).rjust(10) + str(best).rjust(10) + str(worst).rjust(10))

    # Step 5: Generate all figures
    print("\nGenerating figures...")
    generate_figures(simulations)
    print("All figures saved to figures/ folder")

    for strategy in strategies:
        scores = get_starter_scores(simulations[strategy])
        avg   = round(sum(scores) / len(scores), 1)
        best  = round(max(scores), 1)
        worst = round(min(scores), 1)
        print(strategy.upper().ljust(10) + str(avg).rjust(10) + str(best).rjust(10) + str(worst).rjust(10))
