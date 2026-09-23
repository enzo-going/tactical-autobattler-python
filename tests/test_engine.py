import unittest
from contextlib import redirect_stdout
from io import StringIO

from battle_simulator.cli import _build_report, _parse_seeds, _parse_strategies, main
from battle_simulator.engine import AttackOrder, BattleEngine, Battlefield, Player, RecruitOrder, TurnPlan
from battle_simulator.models import (
    Archer,
    Base,
    Guardian,
    Lane,
    Pikeman,
    Medic,
    Role,
    Soldier,
    StatusEffect,
    Tank,
    Troop,
    TroopFactory,
    can_assault_base,
    can_strike,
    needs_triage,
    triage,
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
        self.assertEqual(guardian.defense, 2)
        self.assertEqual(guardian.cost, 4)
        self.assertIsInstance(medic, Medic)
        self.assertEqual(medic.role.value, "support")

    def test_defense_reduces_damage_with_minimum_one(self):
        soldier = Soldier("Soldier")
        guardian = Guardian("Guardian")

        applied = soldier.attack_troop(guardian)

        self.assertEqual(applied, 1)
        self.assertEqual(guardian.health, guardian.max_hp - 1)

    def test_reach_counts_rows_from_the_attacker_lane(self):
        """Alcance conta a partir de onde a tropa esta, nao so de onde o alvo esta."""
        alvo = Soldier("Alvo", lane=Lane.FRONT)
        deles = [alvo, Archer("Retaguarda deles", lane=Lane.BACK)]

        espada_na_frente = Soldier("Espada", lane=Lane.FRONT)
        espada_no_fundo = Soldier("Espada atras", lane=Lane.BACK)
        lanca_no_fundo = Pikeman("Lanca", lane=Lane.BACK)
        meus = [espada_na_frente, espada_no_fundo, lanca_no_fundo]

        self.assertTrue(can_strike(espada_na_frente, meus, alvo, deles))
        self.assertFalse(can_strike(espada_no_fundo, meus, alvo, deles))
        self.assertTrue(can_strike(lanca_no_fundo, meus, alvo, deles))

    def test_rear_rank_steps_up_when_the_front_falls(self):
        """Sem ninguem na frente, quem esta atras vira a linha de frente."""
        sozinho_atras = Archer("Sozinho", lane=Lane.BACK)
        espada = Soldier("Espada", lane=Lane.FRONT)

        self.assertTrue(can_strike(espada, [espada], sozinho_atras, [sozinho_atras]))
        acompanhado = [Guardian("Escudo", lane=Lane.FRONT), sozinho_atras]
        self.assertFalse(can_strike(espada, [espada], sozinho_atras, acompanhado))

    def test_overflow_is_what_a_lethal_hit_leaves_after_the_troop(self):
        soldier = Soldier("Soldier", lane=Lane.FRONT)
        soldier.current_hp = 1

        self.assertEqual(soldier.overflow_damage(5), 3)
        self.assertEqual(soldier.overflow_damage(2), 0)
        soldier.add_effect(StatusEffect.SHIELD, 1)
        self.assertEqual(soldier.overflow_damage(5), 2)
        soldier.current_hp = 4
        self.assertEqual(soldier.overflow_damage(5), 0)

    def test_only_the_vanguard_uses_a_broken_line(self):
        front = Soldier("Soldier", lane=Lane.FRONT)
        rear = Archer("Archer", lane=Lane.BACK)

        self.assertFalse(can_assault_base(front, [Guardian("Guardian", lane=Lane.FRONT)]))
        self.assertTrue(can_assault_base(front, [Archer("Enemy", lane=Lane.BACK)]))
        self.assertFalse(can_assault_base(rear, [Archer("Enemy", lane=Lane.BACK)]))
        self.assertTrue(can_assault_base(rear, []))
        fallen = Guardian("Fallen", lane=Lane.FRONT)
        fallen.current_hp = 0
        self.assertTrue(can_assault_base(front, [fallen, Archer("Enemy", lane=Lane.BACK)]))

    def test_triage_heals_three_and_clears_bleed_and_stun(self):
        soldier = Soldier("Soldier")
        soldier.current_hp = 1
        soldier.add_effect(StatusEffect.BLEED, 3)
        soldier.add_effect(StatusEffect.STUN, 1)
        soldier.add_effect(StatusEffect.SHIELD, 2)

        healed, cleansed = triage(soldier)

        self.assertEqual((healed, soldier.health), (3, 4))
        self.assertEqual(cleansed, [StatusEffect.BLEED, StatusEffect.STUN])
        self.assertEqual(set(soldier.effects), {StatusEffect.SHIELD})

    def test_triage_targets_wounds_bleed_and_stun_but_not_a_shield(self):
        healthy = Soldier("Soldier")
        self.assertFalse(needs_triage(healthy))
        healthy.add_effect(StatusEffect.SHIELD, 2)
        self.assertFalse(needs_triage(healthy))
        healthy.add_effect(StatusEffect.BLEED, 2)
        self.assertTrue(needs_triage(healthy))

    def test_shield_reduces_next_damage(self):
        guardian = Guardian("Guardian")
        guardian.add_effect(StatusEffect.SHIELD, duration=1)

        applied = Tank("Tank").attack_troop(guardian)

        self.assertEqual(applied, 2)


class BattleEngineTest(unittest.TestCase):
    def test_casualty_does_not_transfer_its_initiative_to_a_survivor(self):
        fast = Troop("Fast", 20, 2, 0, 5, 2, 0, Role.ASSAULT)
        middle = Troop("Middle", 20, 2, 0, 2, 2, 0, Role.ASSAULT)
        fallen = Troop("Fallen", 1, 2, 0, 4, 2, 0, Role.ASSAULT)
        slow = Troop("Slow", 20, 2, 0, 1, 2, 0, Role.ASSAULT)
        engine = BattleEngine(Battlefield(troops_one=[fast, middle], troops_two=[fallen, slow]))
        events = engine.play_round({
            player: TurnPlan(attacks=(AttackOrder(0), AttackOrder(1))) for player in Player
        })
        self.assertEqual(
            [e.actor for e in events if e.event_type == "unit_attack"],
            ["Fast", "Middle", "Slow"],
        )

    def test_target_identity_survives_an_earlier_casualty(self):
        first, second, third = [Soldier(name) for name in ("First", "Second", "Third")]
        first.health = 1
        engine = BattleEngine(Battlefield(
            troops_one=[Archer("Archer"), Soldier("Soldier")],
            troops_two=[first, second, third],
        ))
        events = engine.play_round({Player.ONE: TurnPlan(attacks=(AttackOrder(0, 0), AttackOrder(1, 1)))})
        self.assertEqual([e.target for e in events if e.event_type == "unit_attack"], ["First", "Second"])

    def test_bleeding_casualty_does_not_give_its_order_to_an_unordered_unit(self):
        fallen, survivor = Soldier("Fallen"), Soldier("Survivor")
        fallen.health = 1
        fallen.add_effect(StatusEffect.BLEED, 3)
        engine = BattleEngine(Battlefield(troops_one=[fallen, survivor]))
        events = engine.play_round({Player.ONE: TurnPlan(attacks=(AttackOrder(0),))})
        self.assertFalse([e for e in events if e.event_type == "base_attack"])

    def test_equal_speed_actions_interleave_and_priority_flips_each_round(self):
        def durable_troop(name: str) -> Troop:
            return Troop(name, 100, 1, 0, 2, 1, 0, Role.ASSAULT)

        battlefield = Battlefield(
            troops_one=[durable_troop("Blue 1"), durable_troop("Blue 2")],
            troops_two=[durable_troop("Red 1"), durable_troop("Red 2")],
        )
        engine = BattleEngine(battlefield, initiative_seed=0)
        plans = {
            player: TurnPlan(attacks=(AttackOrder(0), AttackOrder(1)))
            for player in Player
        }

        first_round = engine.play_round(plans)
        second_round = engine.play_round(plans)

        first_order = [event.player for event in first_round if event.event_type == "unit_attack"]
        second_order = [event.player for event in second_round if event.event_type == "unit_attack"]
        self.assertEqual(first_order, [Player.ONE, Player.TWO, Player.ONE, Player.TWO])
        self.assertEqual(second_order, [Player.TWO, Player.ONE, Player.TWO, Player.ONE])

    def test_seed_changes_opening_initiative_without_changing_speed_priority(self):
        plan = {
            Player.ONE: TurnPlan(attacks=(AttackOrder(0),)),
            Player.TWO: TurnPlan(attacks=(AttackOrder(0),)),
        }

        even_engine = BattleEngine(
            Battlefield(troops_one=[Guardian("Blue")], troops_two=[Guardian("Red")]),
            initiative_seed=2,
        )
        odd_engine = BattleEngine(
            Battlefield(troops_one=[Guardian("Blue")], troops_two=[Guardian("Red")]),
            initiative_seed=3,
        )

        even_events = even_engine.play_round(plan)
        odd_events = odd_engine.play_round(plan)
        even_first = next(event.player for event in even_events if event.event_type == "unit_attack")
        odd_first = next(event.player for event in odd_events if event.event_type == "unit_attack")
        self.assertEqual(even_first, Player.ONE)
        self.assertEqual(odd_first, Player.TWO)

        speed_engine = BattleEngine(
            Battlefield(troops_one=[Guardian("Blue")], troops_two=[Archer("Red")]),
            initiative_seed=2,
        )
        speed_events = speed_engine.play_round(plan)
        speed_first = next(event.player for event in speed_events if event.event_type == "unit_attack")
        self.assertEqual(speed_first, Player.TWO)

    def test_recruitment_spends_resources_and_adds_troop(self):
        engine = BattleEngine()

        engine.play_round(
            {
                Player.ONE: TurnPlan(recruits=(RecruitOrder(TroopKind.TANK),)),
                Player.TWO: TurnPlan(),
            }
        )

        self.assertEqual(len(engine.battlefield.troops_one), 1)
        self.assertEqual(engine.battlefield.base_one.resources, 11)
        self.assertEqual(engine.stats.units_recruited[Player.ONE], 1)

    def test_recruitment_cost_uses_selected_troop(self):
        engine = BattleEngine()

        engine.play_round(
            {
                Player.ONE: TurnPlan(recruits=(RecruitOrder(TroopKind.ARCHER),)),
                Player.TWO: TurnPlan(),
            }
        )

        self.assertEqual(engine.battlefield.base_one.resources, 13)
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
        """Com a frente inimiga de pe, a espada nao alcanca a retaguarda."""
        battlefield = Battlefield(
            troops_one=[Soldier("Soldier", lane=Lane.FRONT)],
            troops_two=[Guardian("Guardian", lane=Lane.FRONT), Archer("Archer", lane=Lane.BACK)],
        )
        engine = BattleEngine(battlefield)

        events = engine.play_round(
            {
                Player.ONE: TurnPlan(attacks=(AttackOrder(attacker_index=0, target_index=1),)),
                Player.TWO: TurnPlan(),
            }
        )

        self.assertEqual(engine.battlefield.troops_two[1].health, 3)
        self.assertTrue(any(event.event_type == "out_of_range" for event in events))

    def test_heavy_weapon_waits_its_reload_before_striking_again(self):
        """Martelo de recarga 1 golpeia, espera uma rodada e volta a golpear."""
        martelo = Tank("Martelo", lane=Lane.FRONT)
        alvo = Guardian("Alvo", lane=Lane.FRONT)
        alvo.max_hp = 99
        alvo.current_hp = 99
        battlefield = Battlefield(troops_one=[martelo], troops_two=[alvo])
        engine = BattleEngine(battlefield)

        tipos = []
        for _ in range(4):
            eventos = engine.play_round(
                {
                    Player.ONE: TurnPlan(attacks=(AttackOrder(attacker_index=0, target_index=0),)),
                    Player.TWO: TurnPlan(),
                }
            )
            tipos.append(
                [e.event_type for e in eventos if e.actor == "Martelo" and e.event_type in
                 {"unit_attack", "reloading"}]
            )

        self.assertEqual(
            [t[0] for t in tipos],
            ["unit_attack", "reloading", "unit_attack", "reloading"],
        )

    def test_light_weapon_strikes_every_round(self):
        """Recarga 0 e golpe a cada rodada: a espada nao espera."""
        espada = Soldier("Espada", lane=Lane.FRONT)
        alvo = Guardian("Alvo", lane=Lane.FRONT)
        alvo.max_hp = 99
        alvo.current_hp = 99
        engine = BattleEngine(Battlefield(troops_one=[espada], troops_two=[alvo]))

        golpes = 0
        for _ in range(3):
            eventos = engine.play_round(
                {
                    Player.ONE: TurnPlan(attacks=(AttackOrder(attacker_index=0, target_index=0),)),
                    Player.TWO: TurnPlan(),
                }
            )
            golpes += sum(
                1 for e in eventos if e.actor == "Espada" and e.event_type == "unit_attack"
            )
        self.assertEqual(golpes, 3)

    def test_troop_without_reach_advances_instead_of_wasting_the_round(self):
        """O modo automatico nao tem ordem de mover: quem nao alcanca, avanca."""
        atrasado = Soldier("Atrasado", lane=Lane.BACK)
        battlefield = Battlefield(
            troops_one=[Guardian("Escudo", lane=Lane.FRONT), atrasado],
            troops_two=[Soldier("Inimigo", lane=Lane.FRONT)],
        )
        engine = BattleEngine(battlefield)

        events = engine.play_round(
            {
                Player.ONE: TurnPlan(attacks=(AttackOrder(attacker_index=1, target_index=0),)),
                Player.TWO: TurnPlan(),
            }
        )

        self.assertEqual(atrasado.lane, Lane.FRONT)
        self.assertTrue(
            any(
                event.event_type == "unit_moved" and event.actor == "Atrasado"
                for event in events
            )
        )

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

    def test_medic_treats_every_round_without_reload(self):
        # Vida 2: o sangramento tira 1 no inicio da rodada, antes da triagem.
        soldier = Soldier("Soldier")
        soldier.current_hp = 2
        soldier.add_effect(StatusEffect.BLEED, 3)
        engine = BattleEngine(Battlefield(troops_one=[Medic("Medic"), soldier]))
        plan = {Player.ONE: TurnPlan(attacks=(AttackOrder(attacker_index=0),)), Player.TWO: TurnPlan()}

        first = engine.play_round(plan)
        soldier.current_hp = 2
        second = engine.play_round(plan)

        heals = [event for event in first + second if event.event_type == "heal"]
        self.assertEqual(len(heals), 2)
        self.assertEqual(heals[0].metadata["cleansed"], ["bleed"])
        self.assertFalse(any(event.event_type == "reloading" for event in second))

    def test_tank_stuns_target_next_action(self):
        battlefield = Battlefield(
            troops_one=[Tank("Tank")],
            troops_two=[Guardian("Guardian")],
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

        self.assertEqual(engine.battlefield.troops_two[0].health, 9)
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

    def test_vanguard_strikes_the_fort_when_the_enemy_front_is_empty(self):
        """Sem vanguarda inimiga, a espada passa pela brecha e o arqueiro fica."""
        battlefield = Battlefield(
            troops_one=[Soldier("Soldier", lane=Lane.FRONT)],
            troops_two=[Archer("Archer", lane=Lane.BACK)],
        )
        engine = BattleEngine(battlefield)

        events = engine.play_round(
            {Player.ONE: TurnPlan(attacks=(AttackOrder(attacker_index=0, target_index=0),)), Player.TWO: TurnPlan()}
        )

        self.assertEqual(engine.battlefield.base_two.health, 26)
        self.assertEqual(engine.battlefield.troops_two[0].health, 3)
        strike = next(event for event in events if event.event_type == "base_attack")
        self.assertTrue(strike.metadata["line_broken"])

    def test_rear_rank_keeps_fighting_the_enemy_rear(self):
        battlefield = Battlefield(
            troops_one=[Archer("Archer One", lane=Lane.BACK)],
            troops_two=[Archer("Archer Two", lane=Lane.BACK)],
        )
        engine = BattleEngine(battlefield)

        engine.play_round({Player.ONE: TurnPlan(attacks=(AttackOrder(attacker_index=0),)), Player.TWO: TurnPlan()})

        self.assertEqual(engine.battlefield.base_two.health, 28)
        self.assertEqual(engine.battlefield.troops_two, [])

    def test_lethal_hit_carries_its_overflow_onto_the_fort(self):
        soldier = Soldier("Soldier", lane=Lane.FRONT)
        soldier.current_hp = 1
        battlefield = Battlefield(troops_one=[Tank("Tank")], troops_two=[soldier, Archer("Archer")])
        engine = BattleEngine(battlefield)

        events = engine.play_round({Player.ONE: TurnPlan(attacks=(AttackOrder(attacker_index=0, target_index=0),)), Player.TWO: TurnPlan()})

        self.assertEqual(engine.battlefield.base_two.health, 25)
        spill = next(event for event in events if event.event_type == "base_attack")
        self.assertEqual((spill.actor, spill.amount, spill.metadata["overflow"]), ("Tank", 3, True))
        self.assertEqual(engine.stats.damage_dealt[Player.ONE], 4)

    def test_non_lethal_hit_does_not_reach_the_fort(self):
        battlefield = Battlefield(troops_one=[Tank("Tank")], troops_two=[Guardian("Guardian")])
        engine = BattleEngine(battlefield)

        events = engine.play_round({Player.ONE: TurnPlan(attacks=(AttackOrder(attacker_index=0),)), Player.TWO: TurnPlan()})

        self.assertEqual(engine.battlefield.base_two.health, 28)
        self.assertFalse(any(event.event_type == "base_attack" for event in events))

    def test_overflow_can_finish_the_fort_and_win(self):
        soldier = Soldier("Soldier", lane=Lane.FRONT)
        soldier.current_hp = 1
        battlefield = Battlefield(base_two=Base("Red", health=2), troops_one=[Tank("Tank")], troops_two=[soldier])
        engine = BattleEngine(battlefield)

        engine.play_round({Player.ONE: TurnPlan(attacks=(AttackOrder(attacker_index=0),)), Player.TWO: TurnPlan()})

        self.assertEqual(engine.battlefield.winner(), Player.ONE)

    def test_round_limit_uses_tiebreaker(self):
        battlefield = Battlefield(
            base_one=Base("Blue", health=20),
            base_two=Base("Red", health=15),
        )
        engine = BattleEngine(battlefield)

        result = engine.run(BalancedBot(), BalancedBot(), max_rounds=1)

        self.assertEqual(result.winner, Player.ONE)
        self.assertTrue(any(event.event_type == "tiebreak" for event in result.events))

    def test_report_contains_structured_battle_state(self):
        engine = BattleEngine()
        result = engine.run(BalancedBot(), DefensiveBot(), max_rounds=2)

        report = _build_report(engine, result)

        self.assertIn("strategies", report)
        self.assertIn("damage", report)
        self.assertIn("events", report)
        self.assertIn("round_snapshots", report)
        self.assertIn("opening_initiative", report)
        self.assertEqual(report["rounds_played"], result.rounds_played)
        self.assertEqual(len(report["round_snapshots"]), result.rounds_played)

        first_snapshot = report["round_snapshots"][0]
        final_snapshot = report["round_snapshots"][-1]
        self.assertEqual(first_snapshot["round"], 1)
        self.assertGreater(first_snapshot["event_count"], 0)
        self.assertEqual(final_snapshot["round"], result.rounds_played)
        self.assertEqual(final_snapshot["bases"], report["bases"])
        self.assertEqual(final_snapshot["troops"], report["troops_remaining"])
        self.assertEqual(
            final_snapshot["stats"]["player_one"]["damage_dealt"],
            report["damage"]["player_one"]["dealt"],
        )

    def test_round_snapshots_preserve_historical_state(self):
        engine = BattleEngine()
        empty_plans = {Player.ONE: TurnPlan(), Player.TWO: TurnPlan()}

        engine.play_round(empty_plans)
        engine.play_round(empty_plans)

        self.assertEqual(len(engine.round_snapshots), 2)
        self.assertEqual(engine.round_snapshots[0]["bases"]["player_one"]["resources"], 16)
        self.assertEqual(engine.round_snapshots[1]["bases"]["player_one"]["resources"], 22)
        self.assertLess(
            engine.round_snapshots[0]["event_count"],
            engine.round_snapshots[1]["event_count"],
        )


class StrategyTest(unittest.TestCase):
    def test_aggressive_bot_prefers_attack_units(self):
        battlefield = Battlefield(base_one=Base("Blue", resources=10))

        plan = AggressiveBot().choose_plan(Player.ONE, battlefield)

        self.assertEqual(plan.recruits[0].troop_kind, TroopKind.ARCHER)

    def test_defensive_bot_recruits_guardian_first(self):
        battlefield = Battlefield(base_one=Base("Blue", resources=10))

        plan = DefensiveBot().choose_plan(Player.ONE, battlefield)

        self.assertEqual(plan.recruits[0].troop_kind, TroopKind.GUARDIAN)


class TournamentTest(unittest.TestCase):
    def test_tournament_uses_round_robin_matchups(self):
        summary = run_tournament(simulations=2, max_rounds=4, seed=10)

        self.assertEqual(len(summary.matchups), 12)
        self.assertEqual(summary.simulations, 24)
        self.assertEqual(len(summary.standings), 4)

    def test_tournament_accepts_custom_strategy_list(self):
        summary = run_tournament(
            simulations=2,
            max_rounds=4,
            seed=10,
            strategies=("aggressive", "defensive"),
        )

        self.assertEqual(len(summary.matchups), 2)
        self.assertEqual(summary.simulations, 4)
        self.assertEqual(summary.strategies, ("aggressive", "defensive"))

    def test_tournament_aggregates_multiple_seeds_and_initiative_metrics(self):
        summary = run_tournament(
            simulations=2,
            max_rounds=8,
            strategies=("aggressive", "defensive"),
            seeds=(3, 11),
        )

        self.assertEqual(summary.seeds, (3, 11))
        self.assertEqual(summary.simulations_per_seed, 2)
        self.assertEqual(summary.simulations_per_matchup, 4)
        self.assertEqual(len(summary.matchups), 4)
        self.assertEqual(summary.simulations, 8)
        self.assertEqual(
            summary.initiative_wins + summary.response_wins + summary.draws,
            summary.simulations,
        )
        self.assertIn("initiative", summary.to_dict())

    def test_matchup_reports_wins_losses_draws_and_damage(self):
        summary = run_matchup("aggressive", "balanced", simulations=2, max_rounds=3, seed=2)

        total_outcomes = summary.strategy_one_wins + summary.strategy_two_wins + summary.draws
        self.assertEqual(total_outcomes, 2)
        self.assertEqual(summary.losses_for_strategy_one, summary.strategy_two_wins)
        self.assertLessEqual(summary.average_rounds, 3)
        self.assertGreaterEqual(summary.strategy_one_damage_dealt, 0)


class CliTest(unittest.TestCase):
    def test_parse_multiple_unique_seeds(self):
        self.assertEqual(_parse_seeds("3, 7,11"), (3, 7, 11))

    def test_parse_seeds_rejects_duplicates(self):
        with self.assertRaises(ValueError):
            _parse_seeds("3,7,3")

    def test_parse_strategies_from_comma_separated_value(self):
        self.assertEqual(
            _parse_strategies("aggressive, balanced, economy"),
            ("aggressive", "balanced", "economy"),
        )

    def test_parse_strategies_rejects_unknown_names(self):
        with self.assertRaises(ValueError):
            _parse_strategies("balanced,unknown")

    def test_summary_only_omits_tournament_matchups(self):
        output = StringIO()

        with redirect_stdout(output):
            exit_code = main(
                [
                    "--mode",
                    "tournament",
                    "--strategies",
                    "aggressive,balanced",
                    "--simulations",
                    "1",
                    "--rounds",
                    "2",
                    "--summary-only",
                ]
            )

        self.assertEqual(exit_code, 0)
        self.assertIn("Standings:", output.getvalue())
        self.assertNotIn("aggressive vs balanced", output.getvalue())


class BalanceRegressionTest(unittest.TestCase):
    def test_opening_initiative_advantage_stays_small(self):
        """Guarda contra a regressao da iniciativa, nao contra ruido.

        A amostra anterior era de 2 batalhas por confronto e caia exatamente em
        0.100, o limiar: bastava subir para 10 batalhas para medir 0.105 e o
        teste falhar sem nenhuma mudanca de comportamento. O limiar tambem
        cortava no meio da faixa natural — o benchmark de balance_notes.md
        mostra 8,5 a 11,0 p.p. conforme a seed.

        Agora a amostra e grande o bastante para o numero se estabilizar e o
        limite tem folga sobre essa faixa. Continua sendo um teste util: a
        regra anterior media entre 55 e 83 p.p., varias vezes o teto daqui.
        """
        summary = run_tournament(
            simulations=10,
            max_rounds=30,
            strategies=("aggressive", "balanced", "defensive", "economy", "random"),
            seeds=(3, 7, 11),
        )

        self.assertLessEqual(abs(summary.initiative_advantage), 0.15)


if __name__ == "__main__":
    unittest.main()
