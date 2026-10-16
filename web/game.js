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
  pikeman: "Lanceiro",
};
const DESCRIPTIONS = {
  soldier: "Linha de frente · baixo custo",
  archer: "Alcance 2 · aplica sangramento",
  guardian: "Resistência · protege aliados",
  medic: "Triagem · cura 3, estanca e desperta · sem recarga",
  tank: "Impacto pesado · atordoa · recarga 1 rodada",
  pikeman: "Alcance 2 · golpeia da retaguarda · sem recarga",
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
const CLEANSES = { bleed: "estanca o sangramento", stun: "desfaz o atordoamento" };
const CLEANSED = { bleed: "estancou o sangramento", stun: "desfez o atordoamento" };
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
        /^(Soldier|Archer|Guardian|Medic|Tank|Pikeman)/,
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
const portrait = (kind, enemy = false) => {
  const index = Object.keys(NAMES).indexOf(kind);
  if (index < 0) return BattleArt.portrait(kind, enemy);
  const x = (index % 3) * 50, y = Math.floor(index / 3) * 100;
  return '<span class="portrait character illustrated-character' + (enemy ? ' enemy-character' : '') + '" aria-hidden="true"><span class="figure"><span class="figure-body" style="background-position:' + x + '% ' + y + '%"></span></span></span>';
};
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
// Mesma versao declarada no HTML: os modulos Python tambem precisam dela, ou o
// navegador continua rodando o motor antigo que ficou em cache.
const ASSET_VERSION =
  document.querySelector('script[src*="game.js"]')?.src.split("?v=")[1] || "";
const versioned = (path) => (ASSET_VERSION ? `${path}?v=${ASSET_VERSION}` : path);
async function source(path) {
  const response = await fetch(versioned(path));
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
    restoreGame();
    $("import").disabled = false;
    $("boot").hidden = true;
    $("game").setAttribute("aria-busy", "false");
    $("new").disabled = false;
    $("export").disabled = false;
    if (state.phase === "enemy") void runEnemyTurn();
  } catch (error) {
    $("boot").classList.add("error");
    $("boot-text").textContent =
      `Não foi possível preparar a partida. ${error.message}`;
    $("retry").hidden = false;
    $("game").setAttribute("aria-busy", "false");
  }
}
function startGame(persist = true) {
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
  if (persist) {
    protectedSave = null;
    $("save-recovery").hidden = true;
    saveGame();
  }
}
const SAVE_KEY = "tactical-save-v1";
let protectedSave = null;
function saveGame() {
  if (protectedSave !== null) return;
  try {
    localStorage.setItem(SAVE_KEY, bridge.game_save());
    $("save-status").textContent = "✓ Partida salva neste navegador";
  } catch (error) {
    $("save-status").textContent = error.message?.includes("ValueError:")
      ? errorMessage(error) + " A última cópia automática foi preservada."
      : "Salvamento automático indisponível. Baixe uma cópia em Salvar partida / relatório.";
  }
}
function acceptLoadedGame(nextState) {
  state = nextState;
  selected = Object.keys(state.legal_actions)[0] || state.troops.player_one[0]?.name || null;
  mode = null;
  $("opponent").value = state.opponent;
  $("seed").value = state.seed;
  $("rounds").value = state.max_rounds;
  render();
}
function restoreGame() {
  let saved;
  try { saved = localStorage.getItem(SAVE_KEY); }
  catch { startGame(false); saveGame(); return; }
  if (!saved) { startGame(); return; }
  try {
    acceptLoadedGame(JSON.parse(bridge.load_game(saved)));
    $("save-status").textContent = "✓ Partida retomada. Continue de onde parou.";
  } catch (error) {
    // Preserve original bytes until the player explicitly replaces the save.
    protectedSave = saved;
    startGame(false);
    $("save-status").textContent = "Não foi possível retomar a cópia anterior. " + errorMessage(error) + " Ela foi preservada; baixe-a antes de substituir.";
    $("save-recovery").hidden = false;
  }
}
function downloadJson(contents, filename) {
  const url = URL.createObjectURL(new Blob([contents], { type: "application/json" }));
  const link = node("a");
  link.href = url;
  link.download = filename;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
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
    if (state.phase === "recruit") {
      if (payload.type === "recruit") selected = state.troops.player_one.at(-1)?.name;
      if (!state.troops.player_one.some(t => t.name === selected))
        selected = state.troops.player_one[0]?.name || null;
    } else if (!state.legal_actions[selected])
      selected = Object.keys(state.legal_actions)[0] || null;
    render();
    saveGame();
    showCombatFeedback(state.events.slice(count));
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
  if (state.phase === "enemy") void runEnemyTurn();
}
let enemyPlaying = false;
let skipEnemyAnimation = false;
const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));
function lockEnemyControls() {
  const locked = enemyPlaying || state.phase === "enemy";
  for (const id of ["new", "import", "export"]) $(id).disabled = locked;
  $("advance").disabled = locked;
  $("enemy-resume").hidden = enemyPlaying || state.phase !== "enemy";
}
async function animateEnemyOrder(events) {
  const orders = events.filter(e => e.player === 2 && [
    "unit_attack", "base_attack", "heal", "shield", "unit_moved", "unit_waited",
  ].includes(e.type));
  const message = orders.map(eventText).join(" ");
  $("enemy-action").textContent = message || "O rival concluiu suas ações.";
  $("announcement").textContent = message;
  // Even without motion, present each authoritative state in sequence.
  const animated = !skipEnemyAnimation && motionEnabled && !motionQuery.matches;
  const speed = Number($("enemy-speed").value) || 1;
  if (!animated) { await delay(skipEnemyAnimation ? 0 : 160 / speed); return; }
  const pieces = new Map([...document.querySelectorAll(".piece")].map(p => [p.dataset.unit, p]));
  const order = orders[0];
  const actor = pieces.get(order?.actor);
  actor?.classList.add("enemy-acting");
  if (order?.type === "unit_moved") actor?.classList.add("relocating");
  if (order?.type === "shield") pieces.get(order.target)?.classList.add("restored");
  showCombatFeedback(events);
  // Keep the pre-hit figures on screen until impact, including a defeated target.
  const target = order?.type === "base_attack"
    ? document.querySelector(".fort.ally") : pieces.get(order?.target);
  let trail;
  if (actor && target && actor !== target && ["unit_attack", "base_attack", "heal"].includes(order.type)) {
    const from = actor.getBoundingClientRect(), to = target.getBoundingClientRect();
    const x = from.left + from.width / 2, y = from.top + Math.min(55, from.height / 2);
    const dx = to.left + to.width / 2 - x, dy = to.top + Math.min(55, to.height / 2) - y;
    trail = node("span", "order-trail" + (order.type === "heal" ? " healing" : ""));
    trail.setAttribute("aria-hidden", "true");
    Object.assign(trail.style, { left: x + "px", top: y + "px", width: Math.hypot(dx, dy) + "px", transform: `rotate(${Math.atan2(dy, dx)}rad)` });
    document.body.append(trail);
  }
  if (order?.type === "base_attack") {
    target?.classList.add("fort-hit");
    const damage = node("span", "combat-float", "−" + order.amount);
    target?.append(damage);
    setTimeout(() => damage.remove(), 1000);
  }
  try {
    await delay(450 / speed);
    for (const e of events.filter(e => e.type === "unit_defeated")) pieces.get(e.actor)?.classList.add("falling");
    await delay(400 / speed);
  } finally {
    trail?.remove();
    target?.classList.remove("fort-hit");
  }
}
async function runEnemyTurn() {
  if (busy || enemyPlaying || state.phase !== "enemy") return;
  busy = enemyPlaying = true;
  skipEnemyAnimation = false;
  lockEnemyControls();
  try {
    await delay(motionEnabled && !motionQuery.matches ? 500 : 0);
    while (state.phase === "enemy") {
      const count = state.events.length;
      const nextState = JSON.parse(bridge.game_command('{"type":"enemy_step"}'));
      // Persist the accepted Python command before showing it; reload cannot duplicate it.
      saveGame();
      try { await animateEnemyOrder(nextState.events.slice(count)); }
      finally { state = nextState; }
      render();
    }
  } catch (error) {
    $("announcement").textContent = errorMessage(error) + " Use Retomar turno rival.";
    $("announcement").classList.add("error");
  } finally {
    busy = enemyPlaying = false;
    lockEnemyControls();
    if (state.phase !== "enemy") $("advance").focus({ preventScroll: true });
  }
}
function showCombatFeedback(events) {
  if (document.body.classList.contains("motion-paused") ||
      window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  const pieces = new Map([...document.querySelectorAll(".piece")].map(p => [p.dataset.unit, p]));
  const totals = new Map();
  for (const e of events) {
    if (["unit_attack", "base_attack"].includes(e.type)) pieces.get(e.actor)?.classList.add("striking");
    if (!["unit_attack", "effect_damage", "heal"].includes(e.type)) continue;
    const target = pieces.get(e.target);
    if (!target) continue; // Defeated troops have already left the authoritative state.
    const healing = e.type === "heal";
    target.classList.add(healing ? "restored" : "hurt");
    const key = `${e.target}:${healing}`;
    const item = totals.get(key) || { target, amount: 0, healing };
    item.amount += e.amount;
    totals.set(key, item);
  }
  for (const { target, amount, healing } of totals.values()) {
    if (!amount) continue; // Triagem que so remove efeitos nao tem numero a mostrar.
    const floater = node("span", `combat-float${healing ? " healing" : ""}`, `${healing ? "+" : "−"}${amount}`);
    floater.setAttribute("aria-hidden", "true");
    target.append(floater);
    setTimeout(() => floater.remove(), 1000);
  }
  setTimeout(() => pieces.forEach(p => p.classList.remove("striking", "hurt", "restored")), 700);
}
function phaseHint() {
  if (state.phase === "recruit")
    return `Recrute e ajuste sua formação. Você joga seu turno completo antes do rival.${lineHint()}`;
  if (state.phase === "combat")
    return `Seu turno · ${Object.keys(state.legal_actions).length} ações restantes. Combine suas ordens; o rival aguarda.${lineHint()}`;
  if (state.phase === "enemy")
    return `Turno rival · ${state.remaining_actions.player_two} ações restantes. Acompanhe as jogadas no campo.`;
  if (state.phase === "review")
    return "Rodada encerrada. Confira o campo e prepare seus próximos reforços.";
  return state.winner === 1
    ? "Vitória. Seu forte resistiu."
    : state.winner === 2
      ? "Derrota. Uma nova tentativa começa com outro plano."
      : "Empate. A fronteira segue em disputa.";
}
// Vanguarda vazia abre o forte: a do rival para a sua vanguarda, a sua para a dele.
function lineHint() {
  let hint = "";
  if (state.phase === "combat" && state.open_lines.player_two)
    hint += " A linha rival está rompida: sua vanguarda pode atacar o forte.";
  if (state.open_lines.player_one && state.troops.player_one.length)
    hint += " Sua vanguarda está vazia: o forte fica exposto.";
  return hint;
}
function emptyLane(side, lane) {
  if (lane === "front" && side === "enemy" && state.phase === "combat" && state.open_lines.player_two)
    return node("div", "empty-slot breach-open", "Linha rompida · sua vanguarda alcança o forte");
  if (lane === "front" && side === "ally" && state.phase !== "finished"
      && state.open_lines.player_one && state.troops.player_one.length)
    return node("div", "empty-slot breach-exposed", "Vanguarda vazia · a vanguarda rival alcança seu forte");
  return node("div", "empty-slot",
    state.phase === "recruit" ? (side === "ally" ? "Recrute tropas para esta linha" : "O rival se prepara") : "Linha sem tropas");
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
    enemy: "O rival está jogando.",
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
    state.phase === "recruit" ? `${state.troops.player_one.length} em formação` : state.phase === "enemy" ? "Aguardando o rival" : `${Object.keys(state.legal_actions).length} prontas`;
  $("board-hint").textContent = state.phase === "recruit" ? "Selecione uma tropa para ajustar sua formação." : state.phase === "enemy" ? "Acompanhe a unidade destacada e o alvo de sua ordem." : "Selecione uma tropa pronta para dar uma ordem.";
  $("recruit-panel").hidden = state.phase !== "recruit";
  $("orders-panel").hidden = state.phase !== "combat";
  $("enemy-panel").hidden = state.phase !== "enemy";
  $("enemy-progress").textContent = `${state.remaining_actions.player_two} ações restantes`;
  document.body.classList.toggle("enemy-turn", state.phase === "enemy");
  $("turn-flow").querySelectorAll("[data-phase]").forEach(n => {
    n.classList.toggle("current", n.dataset.phase === state.phase);
    if (n.dataset.phase === state.phase) n.setAttribute("aria-current", "step");
    else n.removeAttribute("aria-current");
  });
  $("review-panel").hidden = !["review", "finished"].includes(state.phase);
  renderBoard();
  renderShop();
  renderFormation();
  renderOrders();
  renderReview();
  renderLog();
  $("advance").textContent = {
    recruit: "Entrar em combate →",
    combat: "Encerrar meu turno →",
    enemy: "Turno do rival…",
    review: "Preparar próxima rodada →",
    finished: "Jogar outra partida →",
  }[state.phase];
  lockEnemyControls();
  $("advance-hint").textContent = {
    recruit: "Recrutas podem agir já nesta rodada.",
    combat: `Encerrar agora dispensa as ${Object.keys(state.legal_actions).length} ações restantes. Ao usar todas, o turno passa automaticamente.`,
    enemy: "Cada tropa rival age uma vez. Você volta a jogar na próxima rodada.",
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
      if (!troops.length) container.append(emptyLane(side, lane));
      for (const t of troops) {
        const choice = targets.find((c) => c.target === t.name);
        const ready = Boolean(state.legal_actions[t.name]);
        const deployable = state.phase === "recruit" && side === "ally";
        const spent = state.acted.includes(t.name);
        const reloading = t.reload > 0 && t.reloading > 0;
        const weaponHint = reloading ? `Arma pronta na rodada ${t.ready_round}` : "";
        const b = button(
          "",
          () => {
            if (choice) command({ type: "act", actor: selected, ...choice });
            else if (ready || deployable) {
              selected = t.name;
              mode = null;
              renderBoard();
              renderOrders();
              renderFormation();
              document
                .querySelector(deployable ? "#formation-actions button" : "#actions button:not(:disabled)")
                ?.focus({ preventScroll: true });
              if (window.matchMedia("(max-width:800px)").matches)
                (deployable ? document.querySelector(".formation-edit") : $("orders-panel")).scrollIntoView({ block: "start" });
            }
          },
          `piece ${side === "enemy" ? "enemy-piece" : ""} ${spent ? "spent" : ""} ${selected === t.name ? "selected" : ""} ${choice ? "targetable" : ""}`,
        );
        b.disabled = !choice && !ready && !deployable;
        b.dataset.focus = `unit-${t.name}`;
        b.setAttribute(
          "aria-label",
          `${label(t.name)}, ${t.current_hp} de ${t.max_hp} de vida, ${choice ? "confirmar " + ACTIONS[mode] : deployable ? "ajustar formação" : spent ? "já agiu" : ready ? "ação disponível" : "em campo"}${weaponHint ? ", " + weaponHint : ""}`,
        );
        if (side === "ally")
          b.setAttribute("aria-pressed", String(selected === t.name));
        b.dataset.kind = kindOf(t.name);
        b.dataset.unit = t.name;
        for (const effect of Object.keys(EFFECTS))
          b.classList.toggle(`status-${effect}`, Boolean(t.effects[effect]));
        b.innerHTML = `<div class="piece-art">${portrait(kindOf(t.name), side === "enemy")}</div><div class="piece-body"><span class="piece-name">${esc(label(t.name))}</span><span class="piece-stats"><span>ATQ ${t.attack}</span><span>DEF ${t.defense}</span></span><div class="hp-line"><span class="hp-track"><i style="width:${(t.current_hp / t.max_hp) * 100}%"></i></span><small>${t.current_hp}/${t.max_hp}</small></div><span class="piece-state">${choice ? "↗ Confirmar alvo" : deployable ? "↔ Ajustar" : spent ? "— Já agiu" : ready ? "● Pode agir" : "Em posição"}</span>${reloading ? `<span class="weapon-state" title="${weaponHint}">⟳ Arma: R${t.ready_round}</span>` : ""}</div>`;
        const effects = Object.entries(t.effects)
          .map(([e, n]) => `${EFFECTS[e]} ${n}`)
          .join(" · ");
        if (effects)
          b.querySelector(".piece-body").append(node("span", "effects", effects));
        if (choice) {
          const preview = previewFor(choice);
          if (preview?.damage !== undefined)
            b.querySelector(".piece-body").append(node("span", "target-preview",
              `${preview.damage} dano${preview.defeats ? " · derrota" : ""}${preview.overflow ? ` · +${preview.overflow} forte` : ""}`));
        }
        container.append(b);
      }
    }
  }
}
function renderShop() {
  $("shop").replaceChildren();
  const warnings = state.formation_warnings.length;
  $("formation-warning").hidden = !warnings;
  $("formation-warning").textContent = (warnings === 1 ? "1 tropa de alcance 1 está atrás da vanguarda." : warnings + " tropas de alcance 1 estão atrás da vanguarda.") + " Ajuste a formação antes de combater.";
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
    b.innerHTML = `${portrait(unit.kind)}<span><span class="recruit-name">${NAMES[unit.kind]}</span><span class="recruit-desc">${DESCRIPTIONS[unit.kind]}</span><span class="recruit-facts">${unit.max_hp} VIDA · ${unit.attack} ATQ · ${unit.defense} DEF · ${unit.range} ALC</span></span><span class="recruit-cost">${unit.cost} s.</span>`;
    b.setAttribute(
      "aria-label",
      `Recrutar ${NAMES[unit.kind]}, ${unit.cost} suprimentos`,
    );
    b.title = `${unit.max_hp} vida · ${unit.attack} ataque · ${unit.defense} defesa · alcance ${unit.range}`;
    $("shop").append(b);
  }
}
function renderFormation() {
  $("formation-panel").hidden = state.phase !== "recruit";
  $("formation-detail").replaceChildren();
  $("formation-actions").replaceChildren();
  if (state.phase !== "recruit") return;
  const unit = state.troops.player_one.find(t => t.name === selected);
  if (!unit) return;
  $("formation-detail").append(node("p", "formation-name", label(unit.name)));
  if (state.formation_warnings.includes(unit.name))
    $("formation-detail").append(node("p", "reload-hint",
      "Alcance 1 atrás da vanguarda: esta tropa precisará avançar para atacar. Você pode ajustar agora sem gastar ação."));
  const lane = unit.lane === "front" ? "back" : "front";
  const move = button(`Mover para ${lane === "front" ? "vanguarda" : "retaguarda"} · grátis`,
    () => command({ type: "deploy", actor: unit.name, lane }));
  move.dataset.focus = "deploy";
  $("formation-actions").append(move);
  if (state.refundable.includes(unit.name)) {
    const refund = button(`Devolver recruta · +${unit.cost} suprimentos`,
      () => command({ type: "return", actor: unit.name }));
    refund.dataset.focus = "return-recruit";
    $("formation-actions").append(refund);
  } else {
    $("formation-detail").append(node("p", "hint", "Veteranos mantêm vida, efeitos e recarga. Não podem ser devolvidos."));
  }
}
function previewFor(choice) {
  return (state.action_previews[selected] || []).find(p =>
    p.action === choice.action && p.target === choice.target && p.lane === choice.lane);
}
function renderOrders() {
  $("ready-units").replaceChildren();
  $("cancel-order").hidden = !mode || state.phase !== "combat";
  for (const troop of state.troops.player_one.filter(t => state.legal_actions[t.name])) {
    const b = button(label(troop.name) + " · " + troop.current_hp + "/" + troop.max_hp,
      () => {
        selected = troop.name;
        mode = null;
        renderBoard();
        renderOrders();
        document.querySelector("#actions button:not(:disabled)")?.focus({ preventScroll: true });
      });
    b.setAttribute("aria-pressed", String(selected === troop.name));
    b.dataset.focus = "ready-" + troop.name;
    $("ready-units").append(b);
  }
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
    `<div class="unit-heading">${portrait(kindOf(t.name))}<div><h4>${esc(label(t.name))}</h4><small>${t.current_hp}/${t.max_hp} VIDA · ${t.lane === "front" ? "VANGUARDA" : "RETAGUARDA"}</small></div></div><p class="unit-facts">Ataque ${t.attack} · Defesa ${t.defense} · Alcance ${t.range}${t.reload ? ` · Recarga ${t.reload}` : " · Sem recarga"}<br>${DESCRIPTIONS[kindOf(t.name)]}</p>`;
  const choices = state.legal_actions[selected];
  if (t.reload > 0 && t.reloading > 0)
    $("unit-detail").append(node("p", "reload-hint",
      `Recarregando. O golpe volta na rodada ${t.ready_round}. Você ainda pode proteger, reposicionar ou esperar.`));
  else if (!choices.some(c => c.action === "attack"))
    $("unit-detail").append(node("p", "reload-hint",
      "Sem alvo ao alcance. Reposicionar consome a ação deste turno; proteger também pode ser útil."));
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
    const preview = previewFor(choice);
    if (preview?.damage !== undefined)
      text += ` · ${preview.damage} dano · ${preview.defeats ? (choice.target === "base" ? "vence a partida" : "derrota o alvo") : `${preview.remaining_hp} vida após o golpe`}${preview.overflow ? ` · +${preview.overflow} no forte${preview.wins ? ", vence a partida" : ""}` : ""}${preview.effects.length ? " · " + preview.effects.map(e => EFFECTS[e]).join(", ") : ""}`;
    if (preview?.healing !== undefined)
      text += [preview.healing ? `+${preview.healing} vida` : "", ...(preview.cleanses || []).map(e => CLEANSES[e])]
        .filter(Boolean).map(part => ` · ${part}`).join("");
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
    case "turn_started":
      return e.player === 1 ? "Seu turno começou." : "O rival iniciou seu turno.";
    case "turn_ended":
      return e.player === 1 ? "Você encerrou seu turno." : "O rival encerrou seu turno.";
    case "unit_recruited":
      return `${a} chegou à ${e.metadata.lane === "front" ? "vanguarda" : "retaguarda"}.`;
    case "unit_attack":
      return `${a} causou ${e.amount} de dano a ${t}.`;
    case "base_attack": {
      const fort = e.player === 1 ? "ao forte rival" : "ao seu forte";
      if (e.metadata?.overflow)
        return `O golpe de ${a} atravessou: ${e.amount} de dano ${fort}.`;
      if (e.metadata?.line_broken)
        return `${a} passou pela linha rompida: ${e.amount} de dano ${fort}.`;
      return `${a} causou ${e.amount} de dano ${fort}.`;
    }
    case "unit_defeated":
      return `${a} caiu em combate.`;
    case "heal": {
      const done = [e.amount ? `curou ${e.amount} de vida de ${t}` : `tratou ${t}`,
        ...(e.metadata?.cleansed || []).map(effect => CLEANSED[effect])];
      return `${a} ${done.length > 1 ? done.slice(0, -1).join(", ") + " e " + done.at(-1) : done[0]}.`;
    }
    case "shield":
      return `${a} protegeu ${t}.`;
    case "unit_stunned":
      return `${a} perdeu a ação por atordoamento.`;
    case "effect_applied":
      return `${t}: ${EFFECTS[e.metadata.effect]}.`;
    case "effect_damage":
      return `${t} sofreu ${e.amount} de dano por sangramento.`;
    case "unit_moved":
    case "unit_deployed":
      return `${a} se moveu para a ${e.metadata.lane === "front" ? "vanguarda" : "retaguarda"}.`;
    case "unit_returned":
      return `${a} deixou a formação. ${e.amount} suprimentos devolvidos.`;
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
  if (busy) return;
  if (state.phase === "finished") $("setup-dialog").showModal();
  else command({ type: state.phase === "recruit" ? "begin" : state.phase === "combat" ? "end_turn" : "next" });
});
$("enemy-skip").addEventListener("click", () => { skipEnemyAnimation = true; });
$("enemy-resume").addEventListener("click", () => { void runEnemyTurn(); });
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
  downloadJson(bridge.game_report(), "tactical-" + state.seed + "-rodada-" + state.round + ".json");
});
$("recover-save").addEventListener("click", () => downloadJson(protectedSave, "tactical-copia-anterior.json"));
$("replace-save").addEventListener("click", () => {
  protectedSave = null;
  $("save-recovery").hidden = true;
  saveGame();
});
$("cancel-order").addEventListener("click", () => {
  mode = null;
  renderBoard();
  renderOrders();
  document.querySelector("#actions button:not(:disabled)")?.focus({ preventScroll: true });
});
$("import").addEventListener("click", () => {
  $("import-form").reset();
  $("import-error").textContent = "";
  $("import-dialog").showModal();
});
$("cancel-import").addEventListener("click", () => $("import-dialog").close());
$("import-form").addEventListener("submit", async e => {
  e.preventDefault();
  const file = $("import-file").files[0];
  if (!file || $("confirm-import").disabled) return;
  if (file.size > 2 * 1024 * 1024) {
    $("import-error").textContent = "O arquivo deve ter no máximo 2 MB.";
    return;
  }
  $("confirm-import").disabled = true;
  try {
    const contents = await file.text();
    if (!$("import-dialog").open) return;
    acceptLoadedGame(JSON.parse(bridge.load_game(contents)));
    protectedSave = null;
    $("save-recovery").hidden = true;
    saveGame();
    $("import-dialog").close();
    $("announcement").textContent = "Partida carregada. " + phaseHint();
    if (state.phase === "enemy") void runEnemyTurn();
    (state.phase === "combat" ? document.querySelector("#ready-units button") : $("advance"))?.focus();
  } catch (error) {
    $("import-error").textContent = errorMessage(error);
  } finally {
    $("confirm-import").disabled = false;
  }
});
const motionQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
let motionEnabled = !motionQuery.matches;
try { motionEnabled = localStorage.getItem("battle-motion") !== "off" && !motionQuery.matches; } catch { /* Storage may be unavailable. */ }
function updateMotion() {
  document.body.classList.toggle("motion-paused", !motionEnabled);
  $("motion").textContent = motionEnabled ? "Animações: ligadas" : "Animações: pausadas";
  $("motion").setAttribute("aria-pressed", String(motionEnabled));
  $("motion").disabled = motionQuery.matches;
  $("motion").title = motionQuery.matches ? "Movimento reduzido nas preferências do sistema." : "";
}
$("motion").addEventListener("click", () => {
  motionEnabled = !motionEnabled;
  try { localStorage.setItem("battle-motion", motionEnabled ? "on" : "off"); } catch { /* Optional preference only. */ }
  updateMotion();
});
motionQuery.addEventListener("change", e => { if (e.matches) motionEnabled = false; updateMotion(); });
updateMotion();
boot();
