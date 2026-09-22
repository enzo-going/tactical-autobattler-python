import json
import unittest
from copy import deepcopy

from battle_simulator.engine import Player
from battle_simulator.models import Archer, Guardian, Lane, Medic, Soldier, StatusEffect, Tank
from battle_simulator.session import TacticalSession


class PreparationTest(unittest.TestCase):
    def test_formation_is_free_and_does_not_consume_the_combat_action(self):
        game = TacticalSession(seed=0)
        game.command({"type": "recruit", "kind": "guardian", "lane": "front"})
        game.command({"type": "deploy", "actor": "Guardian 1", "lane": "back"})
        self.assertEqual(game.field.base_one.resources, 6)
        self.assertEqual(game.field.troops_one[0].lane, Lane.BACK)
        self.assertEqual(game.acted, set())
        self.assertEqual(game.field.troops_two, [])
        game.command({"type": "begin"})
        self.assertIn("Guardian 1", game.state()["legal_actions"])
        with self.assertRaises(ValueError):
            game.command({"type": "deploy", "actor": "Guardian 1", "lane": "front"})

    def test_return_refunds_once_and_does_not_reuse_identity(self):
        game = TacticalSession()
        game.command({"type": "recruit", "kind": "tank", "lane": "front"})
        game.command({"type": "deploy", "actor": "Tank 1", "lane": "back"})
        game.command({"type": "return", "actor": "Tank 1"})
        self.assertEqual(game.field.base_one.resources, 10)
        self.assertEqual(game.engine.stats.units_recruited[Player.ONE], 0)
        before = deepcopy(game.report())
        with self.assertRaises(ValueError):
            game.command({"type": "return", "actor": "Tank 1"})
        self.assertEqual(game.report(), before)
        game.command({"type": "recruit", "kind": "tank", "lane": "front"})
        self.assertEqual(game.field.troops_one[0].name, "Tank 2")

    def test_survivors_can_redeploy_but_cannot_be_refunded(self):
        game = TacticalSession(seed=0)
        game.command({"type": "recruit", "kind": "guardian", "lane": "front"})
        game.command({"type": "begin"})
        game.command({"type": "act", "actor": "Guardian 1", "action": "wait"})
        game.command({"type": "next"})
        self.assertEqual(game.state()["refundable"], [])
        with self.assertRaises(ValueError):
            game.command({"type": "return", "actor": "Guardian 1"})
        game.command({"type": "deploy", "actor": "Guardian 1", "lane": "back"})

    def test_invalid_preparation_orders_are_atomic(self):
        game = TacticalSession()
        game.command({"type": "recruit", "kind": "soldier", "lane": "front"})
        for order in [
            {"type": "deploy", "actor": "Soldier 1", "lane": "front"},
            {"type": "deploy", "actor": "Soldier 1", "lane": "invalid"},
            {"type": "deploy", "actor": "Enemy", "lane": "back"},
            {"type": "return", "actor": "Enemy"},
        ]:
            before = deepcopy(game.report())
            with self.assertRaises(ValueError):
                game.command(order)
            self.assertEqual(game.report(), before)

    def test_preparation_commands_replay_exactly(self):
        game = TacticalSession(seed=3)
        for order in [
            {"type": "recruit", "kind": "soldier", "lane": "front"},
            {"type": "deploy", "actor": "Soldier 1", "lane": "back"},
            {"type": "return", "actor": "Soldier 1"},
            {"type": "recruit", "kind": "pikeman", "lane": "back"},
            {"type": "begin"},
        ]:
            game.command(order)
        report = json.loads(json.dumps(game.report()))
        replay = TacticalSession(**report["config"])
        for order in report["commands"]:
            replay.command(order)
        self.assertEqual(replay.report(), report)


