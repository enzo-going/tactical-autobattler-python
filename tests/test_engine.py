import unittest

from battle_simulator.cli import _build_report
from battle_simulator.engine import BattleEngine, Player, RecruitOrder, TurnPlan
from battle_simulator.models import Base, TroopKind
from battle_simulator.strategies import BalancedBot


class BaseTest(unittest.TestCase):
    def test_receive_damage_never_goes_below_zero(self):
        base = Base("Blue", health=3)

        base.receive_damage(10)

        self.assertEqual(base.health, 0)
        self.assertTrue(base.is_destroyed)


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


if __name__ == "__main__":
    unittest.main()
