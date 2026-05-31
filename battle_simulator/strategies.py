from __future__ import annotations

import random
from abc import ABC, abstractmethod

from battle_simulator.engine import AttackOrder, Battlefield, Player, RecruitOrder, TurnPlan
from battle_simulator.models import Lane, TROOP_COSTS, Role, Troop, TroopKind


class Strategy(ABC):
    name = "strategy"

    @abstractmethod
    def choose_plan(self, player: Player, battlefield: Battlefield) -> TurnPlan:
        raise NotImplementedError


class BalancedBot(Strategy):
    name = "balanced"

    def choose_plan(self, player: Player, battlefield: Battlefield) -> TurnPlan:
        base = battlefield.base_for(player)
        troops = battlefield.troops_for(player)
        budget = base.resources
        recruits: list[RecruitOrder] = []

        for troop_kind, lane in _balanced_purchase_order(troops):
            while budget >= TROOP_COSTS[troop_kind] and _needs_unit(recruits, troop_kind, max_count=1):
                recruits.append(RecruitOrder(troop_kind, lane=lane))
                budget -= TROOP_COSTS[troop_kind]

        while budget >= TROOP_COSTS[TroopKind.SOLDIER]:
            troop_kind = TroopKind.ARCHER if budget >= TROOP_COSTS[TroopKind.ARCHER] else TroopKind.SOLDIER
            lane = Lane.BACK if troop_kind == TroopKind.ARCHER else Lane.FRONT
            recruits.append(RecruitOrder(troop_kind, lane=lane))
            budget -= TROOP_COSTS[troop_kind]

        attacks = _attack_orders(troops, battlefield.living_troops_for(player.opponent))
        return TurnPlan(recruits=tuple(recruits), attacks=attacks)


class AggressiveBot(Strategy):
    name = "aggressive"

    def choose_plan(self, player: Player, battlefield: Battlefield) -> TurnPlan:
        base = battlefield.base_for(player)
        troops = battlefield.troops_for(player)
        enemies = battlefield.living_troops_for(player.opponent)
        budget = base.resources
        recruits: list[RecruitOrder] = []

        for troop_kind, lane in (
            (TroopKind.TANK, Lane.FRONT),
            (TroopKind.ARCHER, Lane.BACK),
            (TroopKind.SOLDIER, Lane.FRONT),
        ):
            while budget >= TROOP_COSTS[troop_kind]:
                recruits.append(RecruitOrder(troop_kind, lane=lane))
                budget -= TROOP_COSTS[troop_kind]

        target_index = _weakest_target_index(enemies)
        attacks = tuple(AttackOrder(index, target_index) for index, _ in enumerate(troops))
        return TurnPlan(recruits=tuple(recruits), attacks=attacks)


class DefensiveBot(Strategy):
    name = "defensive"

    def choose_plan(self, player: Player, battlefield: Battlefield) -> TurnPlan:
        base = battlefield.base_for(player)
        troops = battlefield.troops_for(player)
        budget = base.resources
        recruits: list[RecruitOrder] = []

        for troop_kind, lane in (
            (TroopKind.GUARDIAN, Lane.FRONT),
            (TroopKind.MEDIC, Lane.BACK),
            (TroopKind.ARCHER, Lane.BACK),
            (TroopKind.SOLDIER, Lane.FRONT),
        ):
            if budget >= TROOP_COSTS[troop_kind]:
                recruits.append(RecruitOrder(troop_kind, lane=lane))
                budget -= TROOP_COSTS[troop_kind]

        attacks = _attack_orders(troops, battlefield.living_troops_for(player.opponent))
        return TurnPlan(recruits=tuple(recruits), attacks=attacks)


