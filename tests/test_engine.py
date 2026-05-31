import unittest

from battle_simulator.cli import _build_report
from battle_simulator.engine import AttackOrder, BattleEngine, Battlefield, Player, RecruitOrder, TurnPlan
from battle_simulator.models import (
    Archer,
    Base,
    Guardian,
    Lane,
    Medic,
    Soldier,
    StatusEffect,
    Tank,
    TroopFactory,
    TroopKind,
)
from battle_simulator.strategies import AggressiveBot, BalancedBot, DefensiveBot
from battle_simulator.tournament import run_matchup, run_tournament


class BaseTest(unittest.TestCase):
    def test_receive_damage_never_goes_below_zero(self):
        base = Base("Blue", health=3)

        applied = base.receive_damage(10)

        self.assertEqual(applied, 3)
        self.assertEqual(base.health, 0)
        self.assertTrue(base.is_destroyed)


class TroopTest(unittest.TestCase):
    def test_factory_creates_tactical_troops(self):
        factory = TroopFactory()

        archer = factory.create(TroopKind.ARCHER)
        guardian = factory.create(TroopKind.GUARDIAN)
        medic = factory.create(TroopKind.MEDIC)

        self.assertIsInstance(archer, Archer)
        self.assertEqual(archer.attack, 3)
        self.assertEqual(archer.range, 2)
        self.assertEqual(archer.lane, Lane.BACK)
        self.assertIsInstance(guardian, Guardian)
        self.assertEqual(guardian.defense, 3)
        self.assertEqual(guardian.cost, 4)
        self.assertIsInstance(medic, Medic)
        self.assertEqual(medic.role.value, "support")

    def test_defense_reduces_damage_with_minimum_one(self):
        soldier = Soldier("Soldier")
        guardian = Guardian("Guardian")

        applied = soldier.attack_troop(guardian)

        self.assertEqual(applied, 1)
        self.assertEqual(guardian.health, guardian.max_hp - 1)

    def test_range_controls_target_access(self):
        soldier = Soldier("Soldier", lane=Lane.FRONT)
        archer = Archer("Archer", lane=Lane.BACK)

        self.assertFalse(soldier.can_reach(archer))
        self.assertTrue(archer.can_reach(soldier))

    def test_shield_reduces_next_damage(self):
        guardian = Guardian("Guardian")
        guardian.add_effect(StatusEffect.SHIELD, duration=1)

        applied = Tank("Tank").attack_troop(guardian)

        self.assertEqual(applied, 0)


