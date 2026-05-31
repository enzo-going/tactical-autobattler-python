from __future__ import annotations

import argparse
import json
from pathlib import Path

from battle_simulator.engine import AttackOrder, BattleEngine, Player, RecruitOrder, TurnPlan
from battle_simulator.models import Lane, TROOP_COSTS, TroopKind
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
            f"Tournament: {summary.simulations} simulations "
            f"across {len(summary.matchups)} matchups."
        )
        for matchup in summary.matchups:
            print(
                f"- {matchup.strategy_one} vs {matchup.strategy_two}: "
                f"{matchup.strategy_one_wins}-{matchup.strategy_two_wins}, "
                f"{matchup.draws} draws, "
                f"{matchup.average_rounds} average rounds."
            )
        print("Standings:")
        for row in summary.standings:
            print(
                f"- {row.name}: {row.wins}W/{row.losses}L/{row.draws}D, "
                f"{row.win_rate:.3f} win rate, "
                f"{row.draw_rate:.3f} draw rate, "
                f"{row.average_rounds} avg rounds, "
                f"{row.average_damage_dealt}/{row.average_damage_taken} avg damage."
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
        choice = input(
            "Recruit [s]oldier, [a]rcher, [g]uardian, [m]edic, [t]ank or [enter] to stop: "
        ).strip().lower()
        if not choice:
            break
        troop_kind = {
            "s": TroopKind.SOLDIER,
            "a": TroopKind.ARCHER,
            "g": TroopKind.GUARDIAN,
            "m": TroopKind.MEDIC,
            "t": TroopKind.TANK,
        }.get(choice)
        if troop_kind is None:
            print("Invalid option.")
            continue
        cost = TROOP_COSTS[troop_kind]
        if budget < cost:
            print("Not enough resources.")
            continue
        budget -= cost
        lane = Lane.BACK if troop_kind in {TroopKind.ARCHER, TroopKind.MEDIC} else Lane.FRONT
        recruits.append(RecruitOrder(troop_kind, lane=lane))

    attacks = []
    for index, troop in enumerate(troops):
        print(f"{index}: {troop.name} ({troop.health}/{troop.max_hp} HP, {troop.lane.value})")
        attacks.append(AttackOrder(index, None))

    return TurnPlan(recruits=tuple(recruits), attacks=tuple(attacks))


def _print_state(engine: BattleEngine) -> None:
    battlefield = engine.battlefield
    print("\n=== Battlefield ===")
    for player in Player:
        base = battlefield.base_for(player)
        print(f"{base.name}: {base.health} HP, {base.resources} resources")
        for troop in battlefield.troops_for(player):
            print(
                f"  - {troop.name}: {troop.health}/{troop.max_hp} HP, "
                f"{troop.attack} attack, {troop.defense} defense, {troop.lane.value}"
            )


def _build_report(engine: BattleEngine, result) -> dict:
    battlefield = engine.battlefield
    return {
        "winner": None if result.winner is None else battlefield.base_for(result.winner).name,
        "rounds_played": result.rounds_played,
        "strategies": {
            "player_one": result.strategies.get(Player.ONE),
            "player_two": result.strategies.get(Player.TWO),
        },
        "units_recruited": {
            "player_one": result.stats.units_recruited[Player.ONE],
            "player_two": result.stats.units_recruited[Player.TWO],
        },
        "damage": {
            "player_one": {
                "dealt": result.stats.damage_dealt[Player.ONE],
                "received": result.stats.damage_taken[Player.ONE],
            },
            "player_two": {
                "dealt": result.stats.damage_dealt[Player.TWO],
                "received": result.stats.damage_taken[Player.TWO],
            },
        },
        "bases": {
            "player_one": _base_snapshot(battlefield.base_for(Player.ONE)),
            "player_two": _base_snapshot(battlefield.base_for(Player.TWO)),
        },
        "troops_remaining": {
            "player_one": [_troop_snapshot(troop) for troop in battlefield.troops_for(Player.ONE)],
            "player_two": [_troop_snapshot(troop) for troop in battlefield.troops_for(Player.TWO)],
        },
        "event_count": len(result.events),
        "events": [event.to_dict() for event in result.events],
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
        "role": troop.role.value,
        "lane": troop.lane.value,
        "max_hp": troop.max_hp,
        "current_hp": troop.health,
        "attack": troop.attack,
        "defense": troop.defense,
        "speed": troop.speed,
        "range": troop.range,
        "cost": troop.cost,
        "effects": {effect.value: duration for effect, duration in troop.effects.items()},
        "damage_dealt": troop.damage_dealt,
        "damage_received": troop.damage_received,
    }


if __name__ == "__main__":
    raise SystemExit(main())