class EconomyBot(Strategy):
    name = "economy"

    def choose_plan(self, player: Player, battlefield: Battlefield) -> TurnPlan:
        base = battlefield.base_for(player)
        troops = battlefield.troops_for(player)
        enemies = battlefield.living_troops_for(player.opponent)
        recruits: list[RecruitOrder] = []

        if base.resources >= 12:
            recruits.append(RecruitOrder(TroopKind.TANK, lane=Lane.FRONT))
            recruits.append(RecruitOrder(TroopKind.ARCHER, lane=Lane.BACK))
        elif base.resources >= 8:
            recruits.append(RecruitOrder(TroopKind.GUARDIAN, lane=Lane.FRONT))
        elif not troops and base.resources >= TROOP_COSTS[TroopKind.SOLDIER]:
            recruits.append(RecruitOrder(TroopKind.SOLDIER, lane=Lane.FRONT))

        return TurnPlan(recruits=tuple(recruits), attacks=_attack_orders(troops, enemies))


class RandomBot(Strategy):
    name = "random"

    def __init__(self, seed: int | None = None) -> None:
        self._random = random.Random(seed)

    def choose_plan(self, player: Player, battlefield: Battlefield) -> TurnPlan:
        base = battlefield.base_for(player)
        troops = battlefield.troops_for(player)
        enemies = battlefield.living_troops_for(player.opponent)
        recruits: list[RecruitOrder] = []
        budget = base.resources

        while budget >= TROOP_COSTS[TroopKind.SOLDIER] and self._random.random() < 0.70:
            affordable = [
                troop_kind
                for troop_kind, cost in TROOP_COSTS.items()
                if cost <= budget
            ]
            troop_kind = self._random.choice(affordable)
            lane = Lane.BACK if troop_kind in {TroopKind.ARCHER, TroopKind.MEDIC} else Lane.FRONT
            recruits.append(RecruitOrder(troop_kind, lane=lane))
            budget -= TROOP_COSTS[troop_kind]

        attacks = []
        for attacker_index, troop in enumerate(troops):
            reachable = _reachable_enemies(troop, enemies)
            target_index = None
            if reachable:
                target = self._random.choice(reachable)
                target_index = enemies.index(target)
            attacks.append(AttackOrder(attacker_index, target_index))

        return TurnPlan(recruits=tuple(recruits), attacks=tuple(attacks))


def _balanced_purchase_order(troops: list[Troop]) -> tuple[tuple[TroopKind, Lane], ...]:
    existing_roles = {troop.role for troop in troops}
    order: list[tuple[TroopKind, Lane]] = []
    if Role.DEFENDER not in existing_roles:
        order.append((TroopKind.GUARDIAN, Lane.FRONT))
    if Role.RANGED not in existing_roles:
        order.append((TroopKind.ARCHER, Lane.BACK))
    if Role.SUPPORT not in existing_roles:
        order.append((TroopKind.MEDIC, Lane.BACK))
    order.append((TroopKind.TANK, Lane.FRONT))
    return tuple(order)


def _needs_unit(recruits: list[RecruitOrder], troop_kind: TroopKind, max_count: int) -> bool:
    return sum(1 for recruit in recruits if recruit.troop_kind == troop_kind) < max_count


def _attack_orders(troops: list[Troop], enemies: list[Troop]) -> tuple[AttackOrder, ...]:
    return tuple(
        AttackOrder(index, _best_target_index(troop, enemies))
        for index, troop in enumerate(troops)
    )


def _best_target_index(troop: Troop, enemies: list[Troop]) -> int | None:
    reachable = _reachable_enemies(troop, enemies)
    if not reachable:
        return None
    target = min(reachable, key=lambda enemy: (enemy.lane != Lane.FRONT, enemy.health))
    return enemies.index(target)


def _weakest_target_index(enemies: list[Troop]) -> int | None:
    living = [troop for troop in enemies if troop.is_alive]
    if not living:
        return None
    return enemies.index(min(living, key=lambda troop: troop.health))


def _reachable_enemies(troop: Troop, enemies: list[Troop]) -> list[Troop]:
    return [enemy for enemy in enemies if enemy.is_alive and troop.can_reach(enemy)]
