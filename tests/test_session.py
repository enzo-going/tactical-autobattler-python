import json
import unittest

from battle_simulator.engine import Player
from battle_simulator.models import (
    Archer,
    Guardian,
    Lane,
    Medic,
    Pikeman,
    Soldier,
    StatusEffect,
    Tank,
)
from battle_simulator.session import TacticalSession
from web import playground


class TacticalSessionTest(unittest.TestCase):
    def combat(self, allies, enemies, rounds=20):
        game = TacticalSession(seed=0, max_rounds=rounds)
        game.field.troops_one = allies
        game.field.troops_two = enemies
        game.field.base_two.resources = 0
        game.command({"type": "begin"})
        return game

    def act(self, game, actor, action, **kwargs):
        return game.command({"type": "act", "actor": actor, "action": action, **kwargs})

    def test_initial_state_waits_for_player(self):
        game = TacticalSession()
        self.assertEqual(game.state(), game.state())
        self.assertEqual(game.phase, "recruit")
        self.assertEqual(game.engine.round_number, 1)
        self.assertEqual(game.field.base_one.resources, 10)

    def test_recruit_spends_resources_and_keeps_phase(self):
        game = TacticalSession()
        game.command({"type": "recruit", "kind": "archer", "lane": "front"})
        self.assertEqual(game.field.base_one.resources, 7)
        self.assertEqual(game.field.troops_one[0].lane, Lane.FRONT)
        self.assertEqual(game.phase, "recruit")

    def test_invalid_commands_are_atomic(self):
        game = TacticalSession()
        for command in [
            None,
            {},
            {"type": "next"},
            {"type": "act"},
            {"type": "recruit", "kind": "unknown", "lane": "front"},
            {"type": "recruit", "kind": "soldier", "lane": "bad"},
        ]:
            before = json.dumps(game.report(), sort_keys=True)
            with self.assertRaises(ValueError):
                game.command(command)
            self.assertEqual(json.dumps(game.report(), sort_keys=True), before)

    def test_unaffordable_purchase_does_not_consume_unit_id(self):
        game = TacticalSession()
        game.field.base_one.resources = 0
        with self.assertRaises(ValueError):
            game.command({"type": "recruit", "kind": "tank", "lane": "front"})
        game.field.base_one.resources = 5
        game.command({"type": "recruit", "kind": "tank", "lane": "front"})
        self.assertEqual(game.field.troops_one[0].name, "Tank 1")

    def test_roster_limit_applies_to_both_sides(self):
        game = TacticalSession()
        game.field.base_one.resources = game.field.base_two.resources = 100
        for _ in range(8):
            game.command({"type": "recruit", "kind": "soldier", "lane": "front"})
        with self.assertRaises(ValueError):
            game.command({"type": "recruit", "kind": "soldier", "lane": "front"})
        game.command({"type": "begin"})
        self.assertLessEqual(len(game.field.troops_two), 8)

    def test_recruits_are_ready_this_round_and_bot_replies_once(self):
        game = TacticalSession(seed=0)
        for _ in range(2):
            game.command({"type": "recruit", "kind": "soldier", "lane": "front"})
        game.command({"type": "begin"})
        self.assertEqual(len(game.state()["legal_actions"]), 2)
        self.act(game, "Soldier 1", "guard", target="Soldier 1")
        self.assertEqual(sum(t.name in game.acted for t in game.field.troops_two), 1)
        self.assertNotIn("Soldier 1", game.state()["legal_actions"])

    def test_frontline_blocks_melee_but_not_archers(self):
        """Da retaguarda, o arco alcanca a frente inimiga; a espada nao alcanca nada.

        E, com a frente inimiga de pe, nem o arco chega a retaguarda deles: sao
        tres fileiras de distancia.
        """
        game = self.combat(
            [Soldier("Soldier 1"), Archer("Archer 1")], [Guardian("Guardian 1"), Archer("Archer 2")]
        )
        actions = game.state()["legal_actions"]
        self.assertIn({"action": "attack", "target": "Guardian 1"}, actions["Soldier 1"])
        self.assertNotIn({"action": "attack", "target": "Archer 2"}, actions["Soldier 1"])
        self.assertIn({"action": "attack", "target": "Guardian 1"}, actions["Archer 1"])
        self.assertNotIn({"action": "attack", "target": "Archer 2"}, actions["Archer 1"])
        before = game.state()
        with self.assertRaises(ValueError):
            self.act(game, "Soldier 1", "attack", target="Archer 2")
        self.assertEqual(game.state(), before)

    def test_reload_blocks_the_weapon_but_not_the_rest_of_the_turn(self):
        """Arma recarregando tira o golpe da lista, nao a rodada inteira."""
        martelo = Tank("Martelo 1", lane=Lane.FRONT)
        game = self.combat(
            [martelo, Soldier("Escudeiro 1", lane=Lane.FRONT)],
            [Guardian("Muralha 1", lane=Lane.FRONT)],
        )
        # Sem renda o rival nao recruta, e o teste mede so a recarga.
        game.field.base_two.resource_income = 0

        self.assertTrue(
            [a for a in game.state()["legal_actions"]["Martelo 1"] if a["action"] == "attack"]
        )
        self.act(game, "Martelo 1", "attack", target="Muralha 1")

        rodada = game.engine.round_number
        # Recarga 1: fora nesta rodada e na proxima, pronta na seguinte.
        self.assertFalse(martelo.is_loaded(rodada))
        self.assertFalse(martelo.is_loaded(rodada + 1))
        self.assertTrue(martelo.is_loaded(rodada + 2))

        # Fecha a rodada com as outras pecas so esperando e comeca a seguinte.
        while game.phase == "combat":
            pronta = next(iter(game.state()["legal_actions"]), None)
            if pronta is None:
                break
            self.act(game, pronta, "wait")
        game.command({"type": "next"})
        if game.phase == "recruit":
            game.command({"type": "begin"})

        acoes = game.state()["legal_actions"].get("Martelo 1", [])
        self.assertFalse(
            [a for a in acoes if a["action"] == "attack"],
            "martelo recarregando nao deveria oferecer golpe",
        )
        self.assertTrue([a for a in acoes if a["action"] in {"guard", "move", "wait"}])

    def test_pike_strikes_from_the_second_row_and_the_sword_does_not(self):
        """A lanca e o motivo de existir retaguarda ofensiva.

        So ha segunda fileira quando alguem ocupa a primeira: com o esquadrao
        inteiro atras, a retaguarda vira a propria linha de frente.
        """
        game = self.combat(
            [
                Guardian("Guardian 2", lane=Lane.FRONT),
                Pikeman("Pikeman 1", lane=Lane.BACK),
                Soldier("Soldier 1", lane=Lane.BACK),
            ],
            [Guardian("Guardian 1", lane=Lane.FRONT), Archer("Archer 2", lane=Lane.BACK)],
        )
        actions = game.state()["legal_actions"]
        self.assertIn({"action": "attack", "target": "Guardian 1"}, actions["Pikeman 1"])
        self.assertNotIn({"action": "attack", "target": "Guardian 1"}, actions["Soldier 1"])
        self.assertFalse(
            [a for a in actions["Soldier 1"] if a["action"] == "attack"],
            "espada guardada atras nao deveria ter alvo nenhum",
        )

    def test_exposed_backline_is_reachable_by_melee(self):
        game = self.combat([Soldier("Soldier 1")], [Archer("Archer 2")])
        self.act(game, "Soldier 1", "attack", target="Archer 2")
        attack = next(e for e in game.engine.events if e.event_type == "unit_attack")
        self.assertEqual(attack.target, "Archer 2")
        self.assertEqual(attack.amount, 2)

    def test_target_identity_survives_other_deaths(self):
        first, second = Soldier("Soldier 2"), Soldier("Soldier 3")
        first.health = 1
        game = self.combat([Archer("Archer 1"), Tank("Tank 1")], [first, second])
        self.act(game, "Archer 1", "attack", target="Soldier 2")
        self.act(game, "Tank 1", "attack", target="Soldier 3")
        attacks = [
            e
            for e in game.engine.events
            if e.player == Player.ONE and e.event_type == "unit_attack"
        ]
        self.assertEqual([e.target for e in attacks], ["Soldier 2", "Soldier 3"])

    def test_healing_is_an_explicit_action(self):
        ally = Guardian("Guardian 1")
        ally.health = 4
        game = self.combat([Medic("Medic 1"), ally], [])
        self.act(game, "Medic 1", "heal", target="Guardian 1")
        self.assertEqual(ally.health, 7)
        self.assertIn("Medic 1", game.acted)

    def test_triage_treats_a_bleeding_ally_at_full_health(self):
        ally = Soldier("Soldier 1")
        game = self.combat([Medic("Medic 1"), ally], [])
        # Atordoamento pendente e consumido no inicio do combate; o que a triagem
        # desfaz e o que cai durante a rodada, e tiraria a acao da proxima.
        ally.add_effect(StatusEffect.BLEED, 2)
        ally.add_effect(StatusEffect.STUN, 2)
        preview = next(p for p in game.state()["action_previews"]["Medic 1"] if p["action"] == "heal")
        self.assertEqual((preview["healing"], preview["cleanses"]), (0, ["bleed", "stun"]))

        self.act(game, "Medic 1", "heal", target="Soldier 1")

        self.assertEqual(ally.effects, {})
        heal = next(e for e in game.engine.events if e.event_type == "heal")
        self.assertEqual(heal.metadata["cleansed"], ["bleed", "stun"])

    def test_healthy_ally_without_wounds_is_not_a_triage_target(self):
        game = self.combat([Medic("Medic 1"), Soldier("Soldier 1")], [])
        self.assertNotIn({"action": "heal", "target": "Soldier 1"}, game.state()["legal_actions"]["Medic 1"])

    def test_guardian_can_protect_an_ally(self):
        ally = Soldier("Soldier 1")
        game = self.combat([Guardian("Guardian 1"), ally], [])
        self.act(game, "Guardian 1", "guard", target="Soldier 1")
        self.assertTrue(ally.has_effect(StatusEffect.SHIELD))

    def test_moving_consumes_action_and_cannot_act_twice(self):
        game = self.combat([Soldier("Soldier 1"), Soldier("Soldier 2")], [])
        self.act(game, "Soldier 1", "move", lane="back")
        self.assertEqual(game.field.troops_one[0].lane, Lane.BACK)
        with self.assertRaises(ValueError):
            self.act(game, "Soldier 1", "attack", target="base")

    def test_fort_is_not_a_target_while_the_enemy_vanguard_stands(self):
        game = self.combat([Tank("Tank 1")], [Soldier("Soldier 1")])
        with self.assertRaises(ValueError):
            self.act(game, "Tank 1", "attack", target="base")

    def test_broken_line_lets_the_vanguard_choose_the_fort(self):
        game = self.combat([Soldier("Soldier 1")], [Archer("Archer 2", lane=Lane.BACK)])
        legal = game.state()["legal_actions"]["Soldier 1"]
        self.assertIn({"action": "attack", "target": "base"}, legal)
        self.assertIn({"action": "attack", "target": "Archer 2"}, legal)
        self.assertTrue(game.state()["open_lines"]["player_two"])

        self.act(game, "Soldier 1", "attack", target="base")

        self.assertEqual(game.field.base_two.health, 26)
        strike = next(e for e in game.engine.events if e.event_type == "base_attack")
        self.assertTrue(strike.metadata["line_broken"])

    def test_rear_rank_cannot_use_the_breach(self):
        game = self.combat([Archer("Archer 1", lane=Lane.BACK)], [Archer("Archer 2", lane=Lane.BACK)])
        with self.assertRaises(ValueError):
            self.act(game, "Archer 1", "attack", target="base")

    def test_lethal_hit_previews_and_carries_overflow(self):
        soldier = Soldier("Soldier 2")
        soldier.current_hp = 1
        game = self.combat([Tank("Tank 1")], [soldier, Archer("Archer 3", lane=Lane.BACK)])
        preview = next(p for p in game.state()["action_previews"]["Tank 1"] if p.get("target") == "Soldier 2")
        self.assertEqual((preview["defeats"], preview["overflow"], preview["wins"]), (True, 3, False))

        self.act(game, "Tank 1", "attack", target="Soldier 2")

        self.assertEqual(game.field.base_two.health, 25)
        spill = next(e for e in game.engine.events if e.event_type == "base_attack")
        self.assertTrue(spill.metadata["overflow"])

    def test_overflow_that_finishes_the_fort_is_previewed_as_a_win(self):
        soldier = Soldier("Soldier 2")
        soldier.current_hp = 1
        game = self.combat([Tank("Tank 1")], [soldier])
        game.field.base_two.health = 2
        preview = next(p for p in game.state()["action_previews"]["Tank 1"] if p.get("target") == "Soldier 2")
        self.assertEqual((preview["overflow"], preview["wins"]), (2, True))

        self.act(game, "Tank 1", "attack", target="Soldier 2")

        self.assertEqual(game.phase, "finished")
        self.assertEqual(game.winner, Player.ONE)

    def test_rival_breaks_through_an_empty_player_vanguard(self):
        game = self.combat([Archer("Archer 1", lane=Lane.BACK)], [Soldier("Soldier 2")])
        if "Archer 1" in game.state()["legal_actions"]:
            self.act(game, "Archer 1", "wait")

        self.assertTrue(game.state()["open_lines"]["player_one"])
        self.assertEqual(game.field.base_one.health, 26)

    def test_stun_consumes_pending_action_once(self):
        enemy = Guardian("Guardian 2")
        game = self.combat([Tank("Tank 1"), Soldier("Soldier 1")], [enemy])
        self.act(game, "Tank 1", "attack", target=enemy.name)
        self.assertIn(enemy.name, game.acted)
        self.assertFalse(enemy.has_effect(StatusEffect.STUN))
        self.assertFalse(
            any(
                e.event_type == "unit_attack" and e.player == Player.TWO for e in game.engine.events
            )
        )

    def test_stun_on_spent_unit_consumes_next_round_action(self):
        enemy = Guardian("Guardian 2")
        game = self.combat([Tank("Tank 1"), Guardian("Guardian 1")], [enemy])
        self.act(game, "Guardian 1", "wait")
        self.act(game, "Tank 1", "attack", target=enemy.name)
        self.assertTrue(enemy.has_effect(StatusEffect.STUN))
        game.command({"type": "next"})
        game.field.base_two.resources = 0
        game.command({"type": "begin"})
        self.assertIn(enemy.name, game.acted)
        self.assertFalse(enemy.has_effect(StatusEffect.STUN))

    def test_bleed_ticks_only_on_next_round_and_can_kill(self):
        ally = Soldier("Soldier 1")
        ally.health = 1
        game = self.combat([ally], [])
        ally.add_effect(StatusEffect.BLEED, 3)
        self.act(game, ally.name, "wait")
        self.assertEqual(ally.health, 1)
        game.command({"type": "next"})
        self.assertEqual(game.field.troops_one, [])

    def test_round_review_waits_and_income_is_paid_once(self):
        game = self.combat([Soldier("Soldier 1")], [])
        self.act(game, "Soldier 1", "wait")
        self.assertEqual(game.phase, "review")
        self.assertEqual(game.field.base_one.resources, 16)
        with self.assertRaises(ValueError):
            game.command({"type": "begin"})
        game.command({"type": "next"})
        self.assertEqual(game.engine.round_number, 2)
        self.assertEqual(game.field.base_one.resources, 16)

    def test_empty_armies_end_round_without_loop(self):
        game = self.combat([], [])
        self.assertEqual(game.phase, "review")

    def test_remaining_enemy_actions_finish_when_player_is_done(self):
        game = self.combat([], [Soldier("Soldier 1"), Soldier("Soldier 2")])
        self.assertEqual(game.phase, "review")
        self.assertEqual(game.field.base_one.health, 24)

    def test_seed_and_round_alternate_opening_side(self):
        game = TacticalSession(seed=11)
        self.assertEqual(game.opener, Player.TWO)
        game.field.base_two.resources = 0
        game.command({"type": "begin"})
        game.command({"type": "next"})
        self.assertEqual(game.opener, Player.ONE)

    def test_destroyed_base_finishes_immediately_and_locks_commands(self):
        game = self.combat([Tank("Tank 1")], [])
        game.field.base_two.health = 3
        self.act(game, "Tank 1", "attack", target="base")
        self.assertEqual(game.phase, "finished")
        self.assertEqual(game.winner, Player.ONE)
        self.assertEqual(game.reason, "base_destroyed")
        with self.assertRaises(ValueError):
            game.command({"type": "next"})

    def test_round_limit_tiebreak_and_draw(self):
        game = self.combat([Tank("Tank 1")], [], rounds=1)
        self.act(game, "Tank 1", "attack", target="base")
        self.assertEqual(game.winner, Player.ONE)
        self.assertEqual(game.reason, "round_limit")
        draw = self.combat([], [], rounds=1)
        self.assertEqual(draw.phase, "finished")
        self.assertIsNone(draw.winner)

    def test_commands_reproduce_complete_game(self):
        for opponent in ("balanced", "random", "economy"):
            game = TacticalSession(opponent=opponent, seed=5, max_rounds=4)
            while game.phase != "finished":
                if game.phase == "recruit":
                    if game.field.base_one.resources >= 3 and len(game.field.troops_one) < 8:
                        game.command({"type": "recruit", "kind": "archer", "lane": "back"})
                    else:
                        game.command({"type": "begin"})
                elif game.phase == "review":
                    game.command({"type": "next"})
                else:
                    actor, choices = next(iter(game.state()["legal_actions"].items()))
                    game.command({"type": "act", "actor": actor, **choices[0]})
            report = json.loads(json.dumps(game.report()))
            replay = TacticalSession(**report["config"])
            for command in report["commands"]:
                replay.command(command)
            self.assertEqual(replay.report(), report)

    def test_bridge_returns_json_and_new_game_resets_session(self):
        state = json.loads(playground.new_game("balanced", 11, 20))
        self.assertEqual(state["phase"], "recruit")
        playground.game_command('{"type":"recruit","kind":"soldier","lane":"front"}')
        self.assertEqual(len(json.loads(playground.game_report())["commands"]), 1)
        playground.new_game("economy", 0, 2)
        self.assertEqual(json.loads(playground.game_report())["commands"], [])

    def test_invalid_config(self):
        for config in (
            {"opponent": "bad"},
            {"seed": -1},
            {"seed": True},
            {"max_rounds": 0},
            {"max_rounds": 51},
        ):
            with self.assertRaises(ValueError):
                TacticalSession(**config)


if __name__ == "__main__":
    unittest.main()
