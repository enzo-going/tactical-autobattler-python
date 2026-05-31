from __future__ import annotations

import random
from abc import ABC, abstractmethod

from battle_simulator.engine import AttackOrder, Battlefield, Player, RecruitOrder, TurnPlan
from battle_simulator.models import TROOP_COSTS, TroopKind


class Strategy(ABC):
    @abstractmethod
    def choose_plan(self, player: Player, battlefield: Battlefield) -> TurnPlan:
        raise NotImplementedError


class BalancedBot(Strategy):
    def choose_plan(self, player: Player, battlefield: Battlefield) -> TurnPlan:
        base = battlefield.base_for(player)
        troops = battlefield.troops_for(player)
        recruits: list[RecruitOrder] = []
        budget = base.resources

        while budget >= TROOP_COSTS[TroopKind.SOLDIER]:
            army_size = len(troops) + len(recruits)
            if budget >= TROOP_COSTS[TroopKind.TANK] and army_size >= 3:
                troop_kind = TroopKind.TANK
            elif budget >= TROOP_COSTS[TroopKind.GUARDIAN] and army_size == 1:
                troop_kind = TroopKind.GUARDIAN
            elif budget >= TROOP_COSTS[TroopKind.ARCHER]:
                troop_kind = TroopKind.ARCHER
            else:
                troop_kind = TroopKind.SOLDIER

            recruits.append(RecruitOrder(troop_kind))
            budget -= TROOP_COSTS[troop_kind]

        attacks = tuple(AttackOrder(index, 0) for index, _ in enumerate(troops))
        return TurnPlan(recruits=tuple(recruits), attacks=attacks)


class AggressiveBot(Strategy):
    def choose_plan(self, player: Player, battlefield: Battlefield) -> TurnPlan:
        base = battlefield.base_for(player)
        troops = battlefield.troops_for(player)
        enemies = battlefield.troops_for(player.opponent)
        budget = base.resources
        recruits: list[RecruitOrder] = []

        for troop_kind in (TroopKind.TANK, TroopKind.ARCHER, TroopKind.SOLDIER):
            while budget >= TROOP_COSTS[troop_kind]:
                recruits.append(RecruitOrder(troop_kind))
                budget -= TROOP_COSTS[troop_kind]

        target_index = _weakest_target_index(enemies)
        attacks = tuple(AttackOrder(index, target_index) for index, _ in enumerate(troops))
        return TurnPlan(recruits=tuple(recruits), attacks=attacks)


class RandomBot(Strategy):
    def __init__(self, seed: int | None = None) -> None:
        self._random = random.Random(seed)

    def choose_plan(self, player: Player, battlefield: Battlefield) -> TurnPlan:
        base = battlefield.base_for(player)
        troops = battlefield.troops_for(player)
        enemies = battlefield.troops_for(player.opponent)
        recruits: list[RecruitOrder] = []
        budget = base.resources

        while budget >= TROOP_COSTS[TroopKind.SOLDIER] and self._random.random() < 0.75:
            affordable = [
                troop_kind
                for troop_kind, cost in TROOP_COSTS.items()
                if cost <= budget
            ]
            troop_kind = self._random.choice(affordable)
            recruits.append(RecruitOrder(troop_kind))
            budget -= TROOP_COSTS[troop_kind]

        attacks = []
        for attacker_index, _ in enumerate(troops):
            target_index = None
            if enemies:
                target_index = self._random.randrange(len(enemies))
            attacks.append(AttackOrder(attacker_index, target_index))

        return TurnPlan(recruits=tuple(recruits), attacks=tuple(attacks))


def _weakest_target_index(enemies) -> int | None:
    if not enemies:
        return None
    living = [(index, troop) for index, troop in enumerate(enemies) if troop.is_alive]
    if not living:
        return None
    return min(living, key=lambda item: item[1].health)[0]
