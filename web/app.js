/*
 * Interface web do Tactical Auto-Battler.
 *
 * Toda regra de jogo vive no pacote Python `battle_simulator`, carregado no
 * Pyodide. Este arquivo cuida de tres coisas:
 *
 *   1. montar os controles a partir do catalogo devolvido por playground.py;
 *   2. reconstruir o campo de batalha rodada a rodada a partir da lista de
 *      eventos do relatorio -- nenhuma regra e recalculada aqui, os eventos ja
 *      trazem quanto dano foi aplicado, quem morreu e quem foi recrutado;
 *   3. animar essa reconstrucao na arena e traduzir tudo para pt-BR.
 */

const MODULES = [
  "__init__.py",
  "models.py",
  "engine.py",
  "strategies.py",
  "tournament.py",
  "cli.py",
];

/* ------------------------------------------------------------------ *
 * Tabelas de apresentacao
 * ------------------------------------------------------------------ */

const COMMANDERS = {
  aggressive: {
    name: "Agressiva",
    className: "AggressiveBot",
    emblem: "🔥",
    tagline: "Compra pouco, mira sempre no alvo mais fraco ao alcance e tenta fechar a partida antes do meio do jogo.",
    traits: { Agressão: 5, Defesa: 1, Economia: 2 },
  },
  balanced: {
    name: "Equilibrada",
    className: "BalancedBot",
    emblem: "⚖️",
    tagline: "Monta composição completa: um defensor, alcance no fundo, suporte e o que sobrar vira linha de frente.",
    traits: { Agressão: 3, Defesa: 3, Economia: 3 },
  },
  defensive: {
    name: "Defensiva",
    className: "DefensiveBot",
    emblem: "🛡️",
    tagline: "Guardião na frente, arqueiros atrás e Médico assim que a tropa apanha. Ganha no desgaste.",
    traits: { Agressão: 2, Defesa: 5, Economia: 2 },
  },
  economy: {
    name: "Econômica",
    className: "EconomyBot",
    emblem: "💰",
    tagline: "Segura recursos por rodadas seguidas para comprar Tanque e Arqueiro juntos mais tarde.",
    traits: { Agressão: 2, Defesa: 2, Economia: 5 },
  },
  random: {
    name: "Aleatória",
    className: "RandomBot",
    emblem: "🎲",
    tagline: "Compra e mira por sorteio com seed. É a única estratégia em que mudar a seed muda a batalha.",
    traits: { Agressão: 3, Defesa: 3, Economia: 1 },
  },
};

const UNITS = {
  soldier: { name: "Soldado", icon: "🗡️" },
  archer: { name: "Arqueiro", icon: "🏹" },
  guardian: { name: "Guardião", icon: "🛡️" },
  medic: { name: "Médico", icon: "➕" },
  tank: { name: "Tanque", icon: "🪓" },
};

const ROLE_PT = { assault: "Assalto", defender: "Defensor", ranged: "Alcance", support: "Suporte" };
const LANE_PT = { front: "frente", back: "fundo" };
const EFFECT_PT = { bleed: "sangramento", shield: "escudo", stun: "atordoamento" };
const EFFECT_ICON = { bleed: "🩸", shield: "🛡️", stun: "💫" };
const EFFECT_DURATION = { bleed: 3, shield: 2, stun: 2 };
const SIDE_PT = { 1: "Azul", 2: "Vermelho" };
const SIDE_COLOR = { 1: "#4d9dff", 2: "#ff5566" };

const EVENT_ICON = {
  unit_recruited: "➕",
  unit_attack: "⚔️",
  base_attack: "🏰",
  unit_defeated: "☠️",
  effect_damage: "🩸",
  effect_applied: "✨",
  heal: "💚",
  shield: "🛡️",
  unit_stunned: "💫",
  out_of_range: "🚫",
  invalid_target: "🚫",
  invalid_recruit: "⚠️",
  tiebreak: "⚖️",
};

/** Duracao base de cada evento no replay, em ms, antes de dividir pela velocidade. */
const STEP_MS = {
  round_started: 620,
  unit_recruited: 230,
  unit_attack: 380,
  base_attack: 480,
  unit_defeated: 300,
  effect_damage: 240,
  effect_applied: 150,
  heal: 320,
  shield: 260,
  unit_stunned: 240,
  out_of_range: 110,
  invalid_target: 110,
  invalid_recruit: 110,
  tiebreak: 800,
};

const SPEEDS = [1, 2, 4, 8];
const TICKER_LIMIT = 30;

/* ------------------------------------------------------------------ *
 * Utilidades
 * ------------------------------------------------------------------ */

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (ch) => (
    { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch]
  ));
}

/** "Archer 3" -> {kind: "archer", label: "Arqueiro 3"} */
function parseUnitName(name) {
  const match = /^([A-Za-z]+)\s*(\d*)$/.exec(String(name || ""));
  if (!match) return { kind: null, label: String(name || "") };
  const kind = match[1].toLowerCase();
  const unit = UNITS[kind];
  if (!unit) return { kind: null, label: String(name) };
  return { kind, label: match[2] ? `${unit.name} ${match[2]}` : unit.name };
}

