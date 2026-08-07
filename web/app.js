/*
 * Interface web do Tactical Auto-Battler.
 *
 * Toda a simulacao acontece no pacote Python `battle_simulator`, carregado no
 * Pyodide. Este arquivo so cuida de: montar os controles, chamar as funcoes de
 * web/playground.py e traduzir para pt-BR o relatorio JSON que volta.
 */

const MODULES = [
  "__init__.py",
  "models.py",
  "engine.py",
  "strategies.py",
  "tournament.py",
  "cli.py",
];

const STRATEGY_PT = {
  aggressive: "Agressiva",
  balanced: "Equilibrada",
  defensive: "Defensiva",
  economy: "Econômica",
  random: "Aleatória",
};

const UNIT_PT = {
  soldier: "Soldado",
  archer: "Arqueiro",
  guardian: "Guardião",
  medic: "Médico",
  tank: "Tanque",
};

const UNIT_ICON = {
  soldier: "🗡️",
  archer: "🏹",
  guardian: "🛡️",
  medic: "➕",
  tank: "🚜",
};

const ROLE_PT = {
  assault: "Assalto",
  defender: "Defensor",
  ranged: "Alcance",
  support: "Suporte",
};

const LANE_PT = { front: "frente", back: "fundo" };

const EFFECT_PT = { bleed: "sangramento", shield: "escudo", stun: "atordoamento" };

const BASE_PT = { Blue: "Azul", Red: "Vermelho" };

/** "Archer 3" -> "Arqueiro 3" */
function unitName(name) {
  if (!name) return "";
  const match = /^([A-Za-z]+)\s*(\d*)$/.exec(name);
  if (!match) return name;
  const key = match[1].toLowerCase();
  if (!UNIT_PT[key]) return name;
  return `${UNIT_PT[key]}${match[2] ? " " + match[2] : ""}`;
}

function baseName(name) {
  return BASE_PT[name] || name;
}

function unitIcon(name) {
  const key = String(name || "").split(" ")[0].toLowerCase();
  return UNIT_ICON[key] || "•";
}

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

/* ------------------------------------------------------------------ *
 * Boot do Pyodide
 * ------------------------------------------------------------------ */

let pyodide = null;
let bridge = null;
let catalog = null;

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
    buildControls();
    renderUnits(catalog.units);

    document.getElementById("b-run").disabled = false;
    document.getElementById("t-run").disabled = false;
    bootBox.classList.add("done");
  } catch (error) {
    bootBox.classList.add("error");
    bootBox.innerHTML = `<span>⚠️</span><span>Não foi possível iniciar o Python no navegador: ${escapeHtml(error.message)}</span>`;
  }
}

/* ------------------------------------------------------------------ *
 * Controles
 * ------------------------------------------------------------------ */

function buildControls() {
  const s1 = document.getElementById("b-s1");
  const s2 = document.getElementById("b-s2");

  catalog.strategies.forEach((name) => {
    const label = STRATEGY_PT[name] || name;
    s1.appendChild(new Option(label, name));
    s2.appendChild(new Option(label, name));
  });
  s1.value = "balanced";
  s2.value = "random";

  const box = document.getElementById("t-strats");
  catalog.strategies.forEach((name) => {
    const label = el("label");
    const input = document.createElement("input");
    input.type = "checkbox";
    input.value = name;
    input.checked = catalog.default_strategies.includes(name);
    label.appendChild(input);
    label.appendChild(document.createTextNode(STRATEGY_PT[name] || name));
    box.appendChild(label);
  });
}

