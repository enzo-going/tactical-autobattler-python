"""Portable saves replay legal commands and replace a session only on success."""

import json
import unittest

from battle_simulator.session import TacticalSession
from web import playground


class SaveTests(unittest.TestCase):
    def test_resume_every_phase_and_continue_deterministically(self):
        for opponent in ("balanced", "random", "economy"):
            game = TacticalSession(opponent=opponent, seed=0, max_rounds=3)
            phases = set()
            for _ in range(100):
                state = game.state()
                phases.add(game.phase)
                for document in (game.checkpoint(), game.report()):
                    restored = TacticalSession.from_report(json.loads(json.dumps(document)))
                    self.assertEqual(restored.report(), game.report())
                if game.phase == "finished":
                    break
                if game.phase == "recruit":
                    if game.field.base_one.resources >= 4 and len(game.field.troops_one) < 4:
                        command = {"type": "recruit", "kind": "guardian", "lane": "front"}
                    else:
                        command = {"type": "begin"}
                elif game.phase == "enemy":
                    command = {"type": "enemy_step"}
                elif game.phase == "review":
                    command = {"type": "next"}
                else:
                    actor, choices = next(iter(state["legal_actions"].items()))
                    command = {"type": "act", "actor": actor, **choices[0]}
                self.assertEqual(game.command(command), restored.command(command))
            self.assertEqual(phases, {"recruit", "combat", "enemy", "review", "finished"})

    def test_refunds_and_factory_ids_survive_resume(self):
        game = TacticalSession()
        game.command({"type": "recruit", "kind": "soldier", "lane": "front"})
        game.command({"type": "return", "actor": "Soldier 1"})
        game.command({"type": "recruit", "kind": "soldier", "lane": "back"})
        game.command({"type": "deploy", "actor": "Soldier 2", "lane": "front"})
        restored = TacticalSession.from_report(game.checkpoint())
        self.assertEqual(restored.report(), game.report())
        self.assertEqual(restored.refundable, {"Soldier 2"})
        command = {"type": "recruit", "kind": "soldier", "lane": "front"}
        self.assertEqual(restored.command(command), game.command(command))

    def test_checkpoint_does_not_expose_mutable_history(self):
        game = TacticalSession()
        game.command({"type": "recruit", "kind": "soldier", "lane": "front"})
        checkpoint = game.checkpoint()
        checkpoint["commands"][0]["kind"] = "tank"
        self.assertEqual(game.commands[0]["kind"], "soldier")

    def test_rejects_wrong_format_rules_and_config(self):
        valid = TacticalSession().checkpoint()
        invalid = [None, [], {}, {**valid, "schema_version": True},
                   {**valid, "schema_version": 2}, {**valid, "ruleset": "tactical-v5"},
                   {**valid, "mode": "auto"}, {**valid, "config": []},
                   {**valid, "config": {**valid["config"], "opponent": []}},
                   {**valid, "config": {**valid["config"], "seed": True}},
                   {**valid, "config": {**valid["config"], "max_rounds": 51}},
                   {**valid, "config": {"opponent": "balanced"}}]
        for document in invalid:
            with self.subTest(document=document), self.assertRaises(ValueError):
                TacticalSession.from_report(document)

    def test_rejects_malformed_or_illegal_history(self):
        valid = TacticalSession().checkpoint()
        for commands in (None, {}, [None], [{"type": []}], [{"type": "begin", "extra": "x"}],
                         [{"type": "act", "actor": "Soldier 1", "action": "wait"}],
                         [{"type": "recruit", "kind": "soldier", "lane": "bad"}],
                         [{"type": "next"}] * 2001):
            with self.subTest(commands=str(commands)[:100]), self.assertRaises(ValueError):
                TacticalSession.from_report({**valid, "commands": commands})

    def test_rejects_snapshot_that_disagrees_with_history(self):
        report = TacticalSession().report()
        report["state"]["bases"]["player_one"]["resources"] = 999
        with self.assertRaisesRegex(ValueError, "estado salvo"):
            TacticalSession.from_report(report)

    def test_bridge_invalid_import_preserves_live_session(self):
        playground.new_game("balanced", 0, 3)
        playground.game_command('{"type":"recruit","kind":"tank","lane":"front"}')
        before = playground.game_report()
        bad_command = json.loads(playground.game_save())
        bad_command["commands"].append({"type": "next"})
        for contents in ("broken json", "null", "[" * 1500, " " * (2 * 1024 * 1024 + 1),
                         json.dumps(bad_command)):
            with self.subTest(contents=contents[:60]), self.assertRaises(ValueError):
                playground.load_game(contents)
            self.assertEqual(playground.game_report(), before)

    def test_bridge_accepts_compact_and_full_export(self):
        playground.new_game("random", 7, 5)
        playground.game_command('{"type":"recruit","kind":"archer","lane":"back"}')
        expected = json.loads(playground.game_report())
        for saved in (playground.game_save(), playground.game_report()):
            playground.new_game("economy", 0, 1)
            state = json.loads(playground.load_game(saved))
            self.assertEqual(state, expected["state"])
            self.assertEqual(json.loads(playground.game_report()), expected)


if __name__ == "__main__":
    unittest.main()
