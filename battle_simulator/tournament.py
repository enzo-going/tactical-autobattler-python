from __future__ import annotations

from dataclasses import dataclass

from battle_simulator.engine import BattleEngine
from battle_simulator.strategies import BalancedBot, RandomBot


@dataclass(frozen=True)
class TournamentSummary:
    simulations: int
    max_rounds: int
    player_one_wins: int
    player_two_wins: int
    draws: int
    average_rounds: float

    def to_dict(self) -> dict:
        return {
            "simulations": self.simulations,
            "max_rounds": self.max_rounds,
            "player_one_wins": self.player_one_wins,
            "player_two_wins": self.player_two_wins,
            "draws": self.draws,
            "average_rounds": self.average_rounds,
        }


def run_tournament(simulations: int, max_rounds: int, seed: int = 7) -> TournamentSummary:
    if simulations <= 0:
        raise ValueError("simulations must be greater than zero.")
    if max_rounds <= 0:
        raise ValueError("max_rounds must be greater than zero.")

    player_one_wins = 0
    player_two_wins = 0
    draws = 0
    total_rounds = 0

    for offset in range(simulations):
        engine = BattleEngine()
        result = engine.run(
            BalancedBot(),
            RandomBot(seed=seed + offset),
            max_rounds=max_rounds,
        )
        total_rounds += result.rounds_played

        if result.winner is None:
            draws += 1
        elif result.winner.value == 1:
            player_one_wins += 1
        else:
            player_two_wins += 1

    return TournamentSummary(
        simulations=simulations,
        max_rounds=max_rounds,
        player_one_wins=player_one_wins,
        player_two_wins=player_two_wins,
        draws=draws,
        average_rounds=round(total_rounds / simulations, 2),
    )