function tabs() {
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

/**
 * Deixa o navegador pintar o estado "rodando" antes de travar na simulacao.
 * Usa setTimeout em vez de requestAnimationFrame porque rAF nao dispara em
 * aba de fundo, o que deixaria o botao preso em "Simulando...".
 */
function nextFrame() {
  return new Promise((resolve) => setTimeout(resolve, 30));
}

function clampInput(input) {
  const value = Number(input.value);
  const min = Number(input.min);
  const max = Number(input.max);
  if (!Number.isFinite(value)) return min;
  return Math.min(max, Math.max(min, Math.round(value)));
}

/* ------------------------------------------------------------------ *
 * Batalha
 * ------------------------------------------------------------------ */

async function runBattle() {
  const button = document.getElementById("b-run");
  const out = document.getElementById("b-out");
  const strategyOne = document.getElementById("b-s1").value;
  const strategyTwo = document.getElementById("b-s2").value;
  const rounds = clampInput(document.getElementById("b-rounds"));
  const seed = clampInput(document.getElementById("b-seed"));

  button.disabled = true;
  out.innerHTML = '<div class="placeholder busy">Simulando…</div>';
  await nextFrame();

  try {
    const report = JSON.parse(bridge.battle(strategyOne, strategyTwo, rounds, seed));
    renderBattle(report, strategyOne, strategyTwo);
  } catch (error) {
    out.innerHTML = `<div class="placeholder">Erro na simulação: ${escapeHtml(error.message)}</div>`;
  } finally {
    button.disabled = false;
  }
}

function renderBattle(report, strategyOne, strategyTwo) {
  const out = document.getElementById("b-out");
  out.innerHTML = "";

  const winner = report.winner;
  const byTiebreak = report.events.some((event) => event.type === "tiebreak");
  const banner = el("div", "result-banner " + (winner === "Blue" ? "blue" : winner === "Red" ? "red" : ""));
  const headline = el("div");
  headline.appendChild(
    el(
      "strong",
      null,
      winner
        ? `Base ${baseName(winner)} venceu${byTiebreak ? " no desempate" : ""}`
        : "Empate"
    )
  );
  headline.appendChild(
    el("div", "meta", `${report.rounds_played} rodadas · ${report.event_count} eventos registrados`)
  );
  banner.appendChild(headline);
  banner.appendChild(
    el("div", "meta", `${STRATEGY_PT[strategyOne] || strategyOne} × ${STRATEGY_PT[strategyTwo] || strategyTwo}`)
  );
  out.appendChild(banner);

  const teams = el("div", "teams");
  teams.appendChild(teamCard("blue", "player_one", report, strategyOne));
  teams.appendChild(teamCard("red", "player_two", report, strategyTwo));
  out.appendChild(teams);

  out.appendChild(el("h2", "section", "Log da batalha"));
  out.appendChild(renderLog(report.events));

  out.appendChild(el("h2", "section", "Relatório JSON"));
  const hint = el("p", "hint", "Mesma estrutura gerada por --report-json na linha de comando.");
  out.appendChild(hint);

  const actions = el("div", "json-actions");
  const toggle = el("button", "ghost", "Mostrar JSON");
  const download = el("button", "ghost", "⬇ Baixar batalha.json");
  actions.appendChild(toggle);
  actions.appendChild(download);
  out.appendChild(actions);

  const pre = el("pre", "json", JSON.stringify(report, null, 2));
  pre.hidden = true;
  out.appendChild(pre);

  toggle.addEventListener("click", () => {
    pre.hidden = !pre.hidden;
    toggle.textContent = pre.hidden ? "Mostrar JSON" : "Ocultar JSON";
  });
  download.addEventListener("click", () => downloadJson(report, "batalha.json"));
}

function teamCard(color, key, report, strategy) {
  const base = report.bases[key];
  const damage = report.damage[key];
  const troops = report.troops_remaining[key];

  const card = el("div", "team " + color);
  card.appendChild(el("h3", null, `Base ${baseName(base.name)}`));
  card.appendChild(el("div", "strat", `Estratégia: ${STRATEGY_PT[strategy] || strategy}`));

  const grid = el("div", "stat-grid");
  grid.appendChild(statBox("HP da base", base.health, base.health / catalog.base_health));
  grid.appendChild(statBox("Recursos", base.resources));
  grid.appendChild(statBox("Dano causado", damage.dealt));
  grid.appendChild(statBox("Dano sofrido", damage.received));
  grid.appendChild(statBox("Unidades recrutadas", report.units_recruited[key]));
  grid.appendChild(statBox("Tropas vivas", troops.length));
  card.appendChild(grid);

  if (troops.length === 0) {
    card.appendChild(el("div", "empty", "Nenhuma tropa sobreviveu."));
  } else {
    troops.forEach((troop) => {
      const row = el("div", "troop");
      row.appendChild(el("span", null, unitIcon(troop.name)));
      const name = el("span", "nm", unitName(troop.name));
      name.title = `${ROLE_PT[troop.role] || troop.role} · linha de ${LANE_PT[troop.lane] || troop.lane} · ${troop.attack} ATQ / ${troop.defense} DEF`;
      row.appendChild(name);
      row.appendChild(hpBar(troop.current_hp / troop.max_hp, "bar"));
      row.appendChild(el("span", "hp", `${troop.current_hp}/${troop.max_hp}`));
      card.appendChild(row);
    });
  }

  return card;
}

function statBox(key, value, ratio) {
  const box = el("div", "stat");
  box.appendChild(el("div", "k", key));
  box.appendChild(el("div", "v", value));
  if (ratio !== undefined) box.appendChild(hpBar(ratio));
  return box;
}

function hpBar(ratio, extraClass) {
  const safe = Math.max(0, Math.min(1, Number.isFinite(ratio) ? ratio : 0));
  const level = safe <= 0.25 ? " critical" : safe <= 0.5 ? " low" : "";
  const bar = el("div", "hpbar" + level + (extraClass ? " " + extraClass : ""));
  const fill = el("span");
  fill.style.width = `${safe * 100}%`;
  bar.appendChild(fill);
  return bar;
}

/* ------------------------------------------------------------------ *
 * Log traduzido a partir dos eventos estruturados
 * ------------------------------------------------------------------ */

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

/** Traduz um evento do motor; devolve null para eventos que nao viram linha. */
function describe(event) {
  const actor = unitName(event.actor);
  const target = unitName(event.target);
  const amount = event.amount;

  switch (event.type) {
    case "round_started":
      return null;
    case "unit_recruited":
      return `${event.player === 1 ? "Azul" : "Vermelho"} recrutou ${actor} na linha de ${LANE_PT[event.metadata.lane] || event.metadata.lane} por ${amount} recursos`;
    case "unit_attack":
      return `${actor} atacou ${target} causando <span class="amt">${amount}</span> de dano`;
    case "base_attack":
      return `${actor} atingiu a base ${baseName(event.target)} causando <span class="amt">${amount}</span> de dano`;
    case "unit_defeated":
      return `${actor} foi derrotado`;
    case "effect_damage":
      return `${target} sofreu <span class="amt">${amount}</span> de dano de ${EFFECT_PT[event.actor] || event.actor}`;
    case "effect_applied":
      return `${actor} aplicou ${EFFECT_PT[event.metadata.effect] || event.metadata.effect} em ${target}`;
    case "heal":
      return `${actor} curou ${target} em <span class="amt">${amount}</span> HP`;
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
      return `Limite de rodadas atingido: vitória do lado ${event.player === 1 ? "Azul" : "Vermelho"} no desempate`;
    default:
      return escapeHtml(event.message || event.type);
  }
}

function renderLog(events) {
  const log = el("div", "log");
  let currentRound = null;

  events.forEach((event) => {
    if (event.round !== currentRound) {
      currentRound = event.round;
      log.appendChild(el("div", "round-head", `Rodada ${currentRound}`));
    }

    const text = describe(event);
    if (text === null) return;

    const side = event.player === 1 ? "p1" : event.player === 2 ? "p2" : "neutral";
    const line = el("div", `line ${side}`);
    line.appendChild(el("span", "icon", EVENT_ICON[event.type] || "·"));
    const body = el("span");
    body.innerHTML = text;
    line.appendChild(body);
    log.appendChild(line);
  });

  if (!log.childElementCount) log.appendChild(el("div", "placeholder", "Sem eventos."));
  return log;
}

/* ------------------------------------------------------------------ *
 * Torneio
 * ------------------------------------------------------------------ */

async function runTournament() {
  const button = document.getElementById("t-run");
  const out = document.getElementById("t-out");
  const selected = [...document.querySelectorAll("#t-strats input:checked")].map((input) => input.value);

  if (selected.length < 2) {
    out.innerHTML = '<div class="placeholder">Selecione ao menos duas estratégias.</div>';
    return;
  }

  const simulations = clampInput(document.getElementById("t-sims"));
  const rounds = clampInput(document.getElementById("t-rounds"));
  const seed = clampInput(document.getElementById("t-seed"));
  const total = simulations * selected.length * (selected.length - 1);

  button.disabled = true;
  out.innerHTML = `<div class="placeholder busy">Rodando ${total} batalhas…</div>`;
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

  const banner = el("div", "result-banner blue");
  const head = el("div");
  head.appendChild(el("strong", null, `🏆 ${STRATEGY_PT[summary.standings[0].name] || summary.standings[0].name} lidera`));
  head.appendChild(
    el("div", "meta", `${summary.simulations} batalhas · ${summary.matchups.length} confrontos · limite de ${summary.max_rounds} rodadas`)
  );
  banner.appendChild(head);
  banner.appendChild(
    el("div", "meta", `${(summary.standings[0].win_rate * 100).toFixed(1)}% de vitórias`)
  );
  out.appendChild(banner);

  out.appendChild(el("h2", "section", "Classificação"));
  const standingsWrap = el("div", "table-wrap");
  standingsWrap.innerHTML = `
    <table>
      <thead>
        <tr>
          <th>#</th><th>Estratégia</th><th>Taxa de vitória</th>
          <th class="num">V</th><th class="num">D</th><th class="num">E</th>
          <th class="num">Rodadas méd.</th><th class="num">Dano causado</th><th class="num">Dano sofrido</th>
        </tr>
      </thead>
      <tbody>
        ${summary.standings.map((row, index) => `
          <tr class="${index === 0 ? "first" : ""}">
            <td class="rank">${index + 1}</td>
            <td>${escapeHtml(STRATEGY_PT[row.name] || row.name)}</td>
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
          </tr>`).join("")}
      </tbody>
    </table>`;
  out.appendChild(standingsWrap);

  out.appendChild(el("h2", "section", "Confrontos"));
  const matchWrap = el("div", "table-wrap");
  matchWrap.innerHTML = `
    <table>
      <thead>
        <tr><th>Confronto</th><th class="num">Placar</th><th class="num">Empates</th><th class="num">Rodadas méd.</th><th class="num">Dano méd.</th></tr>
      </thead>
      <tbody>
        ${summary.matchups.map((matchup) => `
          <tr>
            <td>${escapeHtml(STRATEGY_PT[matchup.strategy_one] || matchup.strategy_one)} <span class="rank">vs</span> ${escapeHtml(STRATEGY_PT[matchup.strategy_two] || matchup.strategy_two)}</td>
            <td class="num">${matchup.strategy_one_wins} – ${matchup.strategy_two_wins}</td>
            <td class="num">${matchup.draws}</td>
            <td class="num">${matchup.average_rounds}</td>
            <td class="num">${matchup.strategy_one_damage_dealt} / ${matchup.strategy_two_damage_dealt}</td>
          </tr>`).join("")}
      </tbody>
    </table>`;
  out.appendChild(matchWrap);

  const actions = el("div", "json-actions");
  const download = el("button", "ghost", "⬇ Baixar torneio.json");
  download.addEventListener("click", () => downloadJson(summary, "torneio.json"));
  actions.appendChild(download);
  out.appendChild(actions);
}

/* ------------------------------------------------------------------ *
 * Unidades
 * ------------------------------------------------------------------ */

function renderUnits(units) {
  document.getElementById("u-table").innerHTML = `
    <thead>
      <tr>
        <th>Unidade</th><th>Papel</th><th>Linha padrão</th>
        <th class="num">HP</th><th class="num">Ataque</th><th class="num">Defesa</th>
        <th class="num">Velocidade</th><th class="num">Alcance</th><th class="num">Custo</th>
      </tr>
    </thead>
    <tbody>
      ${units.map((unit) => `
        <tr>
          <td>${UNIT_ICON[unit.kind] || ""} ${escapeHtml(UNIT_PT[unit.kind] || unit.kind)}</td>
          <td>${escapeHtml(ROLE_PT[unit.role] || unit.role)}</td>
          <td>${escapeHtml(LANE_PT[unit.lane] || unit.lane)}</td>
          <td class="num">${unit.max_hp}</td>
          <td class="num">${unit.attack}</td>
          <td class="num">${unit.defense}</td>
          <td class="num">${unit.speed}</td>
          <td class="num">${unit.range}</td>
          <td class="num">${unit.cost}</td>
        </tr>`).join("")}
    </tbody>`;
}

/* ------------------------------------------------------------------ */

function downloadJson(data, filename) {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

tabs();
document.getElementById("b-run").addEventListener("click", runBattle);
document.getElementById("t-run").addEventListener("click", runTournament);
boot();
