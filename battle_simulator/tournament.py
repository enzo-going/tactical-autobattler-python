from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Callable

from battle_simulator.engine import BattleEngine, Player
from battle_simulator.strategies import (
    AggressiveBot,
    BalancedBot,
    DefensiveBot,
    EconomyBot,
    RandomBot,
    Strategy,
)


StrategyFactory = Callable[[int], Strategy]


STRATEGIES: dict[str, StrategyFactory] = {
    "aggressive": lambda seed: AggressiveBot(),
    "balanced": lambda seed: BalancedBot(),
    "defensive": lambda seed: DefensiveBot(),
    "economy": lambda seed: EconomyBot(),
    "random": lambda seed: RandomBot(seed=seed),
}


DEFAULT_STRATEGIES = ("aggressive", "balanced", "defensive", "economy")


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
    strategy_one_damage_dealt: float
    strategy_two_damage_dealt: float
    strategy_one_damage_taken: float
    strategy_two_damage_taken: float

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
            "strategy_one_damage_dealt": self.strategy_one_damage_dealt,
            "strategy_two_damage_dealt": self.strategy_two_damage_dealt,
            "strategy_one_damage_taken": self.strategy_one_damage_taken,
            "strategy_two_damage_taken": self.strategy_two_damage_taken,
        }


@dataclass(frozen=True)
class StrategySummary:
    name: str
    wins: int
    losses: int
    draws: int
    rounds_played: int
    damage_dealt: int
    damage_taken: int

    @property
    def matches(self) -> int:
        return self.wins + self.losses + self.draws

    @property
    def win_rate(self) -> float:
        if self.matches == 0:
            return 0.0
        return round(self.wins / self.matches, 3)

    @property
    def draw_rate(self) -> float:
        if self.matches == 0:
            return 0.0
        return round(self.draws / self.matches, 3)

    @property
    def average_rounds(self) -> float:
        if self.matches == 0:
            return 0.0
        return round(self.rounds_played / self.matches, 2)

    @property
    def average_damage_dealt(self) -> float:
        if self.matches == 0:
            return 0.0
        return round(self.damage_dealt / self.matches, 2)

    @property
    def average_damage_taken(self) -> float:
        if self.matches == 0:
            return 0.0
        return round(self.damage_taken / self.matches, 2)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "wins": self.wins,
            "losses": self.losses,
            "draws": self.draws,
            "win_rate": self.win_rate,
            "draw_rate": self.draw_rate,
            "average_rounds": self.average_rounds,
            "average_damage_dealt": self.average_damage_dealt,
            "average_damage_taken": self.average_damage_taken,
        }


@dataclass(frozen=True)
class TournamentSummary:
    simulations_per_matchup: int
    max_rounds: int
    strategies: tuple[str, ...]
    matchups: tuple[MatchupSummary, ...]
    standings: tuple[StrategySummary, ...]

    @property
    def simulations(self) -> int:
        return self.simulations_per_matchup * len(self.matchups)

    def to_dict(self) -> dict:
        return {
            "simulations": self.simulations,
            "simulations_per_matchup": self.simulations_per_matchup,
            "max_rounds": self.max_rounds,
            "strategies": list(self.strategies),
            "standings": [summary.to_dict() for summary in self.standings],
            "matchups": [matchup.to_dict() for matchup in self.matchups],
        }


def run_tournament(
    simulations: int,
    max_rounds: int,
    seed: int = 7,
    strategies: tuple[str, ...] = DEFAULT_STRATEGIES,
) -> TournamentSummary:
    if simulations <= 0:
        raise ValueError("simulations must be greater than zero.")
    if max_rounds <= 0:
        raise ValueError("max_rounds must be greater than zero.")
    if len(strategies) < 2:
        raise ValueError("at least two strategies are required.")

    matchups = _round_robin_matchups(strategies)
    matchup_summaries = tuple(
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
        strategies=strategies,
        matchups=matchup_summaries,
        standings=_build_standings(strategies, matchup_summaries),
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
    strategy_one_damage_dealt = 0
    strategy_two_damage_dealt = 0
    strategy_one_damage_taken = 0
    strategy_two_damage_taken = 0

    for offset in range(simulations):
        engine = BattleEngine()
        result = engine.run(
            STRATEGIES[strategy_one](seed + offset),
            STRATEGIES[strategy_two](seed + offset),
            max_rounds=max_rounds,
        )
        total_rounds += result.rounds_played
        strategy_one_damage_dealt += result.stats.damage_dealt[Player.ONE]
        strategy_two_damage_dealt += result.stats.damage_dealt[Player.TWO]
        strategy_one_damage_taken += result.stats.damage_taken[Player.ONE]
        strategy_two_damage_taken += result.stats.damage_taken[Player.TWO]

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
        strategy_one_damage_dealt=round(strategy_one_damage_dealt / simulations, 2),
        strategy_two_damage_dealt=round(strategy_two_damage_dealt / simulations, 2),
        strategy_one_damage_taken=round(strategy_one_damage_taken / simulations, 2),
        strategy_two_damage_taken=round(strategy_two_damage_taken / simulations, 2),
    )


def _round_robin_matchups(strategies: tuple[str, ...]) -> tuple[tuple[str, str], ...]:
    matchups: list[tuple[str, str]] = []
    for strategy_one, strategy_two in combinations(strategies, 2):
        matchups.append((strategy_one, strategy_two))
        matchups.append((strategy_two, strategy_one))
    return tuple(matchups)


def _build_standings(
    strategies: tuple[str, ...],
    matchups: tuple[MatchupSummary, ...],
) -> tuple[StrategySummary, ...]:
    rows = {
        strategy: {
            "wins": 0,
            "losses": 0,
            "draws": 0,
            "rounds_played": 0,
            "damage_dealt": 0,
            "damage_taken": 0,
        }
        for strategy in strategies
    }

    for matchup in matchups:
        _add_matchup_rows(rows, matchup)

    summaries = tuple(
        StrategySummary(name=strategy, **values)
        for strategy, values in rows.items()
    )
    return tuple(sorted(summaries, key=lambda item: (item.win_rate, item.wins), reverse=True))


def _add_matchup_rows(rows: dict, matchup: MatchupSummary) -> None:
    one = rows[matchup.strategy_one]
    two = rows[matchup.strategy_two]

    one["wins"] += matchup.strategy_one_wins
    one["losses"] += matchup.strategy_two_wins
    one["draws"] += matchup.draws
    one["rounds_played"] += int(matchup.average_rounds * matchup.simulations)
    one["damage_dealt"] += int(matchup.strategy_one_damage_dealt * matchup.simulations)
    one["damage_taken"] += int(matchup.strategy_one_damage_taken * matchup.simulations)

    two["wins"] += matchup.strategy_two_wins
    two["losses"] += matchup.strategy_one_wins
    two["draws"] += matchup.draws
    two["rounds_played"] += int(matchup.average_rounds * matchup.simulations)
    two["damage_dealt"] += int(matchup.strategy_two_damage_dealt * matchup.simulations)
    two["damage_taken"] += int(matchup.strategy_two_damage_taken * matchup.simulations)
