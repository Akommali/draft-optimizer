import pandas as pd
import os

# Simulates a 10-team snake draft using three different drafting strategies

class DraftSimulator:
    """
    Simulates a full snake draft with 10 teams and 13 rounds.
    Each team uses one of three strategies to make picks:
    - 'bpa'  : Best Player Available (highest raw projected points)
    - 'need' : Positional Need (fill roster slots in order of need)
    - 'vor'  : Value Over Replacement (highest VOR among still-needed positions)
    """

    def make_pick(self, team_index):
        # raises an error if the player pool is empty before the draft is complete
        if self.available.empty:
            raise ValueError("Player pool is empty before draft is complete.")

    def __init__(self, players, strategy='vor'):
        """
        players  : full DataFrame of players with VOR already calculated
        strategy : 'bpa', 'need', or 'vor' for how teams will make their picks
        """

        # Keep the original player pool untouched as a reference
        self.all_players = players.copy()

        # Working copy — players get removed from here as they are drafted
        # so no player can be picked by two teams
        self.available = players.copy()

        # Which strategy all teams in this simulation use
        self.strategy = strategy

        # League settings
        self.num_teams = 10
        self.num_rounds = 13  # 2QB+4RB+4WR+2TE+1K = 13 roster spots

        # Each team's roster starts as an empty list
        # After the draft: rosters[0] = Team 1's players, rosters[1] = Team 2's, etc.
        # In Java this would be: ArrayList<ArrayList<Player>> rosters
        self.rosters = [[] for _ in range(self.num_teams)]

        # Target number of each position per roster
        # Used by the 'need' and 'vor' strategies to know when a position is full
        self.roster_requirements = {
            'QB': 2,  # 1 starter + 1 backup
            'RB': 4,  # 2 starters + 2 backups
            'WR': 4,  # 2 starters + 2 backups
            'TE': 2,  # 1 starter + 1 backup
            'K':  1,  # just 1 kicker
        }

    def run_draft(self):
        """
        Runs the full 13-round snake draft.
        Each round alternates direction — this is the snake pattern.
        Calls make_pick() for each team on each pick.
        """

        for round_num in range(self.num_rounds):

            # Snake logic using modulo:
            # round_num % 2 == 0 means even round → normal order (0 to 9)
            # round_num % 2 == 1 means odd round  → reversed order (9 to 0)
            if round_num % 2 == 0:
                pick_order = range(self.num_teams)               
            else:
                pick_order = range(self.num_teams - 1, -1, -1)  

            for team_index in pick_order:
                # This team makes their pick based on the strategy
                pick = self.make_pick(team_index)

                # Add the player to this team's roster
                self.rosters[team_index].append(pick)

                # Remove the drafted player from the available pool
                # .reset_index(drop=True) resets row numbers after removal
                self.available = self.available[
                    self.available['name'] != pick['name']
                ].reset_index(drop=True)

    def make_pick(self, team_index):
        """
        Selects a player for the given team based on the draft strategy.

        team_index : which team is picking (0 = Team 1, 9 = Team 10)
        Returns    : one player as a dictionary (name, position, team, projected_points, vor)
        """

        # Count how many of each position this team has already drafted
        position_counts = {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'K': 0}
        for player in self.rosters[team_index]:
            pos = player['position']
            if pos in position_counts:
                position_counts[pos] += 1

        # Best player available, takes whoever has the highest projected points remaining
        if self.strategy == 'bpa':
            pick = self.available.sort_values(
                'projected_points', ascending=False
            ).iloc[0]
            return pick.to_dict()

        # Positional need, takes the best player among positions still needed to fill roster requirements
        elif self.strategy == 'need':
            # Build list of positions that still need more players
            needs = [
                pos for pos, required in self.roster_requirements.items()
                if position_counts.get(pos, 0) < required
            ]

            # Filter available players to only needed positions
            needed_players = self.available[self.available['position'].isin(needs)]

            # If no players available at needed positions, fall back to BPA
            if needed_players.empty:
                pick = self.available.sort_values(
                    'projected_points', ascending=False
                ).iloc[0]
            else:
                pick = needed_players.sort_values(
                    'projected_points', ascending=False
                ).iloc[0]

            return pick.to_dict()

        # Value Over Replacement, takes the player with the highest VOR among positions still needed to fill roster requirements
        elif self.strategy == 'vor':
            # Only consider positions not yet filled to requirement
            still_needed = [
                pos for pos, required in self.roster_requirements.items()
                if position_counts.get(pos, 0) < required
            ]

            # Filter available pool to only eligible positions
            eligible = self.available[self.available['position'].isin(still_needed)]

            # Fall back to BPA if somehow no eligible players exist
            if eligible.empty:
                pick = self.available.sort_values(
                    'projected_points', ascending=False
                ).iloc[0]
            else:
                # Key difference from NEED: sort by VOR not projected_points
                pick = eligible.sort_values('vor', ascending=False).iloc[0]

            return pick.to_dict()

        else:
            raise ValueError(f"Unknown strategy: {self.strategy}")