class TacticalDecisionTest(unittest.TestCase):
    def game(self, allies, enemies):
        game = TacticalSession(seed=0)
        game.field.troops_one, game.field.troops_two = allies, enemies
        game.field.base_two.resources = 0
        game.command({"type": "begin"})
        return game

    def test_damage_preview_matches_resolution_without_consuming_shield(self):
        for attack in (1, 3, 20):
            for shield in (False, True):
                target = Guardian("Target")
                if shield:
                    target.add_effect(StatusEffect.SHIELD, 2)
                before = deepcopy(target)
                amount = target.preview_damage(attack)
                self.assertEqual(target, before)
                self.assertEqual(target.receive_damage(attack), amount)

    def test_action_preview_matches_hit_and_does_not_mutate_state(self):
        target = Guardian("Guardian 2")
        target.add_effect(StatusEffect.SHIELD, 2)
        game = self.game([Archer("Archer 1"), Guardian("Guardian 1")], [target])
        before = deepcopy(target)
        preview = game.state()["action_previews"]["Archer 1"][0]
        self.assertEqual(target, before)
        self.assertEqual(preview["damage"], 0)
        self.assertEqual(preview["effects"], [])
        game.command({"type": "act", "actor": "Archer 1", "action": "attack", "target": target.name})
        self.assertEqual(target.health, preview["remaining_hp"])

    def test_preview_distinguishes_kill_bleed_heal_and_base(self):
        wounded = Soldier("Soldier 1")
        wounded.health = 3
        target = Soldier("Soldier 2")
        game = self.game([Archer("Archer 1"), Medic("Medic 1"), wounded], [target])
        preview = game.state()["action_previews"]["Archer 1"][0]
        self.assertEqual(preview["effects"], ["bleed"])
        target.health = 1
        preview = game.state()["action_previews"]["Archer 1"][0]
        self.assertTrue(preview["defeats"])
        self.assertEqual(preview["effects"], [])
        healing = next(p for p in game.state()["action_previews"]["Medic 1"] if p["action"] == "heal")
        self.assertEqual(healing["healing"], 1)
        game.field.troops_two = []
        game.field.base_two.health = 2
        preview = game.state()["action_previews"]["Archer 1"][0]
        self.assertTrue(preview["defeats"])
        self.assertEqual(preview["damage"], 2)

    def test_enemy_advances_melee_trapped_behind_its_front(self):
        rear = Soldier("Soldier 2", Lane.BACK)
        game = self.game([Guardian("Guardian 1")], [Guardian("Guardian 2"), rear])
        self.assertEqual(game._enemy_choice(rear), {"action": "move", "lane": "front"})
        game.command({"type": "act", "actor": "Guardian 1", "action": "wait"})
        self.assertEqual(rear.lane, Lane.FRONT)

    def test_reloading_enemy_guards_instead_of_wasting_exposed_action(self):
        tank = Tank("Tank 2")
        tank.ready_round = 3
        game = self.game([Archer("Archer 1")], [tank])
        self.assertEqual(game._enemy_choice(tank), {"action": "guard", "target": tank.name})

    def test_guardian_saves_ally_from_exact_lethal_hit(self):
        medic = Medic("Medic 2", Lane.FRONT)
        medic.health = 2
        guardian = Guardian("Guardian 2")
        game = self.game([Soldier("Soldier 1")], [guardian, medic])
        self.assertEqual(game._enemy_choice(guardian), {"action": "guard", "target": medic.name})

    def test_enemy_does_not_waste_shield_on_an_unsurvivable_hit(self):
        medic = Medic("Medic 2", Lane.FRONT)
        medic.health = 1
        guardian = Guardian("Guardian 2")
        game = self.game([Tank("Tank 1")], [guardian, medic])
        self.assertEqual(game._enemy_choice(guardian)["action"], "attack")

    def test_enemy_takes_finishing_blow_before_healing(self):
        target = Archer("Archer 1")
        target.health = 1
        medic = Medic("Medic 2", Lane.FRONT)
        guardian = Guardian("Guardian 2")
        guardian.health = 8
        game = self.game([target], [medic, guardian])
        self.assertEqual(game._enemy_choice(medic), {"action": "attack", "target": target.name})
