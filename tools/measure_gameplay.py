"""Controlled interactive matches; a fixed player policy is not a human playtest."""

import argparse
from collections import Counter
from copy import deepcopy
import json
from pathlib import Path
import sys


def measure():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    sys.path.insert(0, str(args.source.resolve()))
    from battle_simulator.models import TROOP_COSTS, TroopKind
    from battle_simulator.session import TacticalSession

    loadouts = {
        "front": ["soldier"],
        "ranged": ["archer"],
        "mixed": ["guardian", "pikeman", "archer", "medic", "tank", "soldier"],
    }
    rows = []
    for opponent in ("balanced", "aggressive", "defensive", "economy", "random"):
        for loadout, kinds in loadouts.items():
            for seed in (0, 1, 11, 12):
                game = TacticalSession(opponent, seed, max_rounds=12)
                purchase = 0
                for _ in range(1000):
                    state = game.state()
                    if game.phase == "finished":
                        break
                    if game.phase == "recruit":
                        kind = kinds[purchase % len(kinds)]
                        if len(game.field.troops_one) < 8 and game.field.base_one.resources >= TROOP_COSTS[TroopKind(kind)]:
                            lane = "back" if kind in ("archer", "pikeman", "medic") else "front"
                            game.command({"type": "recruit", "kind": kind, "lane": lane})
                            purchase += 1
                        else:
                            game.command({"type": "begin"})
                    elif game.phase == "review":
                        game.command({"type": "next"})
                    else:
                        actor = max((t for t in game.field.troops_one if t.name in state["legal_actions"]),
                                    key=lambda t: (t.speed, t.attack))
                        choices = state["legal_actions"][actor.name]
                        heals = [c for c in choices if c["action"] == "heal"]
                        attacks = [c for c in choices if c["action"] == "attack"]
                        if heals:
                            choice = heals[0]
                        elif attacks:
                            def target_health(choice):
                                if choice["target"] == "base":
                                    return 0
                                target = next(t for t in game.field.troops_two if t.name == choice["target"])
                                damage = deepcopy(target).receive_damage(actor.attack)
                                return target.health - damage
                            choice = min(attacks, key=target_health)
                        else:
                            move = {"action": "move", "lane": "front"}
                            choice = move if move in choices else {"action": "guard", "target": actor.name}
                            if choice not in choices:
                                choice = {"action": "wait"}
                        game.command({"type": "act", "actor": actor.name, **choice})
                else:
                    raise AssertionError("Interactive game exceeded the command limit")
                enemy_actions = Counter(e.event_type for e in game.engine.events if e.player == 2)
                rows.append({"opponent": opponent, "loadout": loadout, "seed": seed,
                             "winner": game.winner.value if game.winner else None,
                             "rounds": game.engine.round_number, "reason": game.reason,
                             "enemy_waits": enemy_actions["unit_waited"],
                             "enemy_moves": enemy_actions["unit_moved"],
                             "enemy_guards": enemy_actions["shield"]})
    summary = {"games": len(rows), "player_wins": sum(r["winner"] == 1 for r in rows),
               "enemy_wins": sum(r["winner"] == 2 for r in rows),
               "average_rounds": round(sum(r["rounds"] for r in rows) / len(rows), 2),
               "round_limit": sum(r["reason"] == "round_limit" for r in rows),
               **{key: sum(r[key] for r in rows) for key in ("enemy_waits", "enemy_moves", "enemy_guards")}}
    print(json.dumps(summary, indent=2))
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps({"summary": summary, "matches": rows}, indent=2), encoding="utf-8")


if __name__ == "__main__":
    measure()
