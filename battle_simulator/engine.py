from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol

from battle_simulator.models import (
    Base,
    Lane,
    Role,
    StatusEffect,
    Troop,
    TroopFactory,
    TroopKind,
)


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
    lane: Lane | None = None


@dataclass(frozen=True)
class AttackOrder:
    attacker_index: int
    target_index: int | None = None


@dataclass(frozen=True)
class TurnPlan:
    recruits: tuple[RecruitOrder, ...] = ()
    attacks: tuple[AttackOrder, ...] = ()


class Strategy(Protocol):
    name: str

    def choose_plan(self, player: Player, battlefield: "Battlefield") -> TurnPlan:
        pass


@dataclass
class BattleEvent:
    event_type: str
    round_number: int
    message: str
    player: Player | None = None
    actor: str | None = None
    target: str | None = None
    amount: int = 0
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "type": self.event_type,
            "round": self.round_number,
            "player": None if self.player is None else self.player.value,
            "actor": self.actor,
            "target": self.target,
            "amount": self.amount,
            "message": self.message,
            "metadata": self.metadata,
        }


@dataclass
class BattleStats:
    units_recruited: dict[Player, int] = field(default_factory=lambda: {Player.ONE: 0, Player.TWO: 0})
    damage_dealt: dict[Player, int] = field(default_factory=lambda: {Player.ONE: 0, Player.TWO: 0})
    damage_taken: dict[Player, int] = field(default_factory=lambda: {Player.ONE: 0, Player.TWO: 0})

    def record_recruit(self, player: Player) -> None:
        self.units_recruited[player] += 1

    def record_damage(self, player: Player, amount: int) -> None:
        self.damage_dealt[player] += amount
        self.damage_taken[player.opponent] += amount


