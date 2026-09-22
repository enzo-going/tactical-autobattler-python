/* Replay presentation, driven by Python events and authoritative snapshots. */
globalThis.BattleReplay = {
  create(catalog) {
    const unitSpecs = Object.fromEntries(catalog.units.map(unit => [unit.kind, unit]));
    const EFFECT_DURATION = { bleed: 3, shield: 2, stun: 2 };
    function initialState() {
      return {
        round: 0,
        incomeThrough: 0,
        bases: {
          1: { hp: catalog.base_health, res: catalog.base_resources },
          2: { hp: catalog.base_health, res: catalog.base_resources },
        },
        units: new Map(),
      };
    }

    function collectIncome(state) {
      state.bases[1].res += catalog.base_income;
      state.bases[2].res += catalog.base_income;
    }

    function tickEffects(state) {
      state.units.forEach((unit) => {
        Object.keys(unit.effects).forEach((effect) => {
          unit.effects[effect] -= 1;
          if (unit.effects[effect] <= 0) delete unit.effects[effect];
        });
      });
    }

    function applyEvent(state, event) {
      const units = state.units;
      const target = event.target ? units.get(event.target) : null;
      const actor = event.actor ? units.get(event.actor) : null;

      switch (event.type) {
        case "round_started":
          if (event.round > 1) {
            if (state.incomeThrough < event.round - 1) {
              collectIncome(state);
              state.incomeThrough = event.round - 1;
            }
            tickEffects(state);
          }
          state.round = event.round;
          break;

        case "unit_recruited": {
          const kind = event.metadata.kind;
          const spec = unitSpecs[kind] || { max_hp: 1, attack: 0, defense: 0, speed: 0, range: 1, role: "assault" };
          state.bases[event.player].res -= event.amount;
          units.set(event.actor, {
            name: event.actor,
            kind,
            owner: event.player,
            lane: event.metadata.lane,
            role: spec.role,
            maxHp: spec.max_hp,
            hp: spec.max_hp,
            attack: spec.attack,
            defense: spec.defense,
            reload: spec.reload || 0,
            readyRound: 0,
            effects: {},
            alive: true,
            dealt: 0,
            kills: 0,
          });
          break;
        }

        case "unit_attack":
          if (target) {
            target.hp = Math.max(0, target.hp - event.amount);
            delete target.effects.shield;
            if (target.hp === 0 && actor) actor.kills += 1;
          }
          if (actor) {
            actor.dealt += event.amount;
            actor.readyRound = event.metadata.ready_round ?? actor.readyRound;
          }
          break;

        case "base_attack": {
          const defender = event.player === 1 ? 2 : 1;
          state.bases[defender].hp = Math.max(0, state.bases[defender].hp - event.amount);
          if (actor) {
            actor.dealt += event.amount;
            actor.readyRound = event.metadata.ready_round ?? actor.readyRound;
          }
          break;
        }

        case "unit_defeated":
          if (actor) actor.alive = false;
          break;

        case "effect_damage":
          if (target) {
            target.hp = Math.max(0, target.hp - event.amount);
            delete target.effects.shield;
          }
          break;

        case "effect_applied":
          if (target) target.effects[event.metadata.effect] = EFFECT_DURATION[event.metadata.effect] || 2;
          break;

        case "heal":
          if (target) target.hp = Math.min(target.maxHp, target.hp + event.amount);
          if (actor) actor.readyRound = event.metadata.ready_round ?? actor.readyRound;
          break;

        case "unit_moved":
          if (actor) actor.lane = event.metadata.lane;
          break;

        case "shield":
          if (target) target.effects.shield = EFFECT_DURATION.shield;
          break;

        case "unit_stunned":
          if (actor) delete actor.effects.stun;
          break;

        default:
          break;
      }
    }

    function stateFromSnapshot(snapshot) {
      const state = initialState();
      state.round = snapshot.round;
      state.incomeThrough = snapshot.round;

      [["player_one", 1], ["player_two", 2]].forEach(([key, owner]) => {
        state.bases[owner] = {
          hp: snapshot.bases[key].health,
          res: snapshot.bases[key].resources,
        };
        snapshot.troops[key].forEach((troop) => {
          const kind = troop.name.split(" ")[0].toLowerCase();
          state.units.set(troop.name, {
            name: troop.name,
            kind,
            owner,
            lane: troop.lane,
            role: troop.role,
            maxHp: troop.max_hp,
            hp: troop.current_hp,
            attack: troop.attack,
            defense: troop.defense,
            reload: troop.reload || 0,
            readyRound: troop.ready_round ?? snapshot.round + (troop.reloading || 0),
            effects: { ...troop.effects },
            alive: true,
            dealt: troop.damage_dealt,
            kills: 0,
          });
        });
      });
      return state;
    }

    /** Estado depois de `count` eventos, retomando do snapshot mais proximo quando existir. */
    function buildState(events, count, snapshots = []) {
      const snapshot = [...snapshots]
        .reverse()
        .find((candidate) => candidate.event_count <= count);
      const state = snapshot ? stateFromSnapshot(snapshot) : initialState();
      const start = snapshot ? snapshot.event_count : 0;

      for (let index = start; index < count; index += 1) applyEvent(state, events[index]);
      if (count >= events.length && state.incomeThrough < state.round) {
        collectIncome(state);
        state.incomeThrough = state.round;
      }
      return state;
    }

    return { initialState, applyEvent, buildState };
  },
};
