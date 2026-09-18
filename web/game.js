/* Presentation only: all commands and legal targets are validated in Python. */
const $ = (id) => document.getElementById(id);
const MODULES = [
  "__init__.py",
  "models.py",
  "engine.py",
  "strategies.py",
  "tournament.py",
  "cli.py",
  "session.py",
];
const NAMES = {
  soldier: "Soldado",
  archer: "Arqueiro",
  guardian: "Guardião",
  medic: "Médico",
  tank: "Tanque",
};
const DESCRIPTIONS = {
  soldier: "Linha de frente · baixo custo",
  archer: "Alcance · aplica sangramento",
  guardian: "Resistência · protege aliados",
  medic: "Suporte · cura 2 de vida",
  tank: "Impacto · atordoa o alvo",
};
const STYLES = {
  balanced: "Equilibrado",
  aggressive: "Agressivo",
  defensive: "Defensivo",
  economy: "Econômico",
  random: "Aleatório",
};
const ACTIONS = {
  attack: "Atacar",
  guard: "Proteger",
  heal: "Curar",
  move: "Reposicionar",
  wait: "Esperar",
};
const EFFECTS = { bleed: "Sangramento", shield: "Escudo", stun: "Atordoado" };
// Tiny code-native silhouettes, shared by the roster and the board.
const GLYPHS = {
  soldier:
    "M11 3h10v4h3v8h-5v3h5v10h-7v-7h-2v7H8V18h5v-3H8V7h3z M3 8h2v13H3z M1 18h6v2H1z",
  archer:
    "M12 3h8v3h3v8h-6v4h5v10h-6v-7h-2v7H8V18h5v-4H9V7h3z M27 4h2v3h2v16h-2v4h-2V4z M23 14h9v2h-9z",
  guardian: "M12 2h10v4h3v9h-7v4h8v9H15V18h-5V7h2z M2 15h12v9l-6 6-6-6z",
  medic:
    "M11 3h10v12h-5v3h7v10h-6v-7h-2v7H8V18h5v-3H9V6h2z M25 16h3v4h4v3h-4v4h-3v-4h-4v-3h4z",
  tank: "M10 2h12v4h4v10h-8v3h8v9h-8v-7h-3v7H6V18h6v-3H6V6h4z M1 2h3v27H1z M4 4h4v9H4z",
};
let bridge,
  catalog,
  state,
  selected = null,
  mode = null,
  busy = false;
const kindOf = (name) => name.split(" ")[0].toLowerCase();
const label = (name) =>
  name === "base"
    ? "Forte rival"
    : String(name || "").replace(
        /^(Soldier|Archer|Guardian|Medic|Tank)/,
        (v) => NAMES[v.toLowerCase()],
      );
const esc = (text) =>
  String(text).replace(
    /[&<>"']/g,
    (v) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        v
      ],
  );
const portrait = (kind) =>
  `<svg class="portrait" viewBox="0 0 32 32" aria-hidden="true" shape-rendering="crispEdges"><path fill="currentColor" d="${GLYPHS[kind] || GLYPHS.soldier}"/><path fill="#22281c" d="M13 9h3v2h-3zM19 9h3v2h-3z"/></svg>`;
