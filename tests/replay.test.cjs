const assert = require("node:assert/strict");
const { test } = require("node:test");
const { spawnSync } = require("node:child_process");
const path = require("node:path");
require("../web/replay-state.js");

// Compare the real presentation code with snapshots produced by the real engine.
const result = spawnSync(process.env.PYTHON || "python", ["-c", `
import json
from web import playground
from battle_simulator.engine import BattleEngine, Player, TurnPlan, RecruitOrder, AttackOrder
from battle_simulator.models import TroopKind, Lane
from battle_simulator.cli import _build_report
reports = [json.loads(playground.battle(a, b, 12, 11)) for a, b in [
    ("balanced", "economy"), ("random", "defensive"), ("aggressive", "balanced")
]]
engine = BattleEngine()
engine.play_round({
    Player.ONE: TurnPlan(recruits=(RecruitOrder(TroopKind.GUARDIAN), RecruitOrder(TroopKind.SOLDIER, lane=Lane.BACK))),
    Player.TWO: TurnPlan(recruits=(RecruitOrder(TroopKind.GUARDIAN),)),
})
engine.play_round({Player.ONE: TurnPlan(attacks=(AttackOrder(1, 0),))})
reports.append({"events": [e.to_dict() for e in engine.events], "round_snapshots": engine.round_snapshots})
print(json.dumps({"catalog": json.loads(playground.catalog()), "reports": reports}))
`], { cwd: path.join(__dirname, ".."), encoding: "utf8", maxBuffer: 10 * 1024 * 1024 });
assert.equal(result.status, 0, result.stderr);
const { catalog, reports } = JSON.parse(result.stdout);
const model = BattleReplay.create(catalog);
const sorted = (rows) => rows.sort((a, b) => a.name.localeCompare(b.name));
const troopView = (state) => sorted([...state.units.values()].filter(t => t.alive).map(t => ({
  name: t.name, lane: t.lane, hp: t.hp, effects: t.effects,
  readyRound: t.readyRound, dealt: t.dealt,
})));

test("playback agrees with Python after movement, damage, effects, healing and reload", () => {
  const types = new Set(reports.flatMap(r => r.events.map(e => e.type)));
  for (const type of ["unit_moved", "heal", "reloading", "effect_damage", "unit_defeated"])
    assert.ok(types.has(type), `Fixture must exercise ${type}`);
  for (const report of reports) {
    for (const snapshot of report.round_snapshots) {
      const expected = sorted(Object.values(snapshot.troops).flat().map(t => ({
        name: t.name, lane: t.lane, hp: t.current_hp, effects: t.effects,
        readyRound: t.ready_round, dealt: t.damage_dealt,
      })));
      assert.deepEqual(troopView(model.buildState(report.events, snapshot.event_count)), expected,
        `Sequential playback at round ${snapshot.round}`);
    }
  }
});

test("seeking from a snapshot gives the same troops as continuous playback", () => {
  for (const report of reports) {
    for (let count = 0; count <= report.events.length; count++) {
      assert.deepEqual(
        troopView(model.buildState(report.events, count, report.round_snapshots)),
        troopView(model.buildState(report.events, count)),
        `Seek at event ${count}`,
      );
    }
  }
});
