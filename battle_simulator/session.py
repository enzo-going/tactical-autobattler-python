"""An explicit, command-driven match. No clock or browser owns game rules."""

from __future__ import annotations

from battle_simulator.engine import (
    BattleEngine,
    BattleEvent,
    Battlefield,
    Player,
    RecruitOrder,
    TurnPlan,
)
from battle_simulator.models import (
    Lane,
    Role,
    StatusEffect,
    TROOP_COSTS,
    Troop,
    TroopKind,
    can_strike,
)
from battle_simulator.tournament import STRATEGIES


class TacticalSession:
    """Recruit, alternate unit actions, review, repeat. Names are stable unit IDs."""

    roster_limit = 8
    ruleset = "tactical-v3"

    def __init__(self, opponent: str = "balanced", seed: int = 11, max_rounds: int = 20):
        if opponent not in STRATEGIES:
            raise ValueError("Adversário desconhecido.")
        if type(seed) is not int or not 0 <= seed <= 999999:
            raise ValueError("A seed deve estar entre 0 e 999999.")
        if type(max_rounds) is not int or not 1 <= max_rounds <= 50:
            raise ValueError("Escolha entre 1 e 50 rodadas.")
        self.engine = BattleEngine(initiative_seed=seed)
        self.engine.battlefield.base_one.name = "Seu forte"
        self.engine.battlefield.base_two.name = "Forte rival"
        self.bot = STRATEGIES[opponent](seed)
        self.opponent = opponent
        self.seed = seed
        self.max_rounds = max_rounds
        self.phase = "recruit"
        self.winner: Player | None = None
        self.reason = ""
        self.acted: set[str] = set()
        self.commands: list[dict] = []
        self.refundable: set[str] = set()
        self.engine.round_number = 1
        self._event("round_started")

    @property
    def field(self) -> Battlefield:
        return self.engine.battlefield

    def _event(
        self,
        kind: str,
        player: Player | None = None,
        actor: str | None = None,
        target: str | None = None,
        amount: int = 0,
        **metadata,
    ) -> None:
        self.engine.events.append(
            BattleEvent(
                kind,
                self.engine.round_number,
                kind,
                player,
                actor,
                target,
                amount,
                metadata,
            )
        )

    def command(self, command: dict) -> dict:
        if not isinstance(command, dict):
            raise ValueError("Comando inválido.")
        kind = command.get("type")
        if kind == "recruit" and self.phase == "recruit":
            try:
                troop_kind = TroopKind(command.get("kind"))
                lane = Lane(command.get("lane"))
            except (ValueError, TypeError):
                raise ValueError("Escolha uma unidade e uma linha válidas.") from None
            if len(self.field.troops_one) >= self.roster_limit:
                raise ValueError("Seu esquadrão já tem 8 unidades.")
            if not self.field.base_one.can_afford(TROOP_COSTS[troop_kind]):
                raise ValueError("Suprimentos insuficientes.")
            self._recruit(Player.ONE, troop_kind, lane)
            self.refundable.add(self.field.troops_one[-1].name)
        elif kind in ("deploy", "return") and self.phase == "recruit":
            actor = next((t for t in self.field.troops_one if t.name == command.get("actor")), None)
            if actor is None:
                raise ValueError("Selecione uma unidade do seu esquadrão.")
            if kind == "return":
                if actor.name not in self.refundable:
                    raise ValueError("Só recrutas comprados nesta preparação podem ser devolvidos.")
                self.field.troops_one.remove(actor)
                self.refundable.remove(actor.name)
                self.field.base_one.resources += actor.cost
                self.engine.stats.units_recruited[Player.ONE] -= 1
                self._event("unit_returned", Player.ONE, actor.name, amount=actor.cost)
            else:
                try:
                    lane = Lane(command.get("lane"))
                except (ValueError, TypeError):
                    raise ValueError("Escolha uma linha válida.") from None
                if lane == actor.lane:
                    raise ValueError("A unidade já está nessa linha.")
                actor.lane = lane
                self._event("unit_deployed", Player.ONE, actor.name, lane=lane.value)
        elif kind == "begin" and self.phase == "recruit":
            self._begin_combat()
        elif kind == "act" and self.phase == "combat":
            actor = next(
                (t for t in self._ready(Player.ONE) if t.name == command.get("actor")), None
            )
            choice = {k: command[k] for k in ("action", "target", "lane") if k in command}
            if actor is None or choice not in self._choices(Player.ONE, actor):
                raise ValueError(
                    "Essa ordem não está disponível. Escolha uma unidade pronta e um alvo válido."
                )
            self._act(Player.ONE, actor, choice)
            if not self._check_finished():
                self._enemy_response()
        elif kind == "next" and self.phase == "review":
            self.engine.round_number += 1
            self.acted.clear()
            self.phase = "recruit"
            self._event("round_started")
            self.engine.events.extend(self.engine._apply_start_of_round_effects())
        else:
            raise ValueError("Esse comando não está disponível nesta fase.")
        self.commands.append(dict(command))
        return self.state()

    def _recruit(self, player: Player, kind: TroopKind, lane: Lane | None) -> None:
        self.engine.events.extend(
            self.engine._apply_recruit_orders(
                player,
                TurnPlan(recruits=(RecruitOrder(kind, lane=lane),)),
            )
        )

    def _begin_combat(self) -> None:
        self.refundable.clear()
        plan = self.bot.choose_plan(Player.TWO, self.field)
        for order in plan.recruits:
            for _ in range(order.quantity):
                if len(self.field.troops_two) >= self.roster_limit:
                    break
                if self.field.base_two.can_afford(TROOP_COSTS[order.troop_kind]):
                    self._recruit(Player.TWO, order.troop_kind, order.lane)
        self.phase = "combat"
        for player in Player:
            for troop in self.field.living_troops_for(player):
                if troop.has_effect(StatusEffect.STUN):
                    troop.effects.pop(StatusEffect.STUN)
                    self.acted.add(troop.name)
                    self._event("unit_stunned", player, troop.name)
        if self.opener == Player.TWO or not self._ready(Player.ONE):
            self._enemy_response()

    @property
    def opener(self) -> Player:
        first = self.engine.opening_initiative
        return first if self.engine.round_number % 2 else first.opponent

    def _ready(self, player: Player) -> list[Troop]:
        return [t for t in self.field.living_troops_for(player) if t.name not in self.acted]

    def _reachable(self, actor: Troop, enemy: Player) -> list[Troop]:
        """Alvos ao alcance, contando as fileiras a partir de onde o ator esta.

        A retaguarda sobe sozinha quando a frente cai, entao a regra antiga de
        "sem frente, todo mundo alcanca" virou consequencia da formacao em vez
        de excecao.
        """
        allies = self.field.living_troops_for(self.owner_of(actor))
        enemies = self.field.living_troops_for(enemy)
        return [t for t in enemies if can_strike(actor, allies, t, enemies)]

    def owner_of(self, actor: Troop) -> Player:
        return Player.ONE if actor in self.field.troops_one else Player.TWO

    def _choices(self, player: Player, actor: Troop) -> list[dict]:
        if actor.has_effect(StatusEffect.STUN):
            return [{"action": "wait"}]
        allies = self.field.living_troops_for(player)
        enemies = self.field.living_troops_for(player.opponent)
        # Arma recarregando nao golpeia nem conjura; proteger, reposicionar e
        # esperar continuam disponiveis, senao a rodada vira tempo morto.
        loaded = actor.is_loaded(self.engine.round_number)
        choices = [
            {"action": "attack", "target": t.name}
            for t in (self._reachable(actor, player.opponent) if loaded else [])
        ]
        if loaded and not enemies:
            choices.append({"action": "attack", "target": "base"})
        choices.extend(
            [
                {"action": "guard", "target": actor.name},
                {"action": "move", "lane": "back" if actor.lane == Lane.FRONT else "front"},
                {"action": "wait"},
            ]
        )
        if actor.role == Role.SUPPORT and loaded:
            choices.extend(
                {"action": "heal", "target": t.name} for t in allies if t.health < t.max_hp
            )
        if actor.role == Role.DEFENDER:
            choices.extend({"action": "guard", "target": t.name} for t in allies if t is not actor)
        return choices

    def _act(self, player: Player, actor: Troop, choice: dict) -> None:
        self.acted.add(actor.name)
        action = choice["action"]
        if actor.has_effect(StatusEffect.STUN):
            actor.effects.pop(StatusEffect.STUN)
            self._event("unit_stunned", player, actor.name)
            return
        if action == "attack":
            target = choice["target"]
            if target == "base":
                base = self.field.base_for(player.opponent)
                amount = base.receive_damage(actor.attack)
                self._event("base_attack", player, actor.name, base.name, amount)
            else:
                enemy = next(
                    t for t in self.field.living_troops_for(player.opponent) if t.name == target
                )
                amount = enemy.receive_damage(actor.attack)
                self._event("unit_attack", player, actor.name, enemy.name, amount)
                if amount > 0 and enemy.is_alive:
                    self.engine.events.extend(
                        self.engine._apply_attack_effects(player, actor, enemy)
                    )
                    # A stun consumes one action, including a pending action this round.
                    if enemy.has_effect(StatusEffect.STUN) and enemy.name not in self.acted:
                        enemy.effects.pop(StatusEffect.STUN)
                        self.acted.add(enemy.name)
                        self._event("unit_stunned", player.opponent, enemy.name)
            actor.damage_dealt += amount
            actor.start_reload(self.engine.round_number)
            self.engine.stats.record_damage(player, amount)
        elif action in ("heal", "guard"):
            ally = next(
                t for t in self.field.living_troops_for(player) if t.name == choice["target"]
            )
            if action == "heal":
                self._event("heal", player, actor.name, ally.name, ally.heal(2))
                actor.start_reload(self.engine.round_number)
            else:
                ally.add_effect(StatusEffect.SHIELD, 2)
                self._event("shield", player, actor.name, ally.name)
        elif action == "move":
            actor.lane = Lane(choice["lane"])
            self._event("unit_moved", player, actor.name, lane=actor.lane.value)
        else:
            self._event("unit_waited", player, actor.name)
        self.engine.events.extend(self.field.remove_defeated(self.engine.round_number))

    def _enemy_response(self) -> None:
        while self.phase == "combat":
            ready = self._ready(Player.TWO)
            if ready:
                actor = max(ready, key=lambda t: (t.speed, t.attack))
                choice = self._enemy_choice(actor)
                self._act(Player.TWO, actor, choice)
                if self._check_finished():
                    return
            if self._ready(Player.ONE):
                return
            if not self._ready(Player.TWO):
                self._end_round()
                return

    def _enemy_choice(self, actor: Troop) -> dict:
        choices = self._choices(Player.TWO, actor)
        attacks = [c for c in choices if c["action"] == "attack"]
        heals = [c for c in choices if c["action"] == "heal"]
        enemies = {t.name: t for t in self.field.living_troops_for(Player.ONE)}
        allies = {t.name: t for t in self.field.living_troops_for(Player.TWO)}
        # Finish a vulnerable target before spending this action on support.
        lethal = [c for c in attacks if (
            self.field.base_one.health <= actor.attack if c["target"] == "base"
            else enemies[c["target"]].preview_damage(actor.attack) >= enemies[c["target"]].health
        )]
        if lethal:
            return lethal[0]
        if heals:
            return min(heals, key=lambda c: allies[c["target"]].health / allies[c["target"]].max_hp)
        # A shield is worthwhile when it saves an ally from a pending lethal hit.
        threats = [t for t in self._ready(Player.ONE) if t.is_loaded(self.engine.round_number)
                   and not t.has_effect(StatusEffect.STUN)]
        for choice in choices:
            if choice["action"] != "guard":
                continue
            target = allies[choice["target"]]
            if target.has_effect(StatusEffect.SHIELD):
                continue
            if any(can_strike(t, enemies.values(), target, allies.values())
                   and max(1, t.attack - target.defense) == target.health for t in threats):
                return choice
        if attacks:
            return min(attacks, key=lambda c: enemies[c["target"]].health if c["target"] != "base" else 0)
        move = {"action": "move", "lane": "front"}
        if actor.is_loaded(self.engine.round_number) and move in choices and enemies:
            return move
        guard = {"action": "guard", "target": actor.name}
        if guard in choices and not actor.has_effect(StatusEffect.SHIELD) and (
            actor.has_effect(StatusEffect.BLEED)
            or any(can_strike(t, enemies.values(), actor, allies.values()) for t in threats)
        ):
            return guard
        return {"action": "wait"}

    def _preview(self, actor: Troop, choice: dict) -> dict:
        preview = dict(choice)
        target_name = choice.get("target")
        if choice["action"] == "attack":
            if target_name == "base":
                target = self.field.base_two
                damage = min(target.health, actor.attack)
            else:
                target = next(t for t in self.field.troops_two if t.name == target_name)
                damage = target.preview_damage(actor.attack)
            preview.update(damage=damage, remaining_hp=target.health - damage,
                           defeats=damage >= target.health)
            effects = []
            if target_name != "base" and damage > 0 and damage < target.health:
                if actor.role == Role.RANGED:
                    effects.append("bleed")
                if actor.name.startswith("Tank"):
                    effects.append("stun")
            preview["effects"] = effects
        elif choice["action"] == "heal":
            target = next(t for t in self.field.troops_one if t.name == target_name)
            preview["healing"] = min(2, target.max_hp - target.health)
        return preview

    def _check_finished(self) -> bool:
        if self.field.base_one.is_destroyed or self.field.base_two.is_destroyed:
            self.winner = self.field.winner()
            self.reason = "base_destroyed"
            self.phase = "finished"
            self._event("match_finished", self.winner, reason=self.reason)
            self.engine.round_snapshots.append(self.engine._capture_round_snapshot())
            return True
        return False

    def _end_round(self) -> None:
        if self.engine.round_number >= self.max_rounds:
            self.winner = self.engine._tiebreak_winner()
            self.reason = "round_limit"
            self.phase = "finished"
            self._event("match_finished", self.winner, reason=self.reason)
        else:
            for player in Player:
                self.field.base_for(player).collect_resources()
            self.phase = "review"
            self._event("round_ended")
        self.engine.round_snapshots.append(self.engine._capture_round_snapshot())

    def state(self) -> dict:
        snapshot = self.engine._capture_round_snapshot()
        legal = {t.name: self._choices(Player.ONE, t) for t in self._ready(Player.ONE)} if self.phase == "combat" else {}
        snapshot.update(
            {
                "phase": self.phase,
                "max_rounds": self.max_rounds,
                "opponent": self.opponent,
                "seed": self.seed,
                "opener": self.opener.value,
                "winner": self.winner.value if self.winner else None,
                "reason": self.reason,
                "roster_limit": self.roster_limit,
                "acted": sorted(self.acted),
                "legal_actions": legal,
                "refundable": sorted(self.refundable),
                "formation_warnings": [
                    t.name for t in self.field.troops_one
                    if t.lane == Lane.BACK and t.range == 1
                    and any(ally.lane == Lane.FRONT for ally in self.field.troops_one)
                ],
                "action_previews": {
                    t.name: [self._preview(t, c) for c in legal[t.name]]
                    for t in self._ready(Player.ONE) if t.name in legal
                },
                "events": [event.to_dict() for event in self.engine.events],
            }
        )
        return snapshot

    def report(self) -> dict:
        return {
            "schema_version": 1,
            "mode": "interactive",
            "ruleset": self.ruleset,
            "config": {"opponent": self.opponent, "seed": self.seed, "max_rounds": self.max_rounds},
            "commands": self.commands,
            "state": self.state(),
            "round_snapshots": self.engine.round_snapshots,
        }
