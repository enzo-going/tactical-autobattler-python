from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum


class TroopKind(str, Enum):
    SOLDIER = "soldier"
    ARCHER = "archer"
    GUARDIAN = "guardian"
    TANK = "tank"


@dataclass
class Base:
    name: str
    health: int = 30
    resources: int = 10
    resource_income: int = 7

    @property
    def is_destroyed(self) -> bool:
        return self.health <= 0

    def receive_damage(self, amount: int) -> None:
        if amount < 0:
            raise ValueError("Damage cannot be negative.")
        self.health = max(0, self.health - amount)

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
class Troop(ABC):
    name: str
    health: int
    damage: int
    cost: int

    @property
    def is_alive(self) -> bool:
        return self.health > 0

    def receive_damage(self, amount: int) -> None:
        if amount < 0:
            raise ValueError("Damage cannot be negative.")
        self.health = max(0, self.health - amount)

    @abstractmethod
    def attack_troop(self, target: "Troop") -> None:
        raise NotImplementedError

    @abstractmethod
    def attack_base(self, target: Base) -> None:
        raise NotImplementedError


class Soldier(Troop):
    def __init__(self, name: str):
        super().__init__(name=name, health=3, damage=1, cost=2)

    def attack_troop(self, target: Troop) -> None:
        target.receive_damage(self.damage)

    def attack_base(self, target: Base) -> None:
        target.receive_damage(self.damage)


class Archer(Troop):
    def __init__(self, name: str):
        super().__init__(name=name, health=2, damage=2, cost=3)

    def attack_troop(self, target: Troop) -> None:
        target.receive_damage(self.damage)

    def attack_base(self, target: Base) -> None:
        target.receive_damage(self.damage)


class Guardian(Troop):
    def __init__(self, name: str):
        super().__init__(name=name, health=10, damage=1, cost=4)

    def attack_troop(self, target: Troop) -> None:
        target.receive_damage(self.damage)

    def attack_base(self, target: Base) -> None:
        target.receive_damage(self.damage)


class Tank(Troop):
    def __init__(self, name: str):
        super().__init__(name=name, health=8, damage=3, cost=5)

    def attack_troop(self, target: Troop) -> None:
        target.receive_damage(self.damage)

    def attack_base(self, target: Base) -> None:
        target.receive_damage(self.damage)


class TroopFactory:
    def __init__(self) -> None:
        self._counters = {troop_kind: 0 for troop_kind in TroopKind}

    def create(self, kind: TroopKind) -> Troop:
        if kind not in self._counters:
            raise ValueError(f"Unsupported troop kind: {kind}")

        self._counters[kind] += 1
        number = self._counters[kind]

        if kind == TroopKind.SOLDIER:
            return Soldier(name=f"Soldier {number}")
        if kind == TroopKind.ARCHER:
            return Archer(name=f"Archer {number}")
        if kind == TroopKind.GUARDIAN:
            return Guardian(name=f"Guardian {number}")
        if kind == TroopKind.TANK:
            return Tank(name=f"Tank {number}")

        raise ValueError(f"Unsupported troop kind: {kind}")


TROOP_COSTS = {
    TroopKind.SOLDIER: Soldier(name="preview").cost,
    TroopKind.ARCHER: Archer(name="preview").cost,
    TroopKind.GUARDIAN: Guardian(name="preview").cost,
    TroopKind.TANK: Tank(name="preview").cost,
}
