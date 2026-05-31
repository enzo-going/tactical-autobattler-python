from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from battle_simulator.engine import BattleEngine
from battle_simulator.strategies import AggressiveBot, BalancedBot, RandomBot, Strategy


StrategyFactory = Callable[[int], Strategy]


STRATEGIES: dict[str, StrategyFactory] = {
    "aggressive": lambda seed: AggressiveBot(),
    "balanced": lambda seed: BalancedBot(),
    "random": lambda seed: RandomBot(seed=seed),
}


DEFAULT_MATCHUPS = (
    ("balanced", "random"),
    ("aggressive", "random"),
    ("aggressive", "balanced"),
)


@dataclass(frozen=True)
class MatchupSummary:
    strategy_one: str
    strategy_two: str
    simulations: int
    max_rounds: int
    strategy_one_wins: int
    strategy_two_wins: int
    draws: int
    average_rounds: float

    @property
    def losses_for_strategy_one(self) -> int:
        return self.strategy_two_wins

    def to_dict(self) -> dict:
        return {
            "strategy_one": self.strategy_one,
            "strategy_two": self.strategy_two,
            "simulations": self.simulations,
            "max_rounds": self.max_rounds,
            "strategy_one_wins": self.strategy_one_wins,
            "strategy_two_wins": self.strategy_two_wins,
            "draws": self.draws,
            "losses_for_strategy_one": self.losses_for_strategy_one,
            "average_rounds": self.average_rounds,
        }


@dataclass(frozen=True)
class TournamentSummary:
    simulations_per_matchup: int
    max_rounds: int
    matchups: tuple[MatchupSummary, ...]

    @property
    def simulations(self) -> int:
        return self.simulations_per_matchup * len(self.matchups)

    def to_dict(self) -> dict:
        return {
            "simulations": self.simulations,
            "simulations_per_matchup": self.simulations_per_matchup,
            "max_rounds": self.max_rounds,
            "matchups": [matchup.to_dict() for matchup in self.matchups],
        }


def run_tournament(
    simulations: int,
    max_rounds: int,
    seed: int = 7,
    matchups: tuple[tuple[str, str], ...] = DEFAULT_MATCHUPS,
) -> TournamentSummary:
    if simulations <= 0:
        raise ValueError("simulations must be greater than zero.")
    if max_rounds <= 0:
        raise ValueError("max_rounds must be greater than zero.")
    if not matchups:
        raise ValueError("at least one matchup is required.")

    summaries = tuple(
        run_matchup(
            strategy_one=strategy_one,
            strategy_two=strategy_two,
            simulations=simulations,
            max_rounds=max_rounds,
            seed=seed + matchup_index * simulations,
        )
        for matchup_index, (strategy_one, strategy_two) in enumerate(matchups)
    )

    return TournamentSummary(
        simulations_per_matchup=simulations,
        max_rounds=max_rounds,
        matchups=summaries,
    )


def run_matchup(
    strategy_one: str,
    strategy_two: str,
    simulations: int,
    max_rounds: int,
    seed: int = 7,
) -> MatchupSummary:
    if strategy_one not in STRATEGIES:
        raise ValueError(f"Unknown strategy: {strategy_one}")
    if strategy_two not in STRATEGIES:
        raise ValueError(f"Unknown strategy: {strategy_two}")

    strategy_one_wins = 0
    strategy_two_wins = 0
    draws = 0
    total_rounds = 0

    for offset in range(simulations):
        engine = BattleEngine()
        result = engine.run(
            STRATEGIES[strategy_one](seed + offset),
            STRATEGIES[strategy_two](seed + offset),
            max_rounds=max_rounds,
        )
        total_rounds += result.rounds_played

        if result.winner is None:
            draws += 1
        elif result.winner.value == 1:
            strategy_one_wins += 1
        else:
            strategy_two_wins += 1

    return MatchupSummary(
        strategy_one=strategy_one,
        strategy_two=strategy_two,
        simulations=simulations,
        max_rounds=max_rounds,
        strategy_one_wins=strategy_one_wins,
        strategy_two_wins=strategy_two_wins,
        draws=draws,
        average_rounds=round(total_rounds / simulations, 2),
    )