function node(tag, className, text) {
  const n = document.createElement(tag);
  if (className) n.className = className;
  if (text !== undefined) n.textContent = text;
  return n;
}
function button(text, fn, className = "") {
  const b = node("button", className, text);
  b.type = "button";
  b.addEventListener("click", fn);
  return b;
}
async function source(path) {
  const response = await fetch(path);
  if (!response.ok) throw new Error(`Não foi possível carregar ${path}.`);
  return response.text();
}
async function boot() {
  try {
    if (typeof loadPyodide !== "function")
      throw new Error(
        "O carregamento do Python foi bloqueado ou a conexão falhou.",
      );
    const py = await loadPyodide();
    py.FS.mkdirTree("/app/battle_simulator");
    const sources = await Promise.all(
      MODULES.map((m) => source(`battle_simulator/${m}`)),
    );
    MODULES.forEach((m, i) =>
      py.FS.writeFile(`/app/battle_simulator/${m}`, sources[i]),
    );
    py.FS.writeFile("/app/playground.py", await source("playground.py"));
    bridge = await py.runPythonAsync(
      'import sys\nsys.path.insert(0, "/app")\nimport playground\nplayground',
    );
    catalog = JSON.parse(bridge.catalog());
    startGame();
    $("boot").hidden = true;
    $("game").setAttribute("aria-busy", "false");
    $("new").disabled = false;
    $("export").disabled = false;
  } catch (error) {
    $("boot").classList.add("error");
    $("boot-text").textContent =
      `Não foi possível preparar a partida. ${error.message}`;
    $("retry").hidden = false;
    $("game").setAttribute("aria-busy", "false");
  }
}
function startGame() {
  state = JSON.parse(
    bridge.new_game(
      $("opponent").value,
      Number($("seed").value),
      Number($("rounds").value),
    ),
  );
  selected = null;
  mode = null;
  render();
}
function errorMessage(error) {
  return (
    error.message
      .split("\n")
      .find((line) => line.startsWith("ValueError:"))
      ?.replace("ValueError: ", "") ||
    "Não foi possível executar a ordem. Tente novamente."
  );
}
function command(payload) {
  if (busy) return;
  busy = true;
  const focusId = document.activeElement?.dataset.focus;
  const previousPhase = state.phase;
  try {
    const count = state.events.length;
    state = JSON.parse(bridge.game_command(JSON.stringify(payload)));
    mode = null;
    if (!state.legal_actions[selected])
      selected = Object.keys(state.legal_actions)[0] || null;
    render();
    const changes = state.events
      .slice(count)
      .filter((e) =>
        [
          "unit_attack",
          "base_attack",
          "heal",
          "unit_defeated",
          "unit_stunned",
        ].includes(e.type),
      );
    if (changes.length)
      $("announcement").textContent =
        `${changes.map(eventText).join(" ")} ${phaseHint()}`;
    const replacement = [...document.querySelectorAll("[data-focus]")].find(
      (n) => n.dataset.focus === focusId && !n.disabled,
    );
    if (replacement) replacement.focus({ preventScroll: true });
    else if (state.phase === "combat")
      document
        .querySelector("#actions button:not(:disabled)")
        ?.focus({ preventScroll: true });
    else $("advance").focus({ preventScroll: true });
    if (
      previousPhase !== state.phase &&
      window.matchMedia("(max-width:800px)").matches
    ) {
      (state.phase === "combat"
        ? $("battlefield")
        : document.querySelector(".command-panel")
      ).scrollIntoView({ block: "start" });
    }
  } catch (error) {
    $("announcement").textContent = errorMessage(error);
    $("announcement").classList.add("error");
  } finally {
    busy = false;
  }
}
function phaseHint() {
  if (state.phase === "recruit")
    return `Recrute seu esquadrão. ${state.opener === 1 ? "Você abre" : "O rival abre"} o combate nesta rodada.`;
  if (state.phase === "combat")
    return "Sua vez. Escolha uma unidade pronta e dê uma ordem.";
  if (state.phase === "review")
    return "Rodada encerrada. Confira o campo e prepare seus próximos reforços.";
  return state.winner === 1
    ? "Vitória. Seu forte resistiu."
    : state.winner === 2
      ? "Derrota. Uma nova tentativa começa com outro plano."
      : "Empate. A fronteira segue em disputa.";
}
function render() {
  document.body.classList.toggle(
    "playing",
    state.phase !== "recruit" || state.round > 1,
  );
  $("announcement").classList.remove("error");
  $("announcement").textContent = phaseHint();
  $("phase-title").textContent = {
    recruit: "Prepare seu esquadrão.",
    combat: "O próximo movimento é seu.",
    review: "Uma pausa entre as batalhas.",
    finished: "Fim da expedição.",
  }[state.phase];
  $("match-id").textContent = String(state.seed).padStart(4, "0");
  $("round-label").textContent =
    `RODADA ${String(state.round).padStart(2, "0")} / ${state.max_rounds}`;
  $("enemy-style").textContent = STYLES[state.opponent];
  for (const [side, key] of [
    ["ally", "player_one"],
    ["enemy", "player_two"],
  ]) {
    $(side + "-hp").textContent =
      `${state.bases[key].health} / ${catalog.base_health}`;
    $(side + "-meter").value = state.bases[key].health;
  }
  $("resources").textContent = state.bases.player_one.resources;
  $("roster-count").textContent =
    `${state.troops.player_one.length} / ${state.roster_limit} unidades`;
  $("ready-count").textContent =
    `${Object.keys(state.legal_actions).length} prontas`;
  $("recruit-panel").hidden = state.phase !== "recruit";
  $("orders-panel").hidden = state.phase !== "combat";
  $("review-panel").hidden = !["review", "finished"].includes(state.phase);
  renderBoard();
  renderShop();
  renderOrders();
  renderReview();
  renderLog();
  $("advance").textContent = {
    recruit: "Entrar em combate →",
    combat: "Escolha uma ordem acima",
    review: "Preparar próxima rodada →",
    finished: "Jogar outra partida →",
  }[state.phase];
  $("advance").disabled = state.phase === "combat";
  $("advance-hint").textContent = {
    recruit: "Recrutas podem agir já nesta rodada.",
    combat: "Uma ordem sua. Uma resposta do rival.",
    review: "+6 suprimentos recebidos. Avance quando quiser.",
    finished: "Uma nova partida substitui o campo atual.",
  }[state.phase];
}
function targetChoices() {
  return (state.legal_actions[selected] || []).filter(
    (c) => c.action === mode && c.target,
  );
}
function renderBoard() {
  const targets = targetChoices();
  for (const [side, key] of [
    ["enemy", "player_two"],
    ["ally", "player_one"],
  ]) {
    for (const lane of ["front", "back"]) {
      const container = $(side + "-" + lane);
      container.replaceChildren();
      const troops = state.troops[key].filter((t) => t.lane === lane);
      if (!troops.length)
        container.append(
          node(
            "div",
            "empty-slot",
            side === "ally" ? "Terreno livre" : "Nenhuma tropa à vista",
          ),
        );
      for (const t of troops) {
        const choice = targets.find((c) => c.target === t.name);
        const ready = Boolean(state.legal_actions[t.name]);
        const spent = state.acted.includes(t.name);
        const b = button(
          "",
          () => {
            if (choice) command({ type: "act", actor: selected, ...choice });
            else if (ready) {
              selected = t.name;
              mode = null;
              renderBoard();
              renderOrders();
              document
                .querySelector("#actions button:not(:disabled)")
                ?.focus({ preventScroll: true });
              if (window.matchMedia("(max-width:800px)").matches)
                $("orders-panel").scrollIntoView({ block: "start" });
            }
          },
          `piece ${side === "enemy" ? "enemy-piece" : ""} ${spent ? "spent" : ""} ${selected === t.name ? "selected" : ""} ${choice ? "targetable" : ""}`,
        );
        b.disabled = !choice && !ready;
        b.dataset.focus = `unit-${t.name}`;
        b.setAttribute(
          "aria-label",
          `${label(t.name)}, ${t.current_hp} de ${t.max_hp} de vida, ${choice ? "confirmar " + ACTIONS[mode] : spent ? "já agiu" : ready ? "pronta" : "em campo"}`,
        );
        if (side === "ally")
          b.setAttribute("aria-pressed", String(selected === t.name));
        b.innerHTML = `<div class="piece-head">${portrait(kindOf(t.name))}<span class="piece-name">${esc(label(t.name))}<span class="piece-stats">ATQ ${t.attack} · DEF ${t.defense}</span></span></div><div class="hp-line"><span class="hp-track"><i style="width:${(t.current_hp / t.max_hp) * 100}%"></i></span><small>${t.current_hp}/${t.max_hp}</small></div><span class="piece-state">${choice ? "↗ Confirmar alvo" : spent ? "— Já agiu" : ready ? "● Pronta" : "Em posição"}</span>`;
        const effects = Object.entries(t.effects)
          .map(([e, n]) => `${EFFECTS[e]} ${n}`)
          .join(" · ");
        if (effects) b.append(node("span", "effects", effects));
        container.append(b);
      }
    }
  }
}
function renderShop() {
  $("shop").replaceChildren();
  for (const unit of catalog.units) {
    const b = button(
      "",
      () =>
        command({
          type: "recruit",
          kind: unit.kind,
          lane:
            $("recruit-lane").value === "auto"
              ? unit.lane
              : $("recruit-lane").value,
        }),
      "recruit",
    );
    b.dataset.focus = `recruit-${unit.kind}`;
    b.disabled =
      state.phase !== "recruit" ||
      state.bases.player_one.resources < unit.cost ||
      state.troops.player_one.length >= state.roster_limit;
    b.innerHTML = `${portrait(unit.kind)}<span><span class="recruit-name">${NAMES[unit.kind]}</span><span class="recruit-desc">${DESCRIPTIONS[unit.kind]}</span></span><span class="recruit-cost">${unit.cost} s.</span>`;
    b.setAttribute(
      "aria-label",
      `Recrutar ${NAMES[unit.kind]}, ${unit.cost} suprimentos`,
    );
    b.title = `${unit.max_hp} vida · ${unit.attack} ataque · ${unit.defense} defesa · alcance ${unit.range}`;
    $("shop").append(b);
  }
}
function renderOrders() {
  $("actions").replaceChildren();
  $("targets").replaceChildren();
  $("unit-detail").replaceChildren();
  const t = state.troops.player_one.find((t) => t.name === selected);
  if (!t || !state.legal_actions[selected]) {
    $("unit-detail").append(
      node(
        "p",
        "hint",
        "Selecione uma peça pronta no campo. Cada unidade pode receber uma ordem por rodada.",
      ),
    );
    $("target-hint").textContent = "";
    return;
  }
  $("unit-detail").innerHTML =
    `<div class="unit-heading">${portrait(kindOf(t.name))}<div><h4>${esc(label(t.name))}</h4><small>${t.current_hp}/${t.max_hp} VIDA · ${t.lane === "front" ? "VANGUARDA" : "RETAGUARDA"}</small></div></div><p class="unit-facts">Ataque ${t.attack} · Defesa ${t.defense} · Alcance ${t.range}<br>${DESCRIPTIONS[kindOf(t.name)]}</p>`;
  const choices = state.legal_actions[selected];
  for (const [action, name] of Object.entries(ACTIONS)) {
    const available = choices.filter((c) => c.action === action);
    const b = button(name, () => {
      mode = action;
      renderBoard();
      renderOrders();
      document.querySelector("#targets button")?.focus({ preventScroll: true });
    });
    b.disabled = !available.length;
    b.setAttribute("aria-pressed", String(mode === action));
    b.dataset.focus = `action-${action}`;
    $("actions").append(b);
  }
  $("target-hint").textContent = mode
    ? "Confirme abaixo ou toque em uma peça destacada no campo."
    : "Escolha uma ordem. Você confirma o alvo antes de agir.";
  for (const choice of choices.filter((c) => c.action === mode)) {
    let text = choice.target
      ? `${ACTIONS[mode]} → ${label(choice.target)}`
      : mode === "move"
        ? `Mover para a ${choice.lane === "front" ? "vanguarda" : "retaguarda"}`
        : "Confirmar: esperar nesta rodada";
    if (mode === "attack") {
      const target = state.troops.player_two.find(
        (t) => t.name === choice.target,
      );
      if (target) text += ` · ${target.current_hp} HP`;
    }
    $("targets").append(
      button(text, () => command({ type: "act", actor: selected, ...choice })),
    );
  }
}
function renderReview() {
  const finished = state.phase === "finished";
  $("result-title").textContent = finished
    ? state.winner === 1
      ? "Seu forte resistiu."
      : state.winner === 2
        ? "A fronteira caiu."
        : "Nenhum lado cedeu."
    : "Respire. Reorganize.";
  $("result-copy").textContent = finished
    ? state.reason === "round_limit"
      ? "Limite de rodadas atingido. Desempate por vida da base, depois dano de golpes (sem sangramento)."
      : "A destruição de um forte encerrou a partida."
    : "Os sobreviventes mantêm a vida e os efeitos. Mais 6 suprimentos chegaram para o próximo confronto.";
  $("round-summary").replaceChildren();
  for (const [name, value] of [
    ["Seu forte", `${state.bases.player_one.health} HP`],
    ["Forte rival", `${state.bases.player_two.health} HP`],
    ["Seu dano de golpes", state.stats.player_one.damage_dealt],
    ["Tropas sobreviventes", state.troops.player_one.length],
  ]) {
    const row = node("div");
    row.append(node("span", "", name), node("b", "", value));
    $("round-summary").append(row);
  }
}
function eventText(e) {
  const a = label(e.actor),
    t = label(e.target);
  switch (e.type) {
    case "round_started":
      return `Rodada ${e.round}: preparar o esquadrão.`;
    case "unit_recruited":
      return `${a} chegou à ${e.metadata.lane === "front" ? "vanguarda" : "retaguarda"}.`;
    case "unit_attack":
    case "base_attack":
      return `${a} causou ${e.amount} de dano a ${t}.`;
    case "unit_defeated":
      return `${a} caiu em combate.`;
    case "heal":
      return `${a} curou ${e.amount} de vida de ${t}.`;
    case "shield":
      return `${a} protegeu ${t}.`;
    case "unit_stunned":
      return `${a} perdeu a ação por atordoamento.`;
    case "effect_applied":
      return `${t}: ${EFFECTS[e.metadata.effect]}.`;
    case "effect_damage":
      return `${t} sofreu ${e.amount} de dano por sangramento.`;
    case "unit_moved":
      return `${a} se moveu para a ${e.metadata.lane === "front" ? "vanguarda" : "retaguarda"}.`;
    case "unit_waited":
      return `${a} manteve posição.`;
    case "round_ended":
      return "Rodada encerrada. Ambos os fortes receberam 6 suprimentos.";
    case "match_finished":
      return e.player === 1
        ? "Vitória do seu esquadrão."
        : e.player === 2
          ? "Vitória do rival."
          : "A partida terminou em empate.";
    default:
      return e.message;
  }
}
function renderLog() {
  const events = [...state.events].reverse();
  $("journal-empty").hidden = events.length > 1;
  for (const [id, items] of [
    ["event-log", events.slice(0, 6)],
    ["history", events],
  ]) {
    $(id).replaceChildren();
    for (const e of items) {
      const li = node("li", e.player === 2 ? "rival" : "");
      li.append(
        node(
          "span",
          "",
          `R${String(e.round).padStart(2, "0")} ${e.player === 1 ? "VOCÊ" : e.player === 2 ? "RIVAL" : ""}`,
        ),
        node("span", "", eventText(e)),
      );
      $(id).append(li);
    }
  }
}
$("advance").addEventListener("click", () => {
  if (state.phase === "finished") $("setup-dialog").showModal();
  else command({ type: state.phase === "recruit" ? "begin" : "next" });
});
$("new").addEventListener("click", () => $("setup-dialog").showModal());
$("cancel-new").addEventListener("click", () => $("setup-dialog").close());
$("setup-form").addEventListener("submit", (e) => {
  e.preventDefault();
  try {
    startGame();
    $("setup-dialog").close();
    $("advance").focus();
  } catch (error) {
    $("announcement").textContent = errorMessage(error);
  }
});
$("help").addEventListener("click", () => $("help-dialog").showModal());
$("close-help").addEventListener("click", () => $("help-dialog").close());
$("retry").addEventListener("click", () => location.reload());
$("export").addEventListener("click", () => {
  const url = URL.createObjectURL(
    new Blob([bridge.game_report()], { type: "application/json" }),
  );
  const link = node("a");
  link.href = url;
  link.download = `tactical-${state.seed}-rodada-${state.round}.json`;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
});
boot();
