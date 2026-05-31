from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol

from battle_simulator.models import Base, Troop, TroopFactory, TroopKind


class Player(int, Enum):
    ONE = 1
    TWO = 2

    @property
    def opponent(self) -> "Player":
        return Player.TWO if self == Player.ONE else Player.ONE


@dataclass(frozen=True)
class RecruitOrder:
    troop_kind: TroopKind
    quantity: int = 1


@dataclass(frozen=True)
class AttackOrder:
    attacker_index: int
    target_index: int | None = None


@dataclass(frozen=True)
class TurnPlan:
    recruits: tuple[RecruitOrder, ...] = ()
    attacks: tuple[AttackOrder, ...] = ()


class Strategy(Protocol):
    def choose_plan(self, player: Player, battlefield: "Battlefield") -> TurnPlan:
        pass


@dataclass
class BattleEvent:
    message: str


@dataclass
class BattleResult:
    winner: Player | None
    rounds_played: int
    events: list[BattleEvent]


@dataclass
class Battlefield:
    base_one: Base = field(default_factory=lambda: Base("Blue"))
    base_two: Base = field(default_factory=lambda: Base("Red"))
    troops_one: list[Troop] = field(default_factory=list)
    troops_two: list[Troop] = field(default_factory=list)
    factory: TroopFactory = field(default_factory=TroopFactory)

    def base_for(self, player: Player) -> Base:
        return self.base_one if player == Player.ONE else self.base_two

    def troops_for(self, player: Player) -> list[Troop]:
        return self.troops_one if player == Player.ONE else self.troops_two

    def recruit(self, player: Player, troop_kind: TroopKind) -> BattleEvent:
        base = self.base_for(player)
        troop = self.factory.create(troop_kind)
        base.spend(troop.cost)
        self.troops_for(player).append(troop)
        return BattleEvent(f"{base.name} recruited {troop.name}.")

    def remove_defeated(self) -> list[BattleEvent]:
        events: list[BattleEvent] = []
        for player in Player:
            troops = self.troops_for(player)
            defeated = [troop for troop in troops if not troop.is_alive]
            self._replace_troops(player, [troop for troop in troops if troop.is_alive])
            for troop in defeated:
                events.append(BattleEvent(f"{troop.name} was defeated."))
        return events

    def _replace_troops(self, player: Player, troops: list[Troop]) -> None:
        if player == Player.ONE:
            self.troops_one = troops
        else:
            self.troops_two = troops

    def winner(self) -> Player | None:
        if self.base_one.is_destroyed and self.base_two.is_destroyed:
            return None
        if self.base_two.is_destroyed:
            return Player.ONE
        if self.base_one.is_destroyed:
            return Player.TWO
        return None


class BattleEngine:
    def __init__(self, battlefield: Battlefield | None = None) -> None:
        self.battlefield = battlefield or Battlefield()
        self.events: list[BattleEvent] = []
        self.round_number = 0

    def play_round(self, plans: dict[Player, TurnPlan]) -> list[BattleEvent]:
        self.round_number += 1
        round_events = [BattleEvent(f"Round {self.round_number} started.")]

        for player in Player:
            round_events.extend(self._apply_recruit_orders(player, plans.get(player, TurnPlan())))

        for player in Player:
            if self.battlefield.winner() is not None:
                break
            round_events.extend(self._apply_attack_orders(player, plans.get(player, TurnPlan())))
            round_events.extend(self.battlefield.remove_defeated())

        for player in Player:
            self.battlefield.base_for(player).collect_resources()

        self.events.extend(round_events)
        return round_events

    def run(
        self,
        strategy_one: Strategy,
        strategy_two: Strategy,
        max_rounds: int = 100,
    ) -> BattleResult:
        strategies = {Player.ONE: strategy_one, Player.TWO: strategy_two}

        while self.battlefield.winner() is None and self.round_number < max_rounds:
            plans = {
                player: strategies[player].choose_plan(player, self.battlefield)
                for player in Player
            }
            self.play_round(plans)

        return BattleResult(
            winner=self.battlefield.winner(),
            rounds_played=self.round_number,
            events=self.events,
        )

    def _apply_recruit_orders(self, player: Player, plan: TurnPlan) -> list[BattleEvent]:
        events: list[BattleEvent] = []
        for order in plan.recruits:
            for _ in range(order.quantity):
                try:
                    events.append(self.battlefield.recruit(player, order.troop_kind))
                except ValueError as exc:
                    events.append(BattleEvent(str(exc)))
                    return events
        return events

    def _apply_attack_orders(self, player: Player, plan: TurnPlan) -> list[BattleEvent]:
        events: list[BattleEvent] = []
        attackers = list(self.battlefield.troops_for(player))
        enemies = self.battlefield.troops_for(player.opponent)
        enemy_base = self.battlefield.base_for(player.opponent)

        for order in plan.attacks:
            if order.attacker_index < 0 or order.attacker_index >= len(attackers):
                continue

            attacker = attackers[order.attacker_index]
            if not attacker.is_alive:
                continue

            living_enemies = [troop for troop in enemies if troop.is_alive]
            if not living_enemies:
                attacker.attack_base(enemy_base)
                events.append(
                    BattleEvent(
                        f"{attacker.name} attacked {enemy_base.name} base "
                        f"for {attacker.damage} damage."
                    )
                )
                continue

            target_index = 0 if order.target_index is None else order.target_index
            if target_index < 0 or target_index >= len(living_enemies):
                events.append(BattleEvent(f"Invalid target index: {target_index}."))
                continue

            target = living_enemies[target_index]
            attacker.attack_troop(target)
            events.append(
                BattleEvent(
                    f"{attacker.name} attacked {target.name} "
                    f"for {attacker.damage} damage."
                )
            )

        return events
