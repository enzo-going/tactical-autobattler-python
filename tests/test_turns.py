"""Full-side turns are authoritative, incremental and safe to resume."""
import json
import unittest

from battle_simulator.engine import Player
from battle_simulator.models import Guardian, Soldier, StatusEffect, Tank
from battle_simulator.session import TacticalSession


class FullTurnTests(unittest.TestCase):
    def game(self, allies=None, enemies=None):
        game = TacticalSession(seed=11)
        game.field.troops_one = allies if allies is not None else [Guardian("A"), Guardian("B")]
        game.field.troops_two = enemies if enemies is not None else [Soldier("X"), Soldier("Y")]
        game.field.base_two.resources = 0
        game.command({"type": "begin"})
        return game

    def test_entire_player_turn_happens_before_any_enemy_order(self):
        game = self.game()
        for actor in ("A", "B"):
            game.command({"type": "act", "actor": actor, "action": "wait"})
            self.assertFalse(game.acted & {"X", "Y"})
        self.assertEqual(game.phase, "enemy")
        self.assertEqual(game.state()["active_player"], 2)
        self.assertEqual(game.state()["legal_actions"], {})
        self.assertEqual(game.state()["remaining_actions"]["player_two"], 2)
        before = game.report()
        for _ in range(3):
            self.assertEqual(game.report(), before)
        game.command({"type": "enemy_step"})
        self.assertEqual(len(game.acted & {"X", "Y"}), 1)
        self.assertEqual(game.phase, "enemy")
        game.command({"type": "enemy_step"})
        self.assertEqual(len(game.acted & {"X", "Y"}), 2)
        self.assertEqual(game.phase, "review")
        self.assertEqual(game.field.base_one.resources, 16)

    def test_end_turn_early_forfeits_pending_actions(self):
        game = self.game()
        game.command({"type": "end_turn"})
        self.assertTrue({"A", "B"} <= game.acted)
        self.assertEqual(game.phase, "enemy")
        self.assertEqual(sum(e.event_type == "unit_waited" for e in game.engine.events), 2)
        before = json.dumps(game.report(), sort_keys=True)
        for command in ({"type": "end_turn"}, {"type": "begin"}, {"type": "next"},
                        {"type": "act", "actor": "A", "action": "wait"},
                        {"type": "recruit", "kind": "soldier", "lane": "front"}):
            with self.assertRaises(ValueError):
                game.command(command)
            self.assertEqual(json.dumps(game.report(), sort_keys=True), before)

    def test_enemy_cannot_act_during_player_turn_or_after_review(self):
        game = self.game()
        before = game.state()
        with self.assertRaises(ValueError):
            game.command({"type": "enemy_step"})
        self.assertEqual(game.state(), before)
        game.command({"type": "end_turn"})
        while game.phase == "enemy":
            game.command({"type": "enemy_step"})
        before = game.state()
        with self.assertRaises(ValueError):
            game.command({"type": "enemy_step"})
        self.assertEqual(game.state(), before)

    def test_enemy_victory_stops_remaining_orders(self):
        game = self.game(allies=[], enemies=[Tank("Tank X"), Soldier("Y")])
        game.field.base_one.health = 1
        game.command({"type": "enemy_step"})
        self.assertEqual(game.phase, "finished")
        self.assertEqual(game.winner, Player.TWO)
        self.assertEqual(len(game.acted), 1)
        self.assertEqual(game.field.base_one.resources, 10)
        with self.assertRaises(ValueError):
            game.command({"type": "enemy_step"})

    def test_stunned_armies_do_not_stall_the_round(self):
        ally, enemy = Guardian("A"), Guardian("X")
        for troop in (ally, enemy):
            troop.add_effect(StatusEffect.STUN, 2)
        game = self.game([ally], [enemy])
        self.assertEqual(game.phase, "review")
        self.assertEqual(game.field.base_one.resources, 16)

    def test_resume_mid_enemy_turn_does_not_repeat_actions(self):
        game = TacticalSession(seed=11)
        game.command({"type": "recruit", "kind": "guardian", "lane": "front"})
        game.command({"type": "begin"})
        game.command({"type": "end_turn"})
        game.command({"type": "enemy_step"})
        self.assertEqual(game.phase, "enemy")
        restored = TacticalSession.from_report(json.loads(json.dumps(game.checkpoint())))
        self.assertEqual(restored.report(), game.report())
        while game.phase == "enemy":
            self.assertEqual(game.command({"type": "enemy_step"}),
                             restored.command({"type": "enemy_step"}))
        self.assertEqual(restored.report(), game.report())
