import unittest

from battle_simulator.cli import _build_report
from battle_simulator.engine import AttackOrder, BattleEngine, Battlefield, Player, RecruitOrder, TurnPlan
from battle_simulator.models import Archer, Base, Guardian, Tank, TroopFactory, TroopKind
from battle_simulator.strategies import AggressiveBot, BalancedBot
from battle_simulator.tournament import run_matchup, run_tournament


class BaseTest(unittest.TestCase):
    def test_receive_damage_never_goes_below_zero(self):
        base = Base("Blue", health=3)

        base.receive_damage(10)

        self.assertEqual(base.health, 0)
        self.assertTrue(base.is_destroyed)


class TroopTest(unittest.TestCase):
    def test_factory_creates_new_troop_types(self):
        factory = TroopFactory()

        archer = factory.create(TroopKind.ARCHER)
        guardian = factory.create(TroopKind.GUARDIAN)

        self.assertIsInstance(archer, Archer)
        self.assertEqual(archer.health, 2)
        self.assertEqual(archer.damage, 2)
        self.assertEqual(archer.cost, 3)
        self.assertIsInstance(guardian, Guardian)
        self.assertEqual(guardian.health, 10)
        self.assertEqual(guardian.damage, 1)
        self.assertEqual(guardian.cost, 4)

    def test_troop_damage_is_applied_to_target(self):
        archer = Archer("Archer")
        target = Guardian("Guardian")

        archer.attack_troop(target)

        self.assertEqual(target.health, 8)


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

    def test_troops_attack_enemy_base_when_no_defenders_exist(self):
        engine = BattleEngine()
        engine.play_round(
            {
                Player.ONE: TurnPlan(recruits=(RecruitOrder(TroopKind.TANK),)),
                Player.TWO: TurnPlan(),
            }
        )

        engine.play_round({Player.ONE: BalancedBot().choose_plan(Player.ONE, engine.battlefield)})

        self.assertLess(engine.battlefield.base_two.health, 30)

    def test_remove_defeated_troops(self):
        battlefield = Battlefield(
            troops_one=[Archer("Archer")],
            troops_two=[Tank("Tank")],
        )
        battlefield.troops_one[0].receive_damage(99)

        events = battlefield.remove_defeated()

        self.assertEqual(battlefield.troops_one, [])
        self.assertEqual(len(battlefield.troops_two), 1)
        self.assertEqual(events[0].message, "Archer was defeated.")

    def test_invalid_target_index_does_not_apply_damage(self):
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

        self.assertEqual(engine.battlefield.troops_two[0].health, 10)
        self.assertTrue(any("Invalid target index" in event.message for event in events))

    def test_simulation_finishes_within_round_limit(self):
        engine = BattleEngine()

        result = engine.run(BalancedBot(), BalancedBot(), max_rounds=5)

        self.assertLessEqual(result.rounds_played, 5)

    def test_report_contains_final_state(self):
        engine = BattleEngine()
        result = engine.run(BalancedBot(), BalancedBot(), max_rounds=2)

        report = _build_report(engine, result)

        self.assertIn("bases", report)
        self.assertIn("troops_remaining", report)
        self.assertEqual(report["rounds_played"], result.rounds_played)


class TournamentTest(unittest.TestCase):
    def test_tournament_aggregates_all_simulations(self):
        summary = run_tournament(simulations=3, max_rounds=4, seed=10)

        self.assertEqual(len(summary.matchups), 3)
        self.assertEqual(summary.simulations, 9)

    def test_matchup_reports_wins_losses_draws_and_rounds(self):
        summary = run_matchup("aggressive", "balanced", simulations=2, max_rounds=3, seed=2)

        total_outcomes = summary.strategy_one_wins + summary.strategy_two_wins + summary.draws
        self.assertEqual(total_outcomes, 2)
        self.assertEqual(summary.losses_for_strategy_one, summary.strategy_two_wins)
        self.assertLessEqual(summary.average_rounds, 3)

    def test_aggressive_bot_prefers_attack_units(self):
        battlefield = Battlefield(base_one=Base("Blue", resources=10))

        plan = AggressiveBot().choose_plan(Player.ONE, battlefield)

        self.assertEqual(plan.recruits[0].troop_kind, TroopKind.TANK)


if __name__ == "__main__":
    unittest.main()