@dataclass
class BattleResult:
    winner: Player | None
    rounds_played: int
    events: list[BattleEvent]
    stats: BattleStats
    strategies: dict[Player, str] = field(default_factory=dict)


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

    def living_troops_for(self, player: Player) -> list[Troop]:
        return [troop for troop in self.troops_for(player) if troop.is_alive]

    def recruit(self, player: Player, troop_kind: TroopKind, lane: Lane | None = None) -> Troop:
        base = self.base_for(player)
        troop = self.factory.create(troop_kind, lane=lane)
        base.spend(troop.cost)
        self.troops_for(player).append(troop)
        return troop

    def remove_defeated(self, round_number: int = 0) -> list[BattleEvent]:
        events: list[BattleEvent] = []
        for player in Player:
            troops = self.troops_for(player)
            defeated = [troop for troop in troops if not troop.is_alive]
            self._replace_troops(player, [troop for troop in troops if troop.is_alive])
            for troop in defeated:
                events.append(
                    BattleEvent(
                        event_type="unit_defeated",
                        round_number=round_number,
                        player=player,
                        actor=troop.name,
                        message=f"{troop.name} was defeated.",
                    )
                )
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
        self.stats = BattleStats()
        self.round_number = 0
        self.strategy_names: dict[Player, str] = {}

    def play_round(self, plans: dict[Player, TurnPlan]) -> list[BattleEvent]:
        self.round_number += 1
        round_events = [
            BattleEvent(
                event_type="round_started",
                round_number=self.round_number,
                message=f"Round {self.round_number} started.",
            )
        ]

        round_events.extend(self._apply_start_of_round_effects())

        for player in Player:
            round_events.extend(self._apply_recruit_orders(player, plans.get(player, TurnPlan())))

        initiative = self._initiative_order(plans)
        for player, order in initiative:
            if self.battlefield.winner() is not None:
                break
            round_events.extend(self._perform_unit_action(player, order))
            round_events.extend(self.battlefield.remove_defeated(self.round_number))

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
        self.strategy_names = {
            Player.ONE: getattr(strategy_one, "name", strategy_one.__class__.__name__),
            Player.TWO: getattr(strategy_two, "name", strategy_two.__class__.__name__),
        }

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
            stats=self.stats,
            strategies=self.strategy_names,
        )

    def _apply_start_of_round_effects(self) -> list[BattleEvent]:
        events: list[BattleEvent] = []
        for player in Player:
            for troop in self.battlefield.living_troops_for(player):
                for effect, amount in troop.tick_effects():
                    if amount <= 0:
                        continue
                    self.stats.damage_taken[player] += amount
                    events.append(
                        BattleEvent(
                            event_type="effect_damage",
                            round_number=self.round_number,
                            player=player,
                            actor=effect.value,
                            target=troop.name,
                            amount=amount,
                            message=f"{troop.name} took {amount} {effect.value} damage.",
                        )
                    )
        events.extend(self.battlefield.remove_defeated(self.round_number))
        return events

    def _apply_recruit_orders(self, player: Player, plan: TurnPlan) -> list[BattleEvent]:
        events: list[BattleEvent] = []
        for order in plan.recruits:
            for _ in range(order.quantity):
                try:
                    troop = self.battlefield.recruit(player, order.troop_kind, lane=order.lane)
                    self.stats.record_recruit(player)
                    events.append(
                        BattleEvent(
                            event_type="unit_recruited",
                            round_number=self.round_number,
                            player=player,
                            actor=troop.name,
                            amount=troop.cost,
                            message=(
                                f"{self.battlefield.base_for(player).name} recruited "
                                f"{troop.name} in {troop.lane.value} lane."
                            ),
                            metadata={
                                "kind": order.troop_kind.value,
                                "lane": troop.lane.value,
                                "role": troop.role.value,
                                "cost": troop.cost,
                            },
                        )
                    )
                except ValueError as exc:
                    events.append(
                        BattleEvent(
                            event_type="invalid_recruit",
                            round_number=self.round_number,
                            player=player,
                            message=str(exc),
                        )
                    )
                    return events
        return events

    def _initiative_order(self, plans: dict[Player, TurnPlan]) -> list[tuple[Player, AttackOrder]]:
        planned: list[tuple[Player, AttackOrder, int]] = []
        for player in Player:
            troops = list(self.battlefield.troops_for(player))
            for order in plans.get(player, TurnPlan()).attacks:
                if order.attacker_index < 0 or order.attacker_index >= len(troops):
                    continue
                attacker = troops[order.attacker_index]
                planned.append((player, order, attacker.speed))
        planned.sort(key=lambda item: item[2], reverse=True)
        return [(player, order) for player, order, _ in planned]

    def _perform_unit_action(self, player: Player, order: AttackOrder) -> list[BattleEvent]:
        events: list[BattleEvent] = []
        attackers = self.battlefield.troops_for(player)
        if order.attacker_index < 0 or order.attacker_index >= len(attackers):
            return events

        attacker = attackers[order.attacker_index]
        if not attacker.is_alive:
            return events

        if attacker.has_effect(StatusEffect.STUN):
            attacker.effects.pop(StatusEffect.STUN, None)
            return [
                BattleEvent(
                    event_type="unit_stunned",
                    round_number=self.round_number,
                    player=player,
                    actor=attacker.name,
                    message=f"{attacker.name} is stunned and skips the action.",
                )
            ]

        if attacker.role == Role.SUPPORT:
            support_events = self._perform_support_action(player, attacker)
            if support_events:
                return support_events

        if attacker.role == Role.DEFENDER:
            guard_events = self._perform_guard_action(player, attacker)
            if guard_events:
                return guard_events

        return self._perform_attack(player, attacker, order.target_index)

    def _perform_support_action(self, player: Player, attacker: Troop) -> list[BattleEvent]:
        allies = [
            troop
            for troop in self.battlefield.living_troops_for(player)
            if troop.health < troop.max_hp
        ]
        if not allies:
            return []
        target = min(allies, key=lambda troop: troop.health / troop.max_hp)
        healed = target.heal(3)
        if healed <= 0:
            return []
        return [
            BattleEvent(
                event_type="heal",
                round_number=self.round_number,
                player=player,
                actor=attacker.name,
                target=target.name,
                amount=healed,
                message=f"{attacker.name} healed {target.name} for {healed} HP.",
            )
        ]

    def _perform_guard_action(self, player: Player, attacker: Troop) -> list[BattleEvent]:
        allies = self.battlefield.living_troops_for(player)
        shield_targets = [
            troop
            for troop in allies
            if troop.lane == Lane.FRONT and not troop.has_effect(StatusEffect.SHIELD)
        ]
        if not shield_targets:
            return []
        target = min(shield_targets, key=lambda troop: troop.health)
        target.add_effect(StatusEffect.SHIELD, duration=2)
        return [
            BattleEvent(
                event_type="shield",
                round_number=self.round_number,
                player=player,
                actor=attacker.name,
                target=target.name,
                message=f"{attacker.name} shielded {target.name}.",
            )
        ]

    def _perform_attack(
        self,
        player: Player,
        attacker: Troop,
        target_index: int | None,
    ) -> list[BattleEvent]:
        enemies = self.battlefield.living_troops_for(player.opponent)
        enemy_base = self.battlefield.base_for(player.opponent)

        if not enemies:
            applied = enemy_base.receive_damage(attacker.attack)
            attacker.damage_dealt += applied
            self.stats.record_damage(player, applied)
            return [
                BattleEvent(
                    event_type="base_attack",
                    round_number=self.round_number,
                    player=player,
                    actor=attacker.name,
                    target=enemy_base.name,
                    amount=applied,
                    message=f"{attacker.name} attacked {enemy_base.name} base for {applied} damage.",
                )
            ]

        if target_index is not None and (target_index < 0 or target_index >= len(enemies)):
            return [
                BattleEvent(
                    event_type="invalid_target",
                    round_number=self.round_number,
                    player=player,
                    actor=attacker.name,
                    message=f"Invalid target index: {target_index}.",
                )
            ]

        target = self._select_target(attacker, enemies, target_index)
        if target is None:
            return [
                BattleEvent(
                    event_type="out_of_range",
                    round_number=self.round_number,
                    player=player,
                    actor=attacker.name,
                    message=f"{attacker.name} has no target in range.",
                )
            ]

        applied = target.receive_damage(attacker.attack)
        attacker.damage_dealt += applied
        self.stats.record_damage(player, applied)
        events = [
            BattleEvent(
                event_type="unit_attack",
                round_number=self.round_number,
                player=player,
                actor=attacker.name,
                target=target.name,
                amount=applied,
                message=f"{attacker.name} attacked {target.name} for {applied} damage.",
                metadata={
                    "attack": attacker.attack,
                    "target_defense": target.defense,
                    "attacker_lane": attacker.lane.value,
                    "target_lane": target.lane.value,
                },
            )
        ]

        if applied > 0 and isinstance(attacker, Troop):
            events.extend(self._apply_attack_effects(player, attacker, target))

        return events

    def _select_target(
        self,
        attacker: Troop,
        enemies: list[Troop],
        target_index: int | None,
    ) -> Troop | None:
        living = [troop for troop in enemies if troop.is_alive]
        if target_index is not None:
            if target_index < 0 or target_index >= len(living):
                return None
            target = living[target_index]
            return target if attacker.can_reach(target) else None

        reachable = [troop for troop in living if attacker.can_reach(troop)]
        if not reachable:
            return None
        return min(reachable, key=lambda troop: (troop.lane != Lane.FRONT, troop.health))

    def _apply_attack_effects(
        self,
        player: Player,
        attacker: Troop,
        target: Troop,
    ) -> list[BattleEvent]:
        events: list[BattleEvent] = []
        if attacker.role == Role.RANGED:
            target.add_effect(StatusEffect.BLEED, duration=2)
            events.append(
                BattleEvent(
                    event_type="effect_applied",
                    round_number=self.round_number,
                    player=player,
                    actor=attacker.name,
                    target=target.name,
                    message=f"{attacker.name} applied bleed to {target.name}.",
                    metadata={"effect": StatusEffect.BLEED.value},
                )
            )

        if attacker.name.startswith("Tank"):
            target.add_effect(StatusEffect.STUN, duration=2)
            events.append(
                BattleEvent(
                    event_type="effect_applied",
                    round_number=self.round_number,
                    player=player,
                    actor=attacker.name,
                    target=target.name,
                    message=f"{attacker.name} stunned {target.name}.",
                    metadata={"effect": StatusEffect.STUN.value},
                )
            )

        return events
