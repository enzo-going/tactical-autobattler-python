# Contribuindo

Pull requests são bem-vindos. Para mudanças grandes, abra uma issue antes para
discutir o que você pretende alterar.

Antes de abrir o PR:

```bash
python -m unittest discover -s tests
python -m compileall battle_simulator tests
python tools/build_site.py
```

Convenção de idioma: o código-fonte mantém identificadores em inglês (`attack`,
`Soldier`, `BalancedBot`); documentação e interface web ficam em pt-BR.

Para mudanças no jogo, leia [Fase II](docs/phase-two.md). Regras devem ficar em
Python; JavaScript consome estado, eventos e ações válidas. A sessão interativa
e o laboratório têm diferenças intencionais: preserve a compatibilidade da CLI
e adicione regressões quando alterar regras.

Para verificar a interface, sirva `_site` e siga as instruções de
`tests/browser_smoke.py`. Playwright é uma dependência opcional de desenvolvimento,
não do jogo. Confira também teclado, telas estreitas e carregamento/falha.
Screenshots da documentação devem refletir o jogo real.
