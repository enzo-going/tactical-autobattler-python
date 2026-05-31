from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Lane(str, Enum):
    FRONT = "front"
    BACK = "back"


class Role(str, Enum):
    ASSAULT = "assault"
    DEFENDER = "defender"
    RANGED = "ranged"
    SUPPORT = "support"


class StatusEffect(str, Enum):
    BLEED = "bleed"
    SHIELD = "shield"
    STUN = "stun"


class TroopKind(str, Enum):
    SOLDIER = "soldier"
    ARCHER = "archer"
    GUARDIAN = "guardian"
    MEDIC = "medic"
    TANK = "tank"


@dataclass
class Base:
    name: str
    health: int = 28
    resources: int = 10
    resource_income: int = 6

    @property
    def is_destroyed(self) -> bool:
        return self.health <= 0

    def receive_damage(self, amount: int) -> int:
        if amount < 0:
            raise ValueError("Damage cannot be negative.")
        applied = min(self.health, amount)
        self.health -= applied
        return applied

    def can_afford(self, cost: int) -> bool:
        return self.resources >= cost

    def spend(self, cost: int) -> None:
        if cost < 0:
            raise ValueError("Cost cannot be negative.")
        if not self.can_afford(cost):
            raise ValueError(f"{self.name} does not have enough resources.")
        self.resources -= cost

    def collect_resources(self) -> None:
        self.resources += self.resource_income


@dataclass
class Troop:
    name: str
    max_hp: int
    attack: int
    defense: int
    speed: int
    range: int
    cost: int
    role: Role
    lane: Lane = Lane.FRONT
    current_hp: int | None = None
    effects: dict[StatusEffect, int] = field(default_factory=dict)
    damage_dealt: int = 0
    damage_received: int = 0

    def __post_init__(self) -> None:
        if self.current_hp is None:
            self.current_hp = self.max_hp

    @property
    def health(self) -> int:
        return self.current_hp or 0

    @health.setter
    def health(self, value: int) -> None:
        self.current_hp = max(0, min(self.max_hp, value))

    @property
    def damage(self) -> int:
        return self.attack

    @property
    def is_alive(self) -> bool:
        return self.health > 0

    def can_reach(self, target: "Troop") -> bool:
        return self.range >= lane_distance(target.lane)

    def attack_troop(self, target: "Troop") -> int:
        return target.receive_damage(self.attack)

    def attack_base(self, target: Base) -> int:
        return target.receive_damage(self.attack)

    def receive_damage(self, amount: int, ignore_defense: bool = False) -> int:
        if amount < 0:
            raise ValueError("Damage cannot be negative.")
        mitigated = amount if ignore_defense else max(1, amount - self.defense)
        if self.effects.pop(StatusEffect.SHIELD, 0) > 0:
            mitigated = max(0, mitigated - 1)
        applied = min(self.health, mitigated)
        self.current_hp = self.health - applied
        self.damage_received += applied
        return applied

    def heal(self, amount: int) -> int:
        if amount < 0:
            raise ValueError("Healing cannot be negative.")
        missing_hp = self.max_hp - self.health
        applied = min(missing_hp, amount)
        self.current_hp = self.health + applied
        return applied

    def add_effect(self, effect: StatusEffect, duration: int) -> None:
        if duration <= 0:
            return
        self.effects[effect] = max(self.effects.get(effect, 0), duration)

    def has_effect(self, effect: StatusEffect) -> bool:
        return self.effects.get(effect, 0) > 0

    def tick_effects(self) -> list[tuple[StatusEffect, int]]:
        triggered: list[tuple[StatusEffect, int]] = []
        if self.has_effect(StatusEffect.BLEED):
            triggered.append((StatusEffect.BLEED, self.receive_damage(1, ignore_defense=True)))

        for effect in list(self.effects):
            self.effects[effect] -= 1
            if self.effects[effect] <= 0:
                del self.effects[effect]

        return triggered


class Soldier(Troop):
    def __init__(self, name: str, lane: Lane = Lane.FRONT):
        super().__init__(
            name=name,
            max_hp=4,
            attack=2,
            defense=1,
            speed=4,
            range=1,
            cost=2,
            role=Role.ASSAULT,
            lane=lane,
        )


class Archer(Troop):
    def __init__(self, name: str, lane: Lane = Lane.BACK):
        super().__init__(
            name=name,
            max_hp=3,
            attack=3,
            defense=0,
            speed=5,
            range=2,
            cost=3,
            role=Role.RANGED,
            lane=lane,
        )


class Guardian(Troop):
    def __init__(self, name: str, lane: Lane = Lane.FRONT):
        super().__init__(
            name=name,
            max_hp=9,
            attack=2,
            defense=2,
            speed=2,
            range=1,
            cost=4,
            role=Role.DEFENDER,
            lane=lane,
        )


class Medic(Troop):
    def __init__(self, name: str, lane: Lane = Lane.BACK):
        super().__init__(
            name=name,
            max_hp=4,
            attack=1,
            defense=0,
            speed=3,
            range=2,
            cost=5,
            role=Role.SUPPORT,
            lane=lane,
        )


class Tank(Troop):
    def __init__(self, name: str, lane: Lane = Lane.FRONT):
        super().__init__(
            name=name,
            max_hp=8,
            attack=5,
            defense=2,
            speed=1,
            range=1,
            cost=5,
            role=Role.ASSAULT,
            lane=lane,
        )


class TroopFactory:
    def __init__(self) -> None:
        self._counters = {troop_kind: 0 for troop_kind in TroopKind}

    def create(self, kind: TroopKind, lane: Lane | None = None) -> Troop:
        if kind not in self._counters:
            raise ValueError(f"Unsupported troop kind: {kind}")

        self._counters[kind] += 1
        number = self._counters[kind]

        if kind == TroopKind.SOLDIER:
            return Soldier(name=f"Soldier {number}", lane=lane or Lane.FRONT)
        if kind == TroopKind.ARCHER:
            return Archer(name=f"Archer {number}", lane=lane or Lane.BACK)
        if kind == TroopKind.GUARDIAN:
            return Guardian(name=f"Guardian {number}", lane=lane or Lane.FRONT)
        if kind == TroopKind.MEDIC:
            return Medic(name=f"Medic {number}", lane=lane or Lane.BACK)
        if kind == TroopKind.TANK:
            return Tank(name=f"Tank {number}", lane=lane or Lane.FRONT)

        raise ValueError(f"Unsupported troop kind: {kind}")


def lane_distance(lane: Lane) -> int:
    return 1 if lane == Lane.FRONT else 2


TROOP_COSTS = {
    TroopKind.SOLDIER: Soldier(name="preview").cost,
    TroopKind.ARCHER: Archer(name="preview").cost,
    TroopKind.GUARDIAN: Guardian(name="preview").cost,
    TroopKind.MEDIC: Medic(name="preview").cost,
    TroopKind.TANK: Tank(name="preview").cost,
}
