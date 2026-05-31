from __future__ import annotations

import argparse
import json
from pathlib import Path

from battle_simulator.engine import AttackOrder, BattleEngine, Player, RecruitOrder, TurnPlan
from battle_simulator.models import TroopKind
from battle_simulator.strategies import BalancedBot, RandomBot
from battle_simulator.tournament import run_tournament


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the Battle Simulator.")
    parser.add_argument(
        "--mode",
        choices=("auto", "interactive", "tournament"),
        default="auto",
        help="Simulation mode. Defaults to auto.",
    )
    parser.add_argument("--rounds", type=int, default=30, help="Maximum number of rounds.")
    parser.add_argument("--seed", type=int, default=7, help="Seed for random mode.")
    parser.add_argument(
        "--simulations",
        type=int,
        default=100,
        help="Number of simulations for tournament mode.",
    )
    parser.add_argument("--quiet", action="store_true", help="Print only the final result.")
    parser.add_argument(
        "--report-json",
        type=Path,
        help="Write a machine-readable battle report to this path.",
    )
    args = parser.parse_args(argv)

    if args.mode == "tournament":
        summary = run_tournament(args.simulations, args.rounds, seed=args.seed)
        print(
            "Tournament: "
            f"{summary.player_one_wins} player-one wins, "
            f"{summary.player_two_wins} player-two wins, "
            f"{summary.draws} draws, "
            f"{summary.average_rounds} average rounds."
        )
        if args.report_json:
            args.report_json.parent.mkdir(parents=True, exist_ok=True)
            args.report_json.write_text(
                json.dumps(summary.to_dict(), indent=2),
                encoding="utf-8",
            )
        return 0

    engine = BattleEngine()
    if args.mode == "interactive":
        result = _run_interactive(engine, args.rounds)
    else:
        result = engine.run(BalancedBot(), RandomBot(seed=args.seed), max_rounds=args.rounds)

    if not args.quiet:
        for event in result.events:
            print(event.message)

    if result.winner is None:
        print(f"Draw after {result.rounds_played} rounds.")
    else:
        winner_base = engine.battlefield.base_for(result.winner)
        print(f"{winner_base.name} wins after {result.rounds_played} rounds.")

    if args.report_json:
        args.report_json.parent.mkdir(parents=True, exist_ok=True)
        args.report_json.write_text(
            json.dumps(_build_report(engine, result), indent=2),
            encoding="utf-8",
        )

    return 0


def _run_interactive(engine: BattleEngine, max_rounds: int):
    while engine.battlefield.winner() is None and engine.round_number < max_rounds:
        _print_state(engine)
        plans = {
            Player.ONE: _read_plan(Player.ONE, engine),
            Player.TWO: BalancedBot().choose_plan(Player.TWO, engine.battlefield),
        }
        engine.play_round(plans)

    from battle_simulator.engine import BattleResult

    return BattleResult(
        winner=engine.battlefield.winner(),
        rounds_played=engine.round_number,
        events=engine.events,
    )


def _read_plan(player: Player, engine: BattleEngine) -> TurnPlan:
    base = engine.battlefield.base_for(player)
    troops = engine.battlefield.troops_for(player)
    recruits: list[RecruitOrder] = []
    budget = base.resources

    print(f"\n{base.name} resources: {budget}")
    while True:
        choice = input("Recruit [s]oldier, [t]ank or [enter] to stop: ").strip().lower()
        if not choice:
            break
        troop_kind = {"s": TroopKind.SOLDIER, "t": TroopKind.TANK}.get(choice)
        if troop_kind is None:
            print("Invalid option.")
            continue
        cost = 2 if troop_kind == TroopKind.SOLDIER else 5
        if budget < cost:
            print("Not enough resources.")
            continue
        budget -= cost
        recruits.append(RecruitOrder(troop_kind))

    attacks = []
    for index, troop in enumerate(troops):
        print(f"{index}: {troop.name} ({troop.health} HP)")
        attacks.append(AttackOrder(index, None))

    return TurnPlan(recruits=tuple(recruits), attacks=tuple(attacks))


def _print_state(engine: BattleEngine) -> None:
    battlefield = engine.battlefield
    print("\n=== Battlefield ===")
    for player in Player:
        base = battlefield.base_for(player)
        print(f"{base.name}: {base.health} HP, {base.resources} resources")
        for troop in battlefield.troops_for(player):
            print(f"  - {troop.name}: {troop.health} HP, {troop.damage} damage")


def _build_report(engine: BattleEngine, result) -> dict:
    battlefield = engine.battlefield
    return {
        "winner": None if result.winner is None else battlefield.base_for(result.winner).name,
        "rounds_played": result.rounds_played,
        "bases": {
            "player_one": _base_snapshot(battlefield.base_for(Player.ONE)),
            "player_two": _base_snapshot(battlefield.base_for(Player.TWO)),
        },
        "troops_remaining": {
            "player_one": [_troop_snapshot(troop) for troop in battlefield.troops_for(Player.ONE)],
            "player_two": [_troop_snapshot(troop) for troop in battlefield.troops_for(Player.TWO)],
        },
        "event_count": len(result.events),
    }


def _base_snapshot(base) -> dict:
    return {
        "name": base.name,
        "health": base.health,
        "resources": base.resources,
    }


def _troop_snapshot(troop) -> dict:
    return {
        "name": troop.name,
        "health": troop.health,
        "damage": troop.damage,
        "cost": troop.cost,
    }


if __name__ == "__main__":
    raise SystemExit(main())
