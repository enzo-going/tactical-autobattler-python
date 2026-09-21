"""Monta a arte do README a partir dos proprios arquivos do jogo.

O cenario e o elenco vivem em `web/battlefield.svg` e `web/characters.js`. Em
vez de manter uma captura de tela que envelhece a cada mudanca de interface,
esta ferramenta compoe as duas coisas em um SVG unico e versionado.

    python tools/make_key_art.py
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SAIDA = ROOT / "docs" / "images" / "campo.svg"

# As mesmas cores de pano que o CSS entrega as duas faccoes.
AZUL = ("#4d7ead", "#354b6d")
VERMELHO = ("#a15368", "#633949")

# Quem aparece, de que lado, e onde. O lanceiro fica atras da linha de frente:
# e a formacao que a versao 0.4 tornou decisiva.
FORMACAO = (
    ("guardian", AZUL, 196, 470, 1.35, False),
    ("soldier", AZUL, 336, 486, 1.3, False),
    ("pikeman", AZUL, 116, 566, 1.25, False),
    ("archer", AZUL, 268, 590, 1.2, False),
    ("tank", VERMELHO, 966, 470, 1.35, True),
    ("soldier", VERMELHO, 838, 486, 1.3, True),
    ("archer", VERMELHO, 1104, 566, 1.25, True),
    ("medic", VERMELHO, 962, 594, 1.2, True),
)


def _const(js: str, nome: str) -> str:
    achado = re.search(r"const %s = ([`'])(.*?)\1;" % nome, js, re.S)
    if not achado:
        raise SystemExit(f"nao encontrei a constante {nome} em characters.js")
    return achado.group(2)


def elenco() -> dict[str, str]:
    js = (ROOT / "web" / "characters.js").read_text(encoding="utf-8")
    compartilhado = {nome: _const(js, nome) for nome in ("boot", "face", "belt")}
    figuras = {}
    for nome in ("soldier", "archer", "guardian", "medic", "tank", "pikeman"):
        corpo = _const(js, nome)
        for chave, valor in compartilhado.items():
            corpo = corpo.replace("${%s}" % chave, valor)
        figuras[nome] = corpo
    return figuras


def build() -> None:
    campo = (ROOT / "web" / "battlefield.svg").read_text(encoding="utf-8")
    fundo = campo.split(">", 1)[1].rsplit("</svg>", 1)[0]
    figuras = elenco()

    partes = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1400 800" '
        'role="img" aria-label="Dois exercitos em formacao no campo de batalha">',
        f"<g>{fundo}</g>",
    ]
    for nome, (pano, pano_escuro), x, y, escala, espelhado in FORMACAO:
        giro = f"translate({x + 120 * escala},{y}) scale({-escala},{escala})" if espelhado else f"translate({x},{y}) scale({escala})"
        partes.append(
            f'<g transform="{giro}" style="--cloth:{pano};--cloth-dark:{pano_escuro}">'
            f'<ellipse cx="58" cy="128" rx="37" ry="6" fill="#080e18" opacity=".35"/>'
            f'<g stroke="#1b202b" stroke-width="2.5" stroke-linejoin="round" '
            f'stroke-linecap="round">{figuras[nome]}</g></g>'
        )
    partes.append("</svg>")

    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    SAIDA.write_text("\n".join(partes), encoding="utf-8")
    print(f"Arte pronta: {SAIDA} ({SAIDA.stat().st_size} bytes)")


if __name__ == "__main__":
    build()