class BattleEngineTest(unittest.TestCase):
    def test_recruitment_spends_resources_and_adds_troop(self):
        engine = BattleEngine()

        engine.play_round(
            {
                Player.ONE: TurnPlan(recruits=(RecruitOrder(TroopKind.TANK),)),
                Player.TWO: TurnPlan(),
            }
        )

        self.assertEqual(len(engine.battlefield.troops_one), 1)
        self.assertEqual(engine.battlefield.base_one.resources, 12)
        self.assertEqual(engine.stats.units_recruited[Player.ONE], 1)

    def test_recruitment_cost_uses_selected_troop(self):
        engine = BattleEngine()

        engine.play_round(
            {
                Player.ONE: TurnPlan(recruits=(RecruitOrder(TroopKind.ARCHER),)),
                Player.TWO: TurnPlan(),
            }
        )

        self.assertEqual(engine.battlefield.base_one.resources, 14)
        self.assertIsInstance(engine.battlefield.troops_one[0], Archer)

    def test_insufficient_resources_does_not_add_troop(self):
        battlefield = Battlefield(base_one=Base("Blue", resources=1))
        engine = BattleEngine(battlefield)

        events = engine.play_round(
            {
                Player.ONE: TurnPlan(recruits=(RecruitOrder(TroopKind.SOLDIER),)),
                Player.TWO: TurnPlan(),
            }
        )

        self.assertEqual(engine.battlefield.troops_one, [])
        self.assertTrue(any("does not have enough resources" in event.message for event in events))

    def test_out_of_range_attack_does_not_damage_backline(self):
        battlefield = Battlefield(
            troops_one=[Soldier("Soldier", lane=Lane.FRONT)],
            troops_two=[Archer("Archer", lane=Lane.BACK)],
        )
        engine = BattleEngine(battlefield)

        events = engine.play_round(
            {
                Player.ONE: TurnPlan(attacks=(AttackOrder(attacker_index=0, target_index=0),)),
                Player.TWO: TurnPlan(),
            }
        )

        self.assertEqual(engine.battlefield.troops_two[0].health, 3)
        self.assertTrue(any(event.event_type == "out_of_range" for event in events))

    def test_archer_applies_bleed_effect(self):
        battlefield = Battlefield(
            troops_one=[Archer("Archer", lane=Lane.BACK)],
            troops_two=[Guardian("Guardian", lane=Lane.FRONT)],
        )
        engine = BattleEngine(battlefield)

        engine.play_round(
            {
                Player.ONE: TurnPlan(attacks=(AttackOrder(attacker_index=0, target_index=0),)),
                Player.TWO: TurnPlan(),
            }
        )
        events = engine.play_round({Player.ONE: TurnPlan(), Player.TWO: TurnPlan()})

        self.assertTrue(any(event.event_type == "effect_damage" for event in events))

    def test_medic_heals_damaged_ally(self):
        soldier = Soldier("Soldier")
        soldier.receive_damage(3, ignore_defense=True)
        battlefield = Battlefield(troops_one=[Medic("Medic"), soldier])
        engine = BattleEngine(battlefield)

        events = engine.play_round(
            {
                Player.ONE: TurnPlan(attacks=(AttackOrder(attacker_index=0),)),
                Player.TWO: TurnPlan(),
            }
        )

        self.assertGreater(soldier.health, 2)
        self.assertTrue(any(event.event_type == "heal" for event in events))

    def test_tank_stuns_target_next_action(self):
        battlefield = Battlefield(
            troops_one=[Tank("Tank")],
            troops_two=[Soldier("Soldier")],
        )
        engine = BattleEngine(battlefield)

        engine.play_round(
            {
                Player.ONE: TurnPlan(attacks=(AttackOrder(attacker_index=0),)),
                Player.TWO: TurnPlan(),
            }
        )
        events = engine.play_round(
            {
                Player.ONE: TurnPlan(),
                Player.TWO: TurnPlan(attacks=(AttackOrder(attacker_index=0),)),
            }
        )

        self.assertTrue(any(event.event_type == "unit_stunned" for event in events))

    def test_remove_defeated_troops(self):
        battlefield = Battlefield(
            troops_one=[Archer("Archer")],
            troops_two=[Tank("Tank")],
        )
        battlefield.troops_one[0].receive_damage(99, ignore_defense=True)

        events = battlefield.remove_defeated()

        self.assertEqual(battlefield.troops_one, [])
        self.assertEqual(len(battlefield.troops_two), 1)
        self.assertEqual(events[0].event_type, "unit_defeated")

    def test_invalid_target_index_is_reported(self):
        battlefield = Battlefield(
            troops_one=[Archer("Archer")],
            troops_two=[Guardian("Guardian")],
        )
        engine = BattleEngine(battlefield)

        events = engine.play_round(
            {
                Player.ONE: TurnPlan(attacks=(AttackOrder(attacker_index=0, target_index=10),)),
                Player.TWO: TurnPlan(),
            }
        )

        self.assertEqual(engine.battlefield.troops_two[0].health, 11)
        self.assertTrue(any(event.event_type == "invalid_target" for event in events))

    def test_troops_attack_enemy_base_when_no_defenders_exist(self):
        battlefield = Battlefield(
            base_two=Base("Red", health=4),
            troops_one=[Tank("Tank")],
        )
        engine = BattleEngine(battlefield)

        engine.play_round(
            {
                Player.ONE: TurnPlan(attacks=(AttackOrder(attacker_index=0),)),
                Player.TWO: TurnPlan(),
            }
        )

        self.assertEqual(engine.battlefield.winner(), Player.ONE)
        self.assertEqual(engine.battlefield.base_two.health, 0)

    def test_report_contains_structured_battle_state(self):
        engine = BattleEngine()
        result = engine.run(BalancedBot(), DefensiveBot(), max_rounds=2)

        report = _build_report(engine, result)

        self.assertIn("strategies", report)
        self.assertIn("damage", report)
        self.assertIn("events", report)
        self.assertEqual(report["rounds_played"], result.rounds_played)


class StrategyTest(unittest.TestCase):
    def test_aggressive_bot_prefers_attack_units(self):
        battlefield = Battlefield(base_one=Base("Blue", resources=10))

        plan = AggressiveBot().choose_plan(Player.ONE, battlefield)

        self.assertEqual(plan.recruits[0].troop_kind, TroopKind.TANK)

    def test_defensive_bot_recruits_guardian_first(self):
        battlefield = Battlefield(base_one=Base("Blue", resources=10))

        plan = DefensiveBot().choose_plan(Player.ONE, battlefield)

        self.assertEqual(plan.recruits[0].troop_kind, TroopKind.GUARDIAN)


class TournamentTest(unittest.TestCase):
    def test_tournament_uses_round_robin_matchups(self):
        summary = run_tournament(simulations=2, max_rounds=4, seed=10)

        self.assertEqual(len(summary.matchups), 6)
        self.assertEqual(summary.simulations, 12)
        self.assertEqual(len(summary.standings), 4)

    def test_matchup_reports_wins_losses_draws_and_damage(self):
        summary = run_matchup("aggressive", "balanced", simulations=2, max_rounds=3, seed=2)

        total_outcomes = summary.strategy_one_wins + summary.strategy_two_wins + summary.draws
        self.assertEqual(total_outcomes, 2)
        self.assertEqual(summary.losses_for_strategy_one, summary.strategy_two_wins)
        self.assertLessEqual(summary.average_rounds, 3)
        self.assertGreaterEqual(summary.strategy_one_damage_dealt, 0)


if __name__ == "__main__":
    unittest.main()
