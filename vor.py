import pandas as pd    # pandas lets us work with tables of data (like spreadsheets in code)
import numpy as np     # numpy gives us math tools
import matplotlib.pyplot as plt  # matplotlib lets us create plots and figures
import os              # os lets us work with file paths in a cross-platform way

def load_projections():
    """
    Reads the 5 FantasyPros projection CSV files (one per position)
    and combines them into one master table of all players.
    Returns a pandas DataFrame with columns: name, team, projected_points, position
    """

    # The 5 positions we care about in standard fantasy football
    positions = ['QB', 'RB', 'WR', 'TE', 'K']

    # Maps each position to its corresponding CSV filename in the data/ folder
    filenames = {
        'QB': 'qb_projections.csv',
        'RB': 'rb_projections.csv',
        'WR': 'wr_projections.csv',
        'TE': 'te_projections.csv',
        'K':  'k_projections.csv',
    }

    # Empty list that will hold one table per position
    # After the loop we'll stack all 5 into one big table
    all_players = []

    # Loop through each position and load its CSV file
    for pos in positions:
        # Build the file path: e.g. 'data/qb_projections.csv'
        # os.path.join works on both Mac and Windows
        filepath = os.path.join('data', filenames[pos])

        # FantasyPros CSVs have a blank second row for all positions EXCEPT kickers
        # skiprows=[1] tells pandas to skip row index 1 (the second row)
        if pos == 'K':
            df = pd.read_csv(filepath)           # Kickers: no blank row
        else:
            df = pd.read_csv(filepath, skiprows=[1])  # Others: skip blank row

       
        # We only need Player name, Team, and FPTS (fantasy points)
        # .copy() makes a fresh independent copy so we don't edit the original
        df = df[['Player', 'Team', 'FPTS']].copy()

        # Adds a 'Position' column to the DataFrame and sets every row to the current position (pos)
        df['Position'] = pos

        # FantasyPros sometimes formats large numbers with commas e.g. "1,234.5"
        # Python can't do math on strings, so we:
        # 1. Convert to string (.astype(str))
        # 2. Remove commas (.str.replace(',', ''))
        # 3. Convert to float so we can do math (.astype(float))
        df['FPTS'] = df['FPTS'].astype(str).str.replace(',', '').astype(float)

        # Remove any rows where the player name is missing or blank
        df = df.dropna(subset=['Player'])
        df = df[df['Player'].str.strip() != '']

        # Add this position's table to our list
        all_players.append(df)

    # Stack all 5 position tables on top of each other into one big table
    # ignore_index=True resets the row numbers so they go 0, 1, 2, 3... continuously
    # instead of restarting at 0 for each position
    players = pd.concat(all_players, ignore_index=True)

    # Rename columns to cleaner lowercase names for consistency throughout the project
    players = players.rename(columns={
        'Player': 'name',
        'Team': 'team',
        'FPTS': 'projected_points',
        'Position': 'position'
    })

    # Sort all players by projected points from highest to lowest
    # reset_index(drop=True) resets row numbers after sorting
    players = players.sort_values('projected_points', ascending=False).reset_index(drop=True)

    return players


def calculate_vor(players):
    """
    Calculates Value Over Replacement (VOR) for every player.

    VOR = player's projected points - replacement level player's projected points

    The replacement level player is the last expected starter at that position
    in a 10 man league. Any player below replacement level has negative VOR
    and is not worth drafting as a starter.

    Returns the same DataFrame with two new columns added:
    - replacement_points: the baseline score for that position
    - vor: how many points above replacement this player is projected for
    """

    replacement_rank = {
        'QB': 10,   
        'RB': 20,   
        'WR': 20,   
        'TE': 10,   
        'K':  10,   
    }

    # Empty list to hold each position's table after VOR is calculated
    vor_list = []

    for pos, rank in replacement_rank.items():
        # Get all players at this position and sort best to worst
        pos_players = players[players['position'] == pos].copy()
        pos_players = pos_players.sort_values('projected_points', ascending=False).reset_index(drop=True)

        # Find the replacement level player's index
        rep_index = min(rank, len(pos_players) - 1)

        # Look up that replacement player's projected points
        replacement_points = pos_players.loc[rep_index, 'projected_points']

        # Add replacement_points as a column (same value for every player at this position)
        pos_players['replacement_points'] = replacement_points

        # VOR = how many points above replacement this player provides
        # A player AT replacement level has VOR = 0
        # A player BELOW replacement level has negative VOR (not worth starting)
        pos_players['vor'] = pos_players['projected_points'] - replacement_points

        vor_list.append(pos_players)

    # Combine all positions back into one table
    result = pd.concat(vor_list, ignore_index=True)

    # Sort by VOR descending
    result = result.sort_values('vor', ascending=False).reset_index(drop=True)

    return result


if __name__ == "__main__":
    # Load all player projections from CSV files
    players = load_projections()

    # Calculate VOR for every player
    draft_board = calculate_vor(players)

    # Print the top 30 players by VOR — our true draft board
    print("=== TOP 30 PLAYERS BY VOR (TRUE DRAFT BOARD) ===")
    print(draft_board[['name', 'position', 'team', 'projected_points', 'vor']].head(30).to_string(index=False))
    print()

    # Print top 3 at each position with their replacement level for reference
    for pos in ['QB', 'RB', 'WR', 'TE', 'K']:
        pos_data = draft_board[draft_board['position'] == pos].head(3)
        rep = pos_data['replacement_points'].iloc[0]
        print(f"--- Top 3 {pos}s by VOR (Replacement = {rep:.1f} pts) ---")
        print(pos_data[['name', 'projected_points', 'vor']].to_string(index=False))
        print()
