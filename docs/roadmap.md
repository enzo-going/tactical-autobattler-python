# Roadmap

## Fase I — simulador (0.2, concluída)

- Pacote Python com modelos de POO, regras, efeitos e estratégias.
- CLI, simulações determinísticas, torneios espelhados e relatórios JSON.
- Testes automatizados, CI e publicação via GitHub Pages.
- Interface de replay usando o próprio pacote Python no navegador.

## Fase II — jogo interativo (0.3, implementada nesta versão)

- Sessão entre comandos, com preparação, combate, revisão e desfecho.
- Recrutamento manual, duas linhas e limite de oito tropas.
- Seleção de unidade, ordem e alvo; respostas alternadas do rival.
- Ataque, proteção, cura, reposicionamento e espera.
- Tabuleiro responsivo, peças SVG, manual e diário de combate.
- Exportação de decisões e reprodução determinística pela API Python.
- Laboratório preservado e documentação das diferenças de regras.

Veja os critérios e detalhes em [Fase II](phase-two.md).

## Próxima prioridade — jogar, observar, ajustar

1. Playtests: duração, clareza, utilidade das unidades e vantagem de abrir a
   rodada. Medir o modo interativo separadamente do simulador.
2. Salvar/retomar sessão com versão de esquema e migração de regras explícitas.
3. Desfazer compras durante a preparação.
4. Melhorar o bot: proteção, movimento e estilos próprios de combate.
5. Feedback visual breve de dano e movimentação, sem bloquear comandos nem
   prejudicar quem prefere movimento reduzido.
6. Expandir verificações para Firefox, Safari e leitores de tela.

## Depois, se fizer sentido

- Interface textual usando a mesma `TacticalSession` da web.
- Pequenos cenários com objetivos diferentes de destruir a base.
- Terrenos e obstáculos, após validar o valor das duas linhas atuais.
- Áudio opcional e progressão entre partidas.

Campanha e multiplayer não fazem parte desta entrega.

## Barra de qualidade

Regras e validação permanecem em Python. O pacote continua sem dependências
externas de runtime; Pyodide é a dependência do navegador. Mudanças devem
preservar testes, documentar diferenças entre modos e manter o build local
igual ao do GitHub Pages. Recursos futuros não devem ser apresentados como
já disponíveis.