function unitLabel(name) {
  return parseUnitName(name).label;
}

function unitIcon(name) {
  const kind = parseUnitName(name).kind;
  return kind ? UNITS[kind].icon : "•";
}

function commanderOf(key) {
  return COMMANDERS[key] || { name: key, className: key, emblem: "•", tagline: "", traits: {} };
}

function clampInput(input) {
  const value = Number(input.value);
  const min = Number(input.min);
  const max = Number(input.max);
  if (!Number.isFinite(value)) return min;
  const clamped = Math.min(max, Math.max(min, Math.round(value)));
  input.value = String(clamped);
  return clamped;
}

/** Deixa o navegador pintar o estado "rodando" antes de travar no Python. */
function nextFrame() {
  return new Promise((resolve) => setTimeout(resolve, 30));
}

function barLevel(ratio) {
  return ratio <= 0.25 ? "bar critical" : ratio <= 0.5 ? "bar low" : "bar";
}

function downloadJson(data, filename) {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

/* ------------------------------------------------------------------ *
 * Boot do Pyodide
 * ------------------------------------------------------------------ */

let pyodide = null;
let bridge = null;
let catalog = null;
let unitSpecs = {};

const bootBox = document.getElementById("boot");
const bootMsg = document.getElementById("boot-msg");

async function boot() {
  try {
    bootMsg.textContent = "Carregando o interpretador Python (~10 MB, só na primeira visita)…";
    pyodide = await loadPyodide();

    bootMsg.textContent = "Carregando o pacote battle_simulator…";
    pyodide.FS.mkdirTree("/app/battle_simulator");

    const sources = await Promise.all(
      MODULES.map((name) =>
        fetch(`battle_simulator/${name}`).then((response) => {
          if (!response.ok) throw new Error(`Falha ao baixar ${name} (HTTP ${response.status})`);
          return response.text();
        })
      )
    );
    MODULES.forEach((name, index) => {
      pyodide.FS.writeFile(`/app/battle_simulator/${name}`, sources[index]);
    });

    const bridgeSource = await fetch("playground.py").then((response) => response.text());
    pyodide.FS.writeFile("/app/playground.py", bridgeSource);

    bridge = await pyodide.runPythonAsync(`
import sys
sys.path.insert(0, "/app")
import playground
playground
`);

    catalog = JSON.parse(bridge.catalog());
    catalog.units.forEach((unit) => { unitSpecs[unit.kind] = unit; });

    buildDeployScreen();
    buildRoster();
    buildManual();

    document.getElementById("b-run").disabled = false;
    document.getElementById("t-run").disabled = false;
    bootBox.classList.add("done");
  } catch (error) {
    bootBox.classList.add("error");
    bootBox.innerHTML = `<span>⚠️</span><span>Não foi possível iniciar o Python no navegador: ${escapeHtml(error.message)}</span>`;
  }
}

/* ------------------------------------------------------------------ *
 * Abas
 * ------------------------------------------------------------------ */

function wireTabs() {
  const buttons = [...document.querySelectorAll(".tab")];
  buttons.forEach((button) => {
    button.addEventListener("click", () => {
      buttons.forEach((other) => {
        const selected = other === button;
        other.setAttribute("aria-selected", String(selected));
        document.getElementById(other.dataset.panel).hidden = !selected;
      });
    });
  });
}

/* ------------------------------------------------------------------ *
 * Tela de deploy
 * ------------------------------------------------------------------ */

const picked = { 1: "balanced", 2: "random" };

function buildDeployScreen() {
  [1, 2].forEach((side) => {
    const card = document.getElementById(`cmd-${side}`);
    const slots = card.querySelector('[data-slot="slots"]');
    slots.innerHTML = "";

    catalog.strategies.forEach((key) => {
      const commander = commanderOf(key);
      const slot = el("button", "commander-slot", commander.emblem);
      slot.type = "button";
      slot.title = commander.name;
      slot.dataset.key = key;
      slot.setAttribute("aria-pressed", String(picked[side] === key));
      slot.addEventListener("click", () => {
        picked[side] = key;
        paintCommander(side);
      });
      slots.appendChild(slot);
    });

    if (!catalog.strategies.includes(picked[side])) picked[side] = catalog.strategies[0];
    paintCommander(side);
  });
}

function paintCommander(side) {
  const card = document.getElementById(`cmd-${side}`);
  const commander = commanderOf(picked[side]);

  card.querySelector('[data-slot="emblem"]').textContent = commander.emblem;
  card.querySelector('[data-slot="name"]').textContent = commander.name;
  card.querySelector('[data-slot="kind"]').textContent = commander.className;
  card.querySelector('[data-slot="class"]').textContent = `#${picked[side]}`;
  card.querySelector('[data-slot="tagline"]').textContent = commander.tagline;

  const traits = card.querySelector('[data-slot="traits"]');
  traits.innerHTML = "";
  Object.entries(commander.traits).forEach(([label, value]) => {
    const row = el("div", "trait");
    row.appendChild(el("span", null, label));
    const pips = el("div", "pips");
    for (let index = 1; index <= 5; index += 1) pips.appendChild(el("i", index <= value ? "on" : null));
    row.appendChild(pips);
    traits.appendChild(row);
  });

  card.querySelectorAll(".commander-slot").forEach((slot) => {
    slot.setAttribute("aria-pressed", String(slot.dataset.key === picked[side]));
  });
}

/* ------------------------------------------------------------------ *
 * Reconstrucao do campo de batalha a partir dos eventos
 * ------------------------------------------------------------------ */

function initialState() {
  return {
    round: 0,
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
        collectIncome(state);
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
      if (actor) actor.dealt += event.amount;
      break;

    case "base_attack": {
      const defender = event.player === 1 ? 2 : 1;
      state.bases[defender].hp = Math.max(0, state.bases[defender].hp - event.amount);
      if (actor) actor.dealt += event.amount;
      break;
    }

    case "unit_defeated":
      if (actor) actor.alive = false;
      break;

    case "effect_damage":
      if (target) target.hp = Math.max(0, target.hp - event.amount);
      break;

    case "effect_applied":
      if (target) target.effects[event.metadata.effect] = EFFECT_DURATION[event.metadata.effect] || 2;
      break;

    case "heal":
      if (target) target.hp = Math.min(target.maxHp, target.hp + event.amount);
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

/** Estado do campo depois de aplicar os `count` primeiros eventos. */
function buildState(events, count) {
  const state = initialState();
  for (let index = 0; index < count; index += 1) applyEvent(state, events[index]);
  if (count >= events.length) collectIncome(state);
  return state;
}

/* ------------------------------------------------------------------ *
 * Arena
 * ------------------------------------------------------------------ */

const arena = document.getElementById("arena");
const fxLayer = document.getElementById("fx-layer");
const roundBanner = document.getElementById("round-banner");
const ticker = document.getElementById("ticker");
const nodesByUnit = new Map();

function laneBox(owner, lane) {
  return document.getElementById(`lane-${owner}-${lane}`);
}

function makeUnitNode(unit) {
  const node = el("div", "unit");
  node.dataset.name = unit.name;

  node.appendChild(el("div", "unit-icon", UNITS[unit.kind] ? UNITS[unit.kind].icon : "•"));

  const info = el("div", "unit-info");
  const top = el("div", "unit-top");
  top.appendChild(el("span", "unit-name", unitLabel(unit.name)));
  top.appendChild(el("span", "unit-hp"));
  info.appendChild(top);

  const bar = el("div", "bar");
  bar.appendChild(el("span"));
  info.appendChild(bar);
  node.appendChild(info);

  node.appendChild(el("div", "unit-fx"));
  return node;
}

function paintUnitNode(node, unit) {
  const ratio = unit.hp / unit.maxHp;
  node.querySelector(".unit-hp").textContent = `${unit.hp}/${unit.maxHp}`;
  const bar = node.querySelector(".bar");
  bar.className = barLevel(ratio);
  bar.firstChild.style.width = `${Math.max(0, ratio) * 100}%`;
  node.title = `${ROLE_PT[unit.role] || unit.role} · linha de ${LANE_PT[unit.lane] || unit.lane} · ${unit.attack} ATQ / ${unit.defense} DEF`;

  const fx = node.querySelector(".unit-fx");
  const effects = Object.keys(unit.effects);
  fx.innerHTML = "";
  effects.forEach((effect) => {
    const badge = el("i", null, EFFECT_ICON[effect] || "✨");
    badge.title = EFFECT_PT[effect] || effect;
    fx.appendChild(badge);
  });
}

function renderBoard(state, animate) {
  nodesByUnit.clear();

  [1, 2].forEach((owner) => {
    ["front", "back"].forEach((lane) => {
      const box = laneBox(owner, lane);
      const wanted = [...state.units.values()].filter(
        (unit) => unit.alive && unit.owner === owner && unit.lane === lane
      );
      const wantedNames = new Set(wanted.map((unit) => unit.name));

      box.querySelectorAll(".unit").forEach((node) => {
        if (wantedNames.has(node.dataset.name)) return;
        if (animate) {
          if (!node.classList.contains("dying")) {
            node.classList.add("dying");
            setTimeout(() => node.remove(), 340);
          }
        } else {
          node.remove();
        }
      });

      wanted.forEach((unit) => {
        let node = box.querySelector(`.unit[data-name="${unit.name}"]:not(.dying)`);
        if (!node) {
          node = makeUnitNode(unit);
          if (animate) node.classList.add("spawn");
          box.appendChild(node);
          if (animate) box.scrollTop = box.scrollHeight;
        }
        paintUnitNode(node, unit);
        nodesByUnit.set(unit.name, node);
      });

      const empty = box.querySelector(".lane-empty");
      if (wanted.length === 0 && !empty) {
        box.appendChild(el("div", "lane-empty", "vazio"));
      } else if (wanted.length > 0 && empty) {
        empty.remove();
      }
    });
  });

  renderForts(state);
}

function renderForts(state) {
  [1, 2].forEach((side) => {
    const fort = document.getElementById(`fort-${side}`);
    const base = state.bases[side];
    const ratio = base.hp / catalog.base_health;
    fort.querySelector('[data-slot="hp"]').textContent = `${base.hp}/${catalog.base_health}`;
    fort.querySelector('[data-slot="res"]').textContent = Math.max(0, base.res);
    const fill = fort.querySelector('[data-slot="bar"]');
    fill.parentElement.className = barLevel(ratio);
    fill.style.width = `${Math.max(0, ratio) * 100}%`;
  });

  document.getElementById("round-now").textContent = state.round;
}

/* ---------- efeitos visuais ---------- */

function pulse(node, className, duration) {
  if (!node) return;
  node.classList.remove(className);
  void node.offsetWidth;
  node.classList.add(className);
  setTimeout(() => node.classList.remove(className), duration);
}

function floatText(node, text, kind) {
  if (!node) return;
  const badge = el("span", `float${kind ? " " + kind : ""}`, text);
  node.appendChild(badge);
  setTimeout(() => badge.remove(), 900);
}

function centerOf(node) {
  const box = node.getBoundingClientRect();
  return { x: box.left + box.width / 2, y: box.top + box.height / 2 };
}

function tracer(fromNode, toNode, color) {
  if (!fromNode || !toNode) return;
  const layer = fxLayer.getBoundingClientRect();
  const from = centerOf(fromNode);
  const to = centerOf(toNode);
  const dx = to.x - from.x;
  const dy = to.y - from.y;
  const length = Math.hypot(dx, dy);
  if (!length) return;

  const beam = el("div", "tracer");
  beam.style.left = `${from.x - layer.left}px`;
  beam.style.top = `${from.y - layer.top}px`;
  beam.style.width = `${length}px`;
  beam.style.transform = `rotate(${(Math.atan2(dy, dx) * 180) / Math.PI}deg)`;
  beam.style.setProperty("--tracer", color);
  fxLayer.appendChild(beam);
  setTimeout(() => beam.remove(), 420);
}

function lunge(node, owner) {
  pulse(node, owner === 1 ? "acting-right" : "acting-left", 340);
}

function animateEvent(event) {
  const actorNode = event.actor ? nodesByUnit.get(event.actor) : null;
  const targetNode = event.target ? nodesByUnit.get(event.target) : null;
  const color = SIDE_COLOR[event.player] || "#f5c451";

  switch (event.type) {
    case "round_started":
      if (replay.speed <= 2) {
        roundBanner.firstElementChild.textContent = `Rodada ${event.round}`;
        pulse(roundBanner, "show", 1000);
      }
      break;

    case "unit_attack":
      lunge(actorNode, event.player);
      tracer(actorNode, targetNode, color);
      pulse(targetNode, "hurt", 340);
      floatText(targetNode, `-${event.amount}`);
      break;

    case "base_attack": {
      const fort = document.getElementById(`fort-${event.player === 1 ? 2 : 1}`);
      lunge(actorNode, event.player);
      tracer(actorNode, fort, color);
      pulse(fort, "hit", 460);
      pulse(arena, "shake", 420);
      floatText(fort, `-${event.amount}`);
      break;
    }

    case "effect_damage":
      pulse(targetNode, "hurt", 340);
      floatText(targetNode, `-${event.amount}`, "bleed");
      break;

    case "heal":
      pulse(targetNode, "healed", 560);
      floatText(targetNode, `+${event.amount}`, "heal");
      break;

    case "shield":
      pulse(targetNode, "shielded", 600);
      break;

    case "unit_stunned":
      pulse(actorNode, "stunned", 600);
      break;

    default:
      break;
  }
}

/* ------------------------------------------------------------------ *
 * Narracao dos eventos
 * ------------------------------------------------------------------ */

/** Traduz um evento do motor; devolve null para eventos que nao viram linha. */
function describe(event) {
  const actor = unitLabel(event.actor);
  const target = unitLabel(event.target);
  const side = SIDE_PT[event.player];

  switch (event.type) {
    case "round_started":
      return null;
    case "unit_recruited":
      return `${side} recrutou <b>${actor}</b> na linha de ${LANE_PT[event.metadata.lane] || event.metadata.lane} por ${event.amount} recursos`;
    case "unit_attack":
      return `${actor} atacou ${target} causando <span class="amt">${event.amount}</span> de dano`;
    case "base_attack":
      return `${actor} atingiu a base ${SIDE_PT[event.player === 1 ? 2 : 1]} causando <span class="amt">${event.amount}</span> de dano`;
    case "unit_defeated":
      return `${actor} foi derrotado`;
    case "effect_damage":
      return `${target} sofreu <span class="amt">${event.amount}</span> de ${EFFECT_PT[event.actor] || event.actor}`;
    case "effect_applied":
      return `${actor} aplicou ${EFFECT_PT[event.metadata.effect] || event.metadata.effect} em ${target}`;
    case "heal":
      return `${actor} curou ${target} em <span class="amt">${event.amount}</span> de HP`;
    case "shield":
      return `${actor} protegeu ${target} com escudo`;
    case "unit_stunned":
      return `${actor} está atordoado e perde a ação`;
    case "out_of_range":
      return `${actor} não tem alvo ao alcance`;
    case "invalid_target":
      return `${actor} recebeu um alvo inválido`;
    case "invalid_recruit":
      return "Recrutamento cancelado por falta de recursos";
    case "tiebreak":
      return `Limite de rodadas atingido — vitória ${side} no desempate`;
    default:
      return escapeHtml(event.message || event.type);
  }
}

function entryNode(event, className) {
  const text = describe(event);
  if (text === null) return null;
  const side = event.player === 1 ? "p1" : event.player === 2 ? "p2" : "";
  const line = el("div", `${className} ${side}`.trim());
  line.appendChild(el("span", "ic", EVENT_ICON[event.type] || "·"));
  const body = el("span");
  body.innerHTML = text;
  line.appendChild(body);
  return line;
}

function pushTicker(event) {
  const line = entryNode(event, "entry");
  if (!line) return;
  ticker.appendChild(line);
  while (ticker.children.length > TICKER_LIMIT) ticker.firstChild.remove();
}

function rebuildTicker(events, count) {
  ticker.innerHTML = "";
  if (count === 0) {
    ticker.appendChild(el("div", "idle", "Aguardando o primeiro movimento…"));
    return;
  }
  for (let index = Math.max(0, count - TICKER_LIMIT); index < count; index += 1) {
    pushTicker(events[index]);
  }
}

function renderFullLog(events) {
  const log = document.getElementById("full-log");
  log.innerHTML = "";
  let currentRound = null;

  events.forEach((event) => {
    if (event.round !== currentRound) {
      currentRound = event.round;
      log.appendChild(el("div", "round-head", `Rodada ${currentRound}`));
    }
    const line = entryNode(event, "entry");
    if (line) log.appendChild(line);
  });
}

/* ------------------------------------------------------------------ *
 * Replay
 * ------------------------------------------------------------------ */

const replay = {
  report: null,
  events: [],
  state: null,
  index: 0,
  playing: false,
  speed: 2,
  timer: null,
};

const transport = {
  play: document.getElementById("t-play"),
  restart: document.getElementById("t-restart"),
  speed: document.getElementById("t-speed"),
  round: document.getElementById("t-round"),
  end: document.getElementById("t-end"),
  scrub: document.getElementById("t-scrub"),
  counter: document.getElementById("t-counter"),
};

function startReplay(report) {
  replay.report = report;
  replay.events = report.events;
  replay.index = 0;
  replay.state = initialState();

  document.getElementById("round-phase").textContent = ` / ${report.rounds_played}`;
  [1, 2].forEach((side) => {
    const key = side === 1 ? "player_one" : "player_two";
    const commander = commanderOf(report.strategies[key]);
    document.getElementById(`fort-${side}`).querySelector('[data-slot="strategy"]').textContent =
      `${commander.emblem} ${commander.name}`;
  });

  transport.scrub.max = String(replay.events.length);
  hideVictory();
  renderFullLog(replay.events);
  document.getElementById("json-view").textContent = JSON.stringify(report, null, 2);

  seek(0);
  play();
}

function updateTransport() {
  transport.counter.textContent = `${replay.index} / ${replay.events.length}`;
  transport.scrub.value = String(replay.index);
  const progress = replay.events.length ? (replay.index / replay.events.length) * 100 : 0;
  transport.scrub.style.setProperty("--progress", `${progress}%`);
  transport.play.textContent = replay.playing ? "⏸" : "▶";
  transport.speed.textContent = `${replay.speed}×`;
}

function seek(count) {
  const target = Math.max(0, Math.min(replay.events.length, count));
  replay.index = target;
  replay.state = buildState(replay.events, target);
  renderBoard(replay.state, false);
  rebuildTicker(replay.events, target);
  updateTransport();
  if (target >= replay.events.length) showVictory(); else hideVictory();
}

function step() {
  if (replay.index >= replay.events.length) {
    pause();
    showVictory();
    return 0;
  }

  const event = replay.events[replay.index];
  applyEvent(replay.state, event);
  replay.index += 1;
  renderBoard(replay.state, true);
  animateEvent(event);
  pushTicker(event);
  updateTransport();

  if (replay.index >= replay.events.length) {
    collectIncome(replay.state);
    renderForts(replay.state);
  }

  return Math.max(16, (STEP_MS[event.type] || 220) / replay.speed);
}

function tick() {
  const delay = step();
  if (!replay.playing) return;
  if (replay.index >= replay.events.length) {
    pause();
    showVictory();
    return;
  }
  replay.timer = setTimeout(tick, delay);
}

function play() {
  // No fim da linha do tempo o botao de play vira "rever": volta ao inicio.
  if (replay.index >= replay.events.length) seek(0);
  if (!replay.events.length) return;
  replay.playing = true;
  updateTransport();
  clearTimeout(replay.timer);
  replay.timer = setTimeout(tick, 260);
}

function pause() {
  replay.playing = false;
  clearTimeout(replay.timer);
  updateTransport();
}

function jumpToNextRound() {
  const events = replay.events;
  for (let index = replay.index; index < events.length; index += 1) {
    if (events[index].type === "round_started" && index > replay.index) {
      seek(index);
      return;
    }
  }
  seek(events.length);
}

/* ---------- desfecho ---------- */

function mvpOf(state) {
  let best = null;
  state.units.forEach((unit) => {
    if (!best || unit.dealt > best.dealt) best = unit;
  });
  return best && best.dealt > 0 ? best : null;
}

function hideVictory() {
  document.getElementById("victory").classList.remove("show");
}

function showVictory() {
  const report = replay.report;
  if (!report) return;

  const box = document.getElementById("victory");
  const winner = report.winner;
  const side = winner === "Blue" ? 1 : winner === "Red" ? 2 : null;
  const byTiebreak = report.events.some((event) => event.type === "tiebreak");
  const finalState = buildState(replay.events, replay.events.length);
  const mvp = mvpOf(finalState);

  box.style.setProperty("--faction", side ? SIDE_COLOR[side] : "#f5c451");
  box.innerHTML = "";

  const inner = el("div", "victory-inner");
  inner.appendChild(el("div", "crown", side ? "👑" : "🤝"));

  const heading = el("h2");
  if (side) {
    heading.appendChild(document.createTextNode("Vitória "));
    heading.appendChild(el("span", "who", SIDE_PT[side]));
  } else {
    heading.appendChild(el("span", "who", "Empate"));
  }
  inner.appendChild(heading);

  const one = commanderOf(report.strategies.player_one);
  const two = commanderOf(report.strategies.player_two);
  inner.appendChild(
    el(
      "div",
      "subtitle",
      `${one.emblem} ${one.name} × ${two.emblem} ${two.name}${byTiebreak ? " · decidido no desempate" : ""}`
    )
  );

  const stats = el("div", "victory-stats");
  stats.appendChild(vstat("Rodadas", report.rounds_played));
  stats.appendChild(vstat("Dano Azul", report.damage.player_one.dealt));
  stats.appendChild(vstat("Dano Vermelho", report.damage.player_two.dealt));
  stats.appendChild(
    vstat(
      "Destaque",
      mvp ? `${unitIcon(mvp.name)} ${unitLabel(mvp.name)}` : "—",
      mvp ? `${mvp.dealt} de dano · ${mvp.kills} abate(s)` : null
    )
  );
  inner.appendChild(stats);

  const actions = el("div", "victory-actions");
  const again = el("button", "btn primary", "Nova batalha");
  again.addEventListener("click", backToDeploy);
  const rewatch = el("button", "btn", "Rever batalha");
  rewatch.addEventListener("click", () => { seek(0); play(); });
  actions.appendChild(again);
  actions.appendChild(rewatch);
  inner.appendChild(actions);

  box.appendChild(inner);
  box.classList.add("show");
}

function vstat(key, value, hint) {
  const box = el("div", "vstat");
  box.appendChild(el("div", "k", key));
  const line = el("div", "v", String(value));
  if (hint) {
    line.appendChild(document.createElement("br"));
    line.appendChild(el("small", null, hint));
  }
  box.appendChild(line);
  return box;
}

/* ------------------------------------------------------------------ *
 * Rodar a batalha
 * ------------------------------------------------------------------ */

function backToDeploy() {
  pause();
  hideVictory();
  document.getElementById("battle-screen").hidden = true;
  document.getElementById("deploy-screen").hidden = false;
}

async function runBattle() {
  const button = document.getElementById("b-run");
  const rounds = clampInput(document.getElementById("b-rounds"));
  const seed = clampInput(document.getElementById("b-seed"));

  button.disabled = true;
  button.textContent = "Convocando as tropas…";
  await nextFrame();

  try {
    const report = JSON.parse(bridge.battle(picked[1], picked[2], rounds, seed));
    document.getElementById("deploy-screen").hidden = true;
    document.getElementById("battle-screen").hidden = false;
    startReplay(report);
  } catch (error) {
    bootBox.classList.remove("done");
    bootBox.classList.add("error");
    bootBox.innerHTML = `<span>⚠️</span><span>Erro na simulação: ${escapeHtml(error.message)}</span>`;
  } finally {
    button.disabled = false;
    button.textContent = "Iniciar batalha";
  }
}

function wireTransport() {
  transport.play.addEventListener("click", () => (replay.playing ? pause() : play()));
  transport.restart.addEventListener("click", () => { seek(0); play(); });
  transport.end.addEventListener("click", () => { pause(); seek(replay.events.length); });
  transport.round.addEventListener("click", () => { pause(); jumpToNextRound(); });
  transport.speed.addEventListener("click", () => {
    replay.speed = SPEEDS[(SPEEDS.indexOf(replay.speed) + 1) % SPEEDS.length];
    updateTransport();
  });
  transport.scrub.addEventListener("input", () => {
    pause();
    seek(Number(transport.scrub.value));
  });

  document.getElementById("b-again").addEventListener("click", backToDeploy);
  document.getElementById("j-download").addEventListener("click", () => {
    if (replay.report) downloadJson(replay.report, "batalha.json");
  });
}

/* ------------------------------------------------------------------ *
 * Torneio
 * ------------------------------------------------------------------ */

function buildRoster() {
  const roster = document.getElementById("t-roster");
  roster.innerHTML = "";

  catalog.strategies.forEach((key) => {
    const commander = commanderOf(key);
    const label = el("label", "toggle");
    const input = document.createElement("input");
    input.type = "checkbox";
    input.value = key;
    input.checked = catalog.default_strategies.includes(key);
    input.addEventListener("change", updateEstimate);
    label.appendChild(input);
    label.appendChild(el("span", "em", commander.emblem));
    label.appendChild(el("span", "nm", commander.name));
    roster.appendChild(label);
  });

  ["t-sims", "t-rounds"].forEach((id) => {
    document.getElementById(id).addEventListener("input", updateEstimate);
  });
  updateEstimate();
}

function selectedStrategies() {
  return [...document.querySelectorAll("#t-roster input:checked")].map((input) => input.value);
}

function updateEstimate() {
  const note = document.getElementById("t-estimate");
  const selected = selectedStrategies();
  if (selected.length < 2) {
    note.textContent = "Selecione ao menos duas estratégias.";
    return;
  }
  const simulations = Number(document.getElementById("t-sims").value) || 0;
  const total = simulations * selected.length * (selected.length - 1);
  note.textContent = `${total} batalhas — ${selected.length * (selected.length - 1)} confrontos rodando na sua máquina.`;
}

async function runTournament() {
  const button = document.getElementById("t-run");
  const out = document.getElementById("t-out");
  const selected = selectedStrategies();

  if (selected.length < 2) {
    out.innerHTML = '<div class="placeholder">Selecione ao menos duas estratégias.</div>';
    return;
  }

  const simulations = clampInput(document.getElementById("t-sims"));
  const rounds = clampInput(document.getElementById("t-rounds"));
  const seed = clampInput(document.getElementById("t-seed"));
  const total = simulations * selected.length * (selected.length - 1);

  button.disabled = true;
  out.innerHTML = `<div class="placeholder">Rodando ${total} batalhas…<div class="progress-strip"><span></span></div></div>`;
  await nextFrame();

  try {
    const summary = JSON.parse(bridge.tournament(selected.join(","), simulations, rounds, seed));
    renderTournament(summary);
  } catch (error) {
    out.innerHTML = `<div class="placeholder">Erro no torneio: ${escapeHtml(error.message)}</div>`;
  } finally {
    button.disabled = false;
  }
}

function renderTournament(summary) {
  const out = document.getElementById("t-out");
  out.innerHTML = "";

  out.appendChild(sectionTitle("Pódio"));
  const podium = el("div", "podium");
  const medals = ["🥇", "🥈", "🥉"];
  const order = [1, 0, 2];
  order.forEach((position) => {
    const row = summary.standings[position];
    if (!row) return;
    const commander = commanderOf(row.name);
    const plinth = el("div", `plinth p${position + 1}`);
    plinth.appendChild(el("div", "medal", medals[position]));
    plinth.appendChild(el("div", "em", commander.emblem));
    plinth.appendChild(el("div", "nm", commander.name));
    plinth.appendChild(el("div", "rate", `${(row.win_rate * 100).toFixed(1)}%`));
    plinth.appendChild(el("div", "wl", `${row.wins}V · ${row.losses}D · ${row.draws}E`));
    podium.appendChild(plinth);
  });
  out.appendChild(podium);

  const meta = el(
    "p",
    "note",
    `${summary.simulations} batalhas · ${summary.matchups.length} confrontos · limite de ${summary.max_rounds} rodadas.`
  );
  out.appendChild(meta);

  out.appendChild(sectionTitle("Classificação"));
  const standings = el("div", "table-wrap");
  standings.innerHTML = `
    <table>
      <thead>
        <tr>
          <th>#</th><th>Comandante</th><th>Taxa de vitória</th>
          <th class="num">V</th><th class="num">D</th><th class="num">E</th>
          <th class="num">Rodadas méd.</th><th class="num">Dano causado</th><th class="num">Dano sofrido</th>
        </tr>
      </thead>
      <tbody>
        ${summary.standings.map((row, index) => {
          const commander = commanderOf(row.name);
          return `
          <tr class="${index === 0 ? "lead" : ""}">
            <td class="rank">${index + 1}</td>
            <td><span class="strat-cell">${commander.emblem} ${escapeHtml(commander.name)}</span></td>
            <td>
              <div class="winbar">
                <div class="track"><span style="width:${(row.win_rate * 100).toFixed(1)}%"></span></div>
                <div class="pct">${(row.win_rate * 100).toFixed(1)}%</div>
              </div>
            </td>
            <td class="num">${row.wins}</td>
            <td class="num">${row.losses}</td>
            <td class="num">${row.draws}</td>
            <td class="num">${row.average_rounds}</td>
            <td class="num">${row.average_damage_dealt}</td>
            <td class="num">${row.average_damage_taken}</td>
          </tr>`;
        }).join("")}
      </tbody>
    </table>`;
  out.appendChild(standings);

  out.appendChild(sectionTitle("Matriz de confrontos"));
  out.appendChild(matchupMatrix(summary));
  out.appendChild(el("p", "note", "Cada célula mostra quanto o comandante da linha venceu contra o da coluna, somando as duas ordens de início."));

  const actions = el("div", "row-actions");
  actions.style.padding = "16px 0 0";
  const download = el("button", "btn", "⬇ Baixar torneio.json");
  download.addEventListener("click", () => downloadJson(summary, "torneio.json"));
  actions.appendChild(download);
  out.appendChild(actions);
}

function sectionTitle(text) {
  return el("h2", "section-title", text);
}

function matchupMatrix(summary) {
  const names = summary.strategies;
  const cells = {};
  names.forEach((one) => {
    cells[one] = {};
    names.forEach((two) => { cells[one][two] = { wins: 0, games: 0 }; });
  });

  summary.matchups.forEach((matchup) => {
    const one = cells[matchup.strategy_one][matchup.strategy_two];
    const two = cells[matchup.strategy_two][matchup.strategy_one];
    one.wins += matchup.strategy_one_wins;
    one.games += matchup.simulations;
    two.wins += matchup.strategy_two_wins;
    two.games += matchup.simulations;
  });

  const wrap = el("div", "matrix-wrap");
  const grid = el("div", "matrix");
  grid.style.gridTemplateColumns = `minmax(96px, 1fr) repeat(${names.length}, minmax(84px, 1fr))`;

  grid.appendChild(el("div", "mcell head", ""));
  names.forEach((name) => grid.appendChild(el("div", "mcell head", commanderOf(name).name)));

  names.forEach((rowName) => {
    grid.appendChild(el("div", "mcell head", `${commanderOf(rowName).emblem} ${commanderOf(rowName).name}`));
    names.forEach((colName) => {
      if (rowName === colName) {
        grid.appendChild(el("div", "mcell self", "—"));
        return;
      }
      const cell = cells[rowName][colName];
      const rate = cell.games ? cell.wins / cell.games : 0;
      const node = el("div", "mcell");
      node.style.background = `hsl(${Math.round(rate * 140)}, 52%, ${Math.round(11 + rate * 13)}%)`;
      node.appendChild(el("div", "pct", `${(rate * 100).toFixed(0)}%`));
      node.appendChild(el("div", "raw", `${cell.wins}/${cell.games}`));
      grid.appendChild(node);
    });
  });

  wrap.appendChild(grid);
  return wrap;
}

/* ------------------------------------------------------------------ *
 * Manual de campo
 * ------------------------------------------------------------------ */

function buildManual() {
  const grid = document.getElementById("manual-units");
  grid.innerHTML = "";

  const peak = ["max_hp", "attack", "defense", "speed"].reduce((acc, key) => {
    acc[key] = Math.max(...catalog.units.map((unit) => unit[key]));
    return acc;
  }, {});

  catalog.units.forEach((unit) => {
    const meta = UNITS[unit.kind] || { name: unit.kind, icon: "•" };
    const card = el("article", "unit-card");
    card.dataset.role = unit.role;

    card.appendChild(el("div", "cost-badge", `🪙 ${unit.cost}`));

    const head = el("div", "head");
    head.appendChild(el("div", "em", meta.icon));
    const title = el("div");
    title.appendChild(el("div", "nm", meta.name));
    title.appendChild(el("div", "role", ROLE_PT[unit.role] || unit.role));
    head.appendChild(title);
    card.appendChild(head);

    const rows = el("div", "stat-rows");
    [
      ["Vida", "max_hp"],
      ["Ataque", "attack"],
      ["Defesa", "defense"],
      ["Velocidade", "speed"],
    ].forEach(([label, key]) => {
      const row = el("div", "stat-row");
      row.appendChild(el("div", "k", label));
      const track = el("div", "track");
      const fill = el("span");
      fill.style.width = `${peak[key] ? (unit[key] / peak[key]) * 100 : 0}%`;
      track.appendChild(fill);
      row.appendChild(track);
      row.appendChild(el("div", "v", unit[key]));
      rows.appendChild(row);
    });
    card.appendChild(rows);

    const tags = el("div", "tag-row");
    tags.appendChild(el("span", "tag", `Linha de ${LANE_PT[unit.lane] || unit.lane}`));
    tags.appendChild(el("span", "tag", unit.range >= 2 ? "Alcance 2 — atinge o fundo" : "Alcance 1 — só a frente"));
    card.appendChild(tags);

    grid.appendChild(card);
  });

  const briefs = document.getElementById("manual-strategies");
  briefs.innerHTML = "";
  catalog.strategies.forEach((key) => {
    const commander = commanderOf(key);
    const brief = el("article", "brief");
    const head = el("div", "head");
    head.appendChild(el("div", "em", commander.emblem));
    const title = el("div");
    title.appendChild(el("div", "nm", commander.name));
    title.appendChild(el("div", "cls", commander.className));
    head.appendChild(title);
    brief.appendChild(head);
    brief.appendChild(el("p", null, commander.tagline));
    briefs.appendChild(brief);
  });
}

/* ------------------------------------------------------------------ */

wireTabs();
wireTransport();
document.getElementById("b-run").addEventListener("click", runBattle);
document.getElementById("t-run").addEventListener("click", runTournament);
boot();
