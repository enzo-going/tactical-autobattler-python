# Revisão de formação e apresentação

Revisão da versão 0.5.0, commit `ea60528`. Mantidos o elenco original, cenário,
alcance por fileiras, Lanceiro e recarga de Tanque/Médico. A prioridade foi
corrigir a execução e tornar suas consequências legíveis antes de ampliar o elenco.

## Correções verificadas

- No simulador, remover uma baixa deslocava índices de tropas. Uma sobrevivente
  podia herdar a iniciativa da baixa, perder a própria ordem ou receber um ataque
  destinado a outra. Três testes reproduziram essas falhas antes da correção.
  Os planos agora permanecem vinculados às tropas originais durante a rodada,
  inclusive se o sangramento matar alguém antes das ações. Alvos mortos permitem
  nova seleção; alvos vivos mantêm sua identidade.
- O laboratório ignorava `unit_moved` e recarga entre snapshots. A apresentação
  agora acompanha esses eventos, a rodada de retorno da arma e o consumo de escudo
  pelo sangramento. Testes comparam reprodução contínua e busca por eventos com
  os snapshots do motor, sem duplicar as regras de combate.
- O manual do laboratório ainda descrevia alcance apenas pela posição do alvo.
  Ambos os manuais agora explicam origem e destino, frente exposta e cadência.
- O relatório interativo ainda dizia `tactical-v1` após duas mudanças de regras.
  Os novos relatórios usam `tactical-v2`; os automáticos, `auto-v2`. Relatórios
  antigos exigem o código da versão original; não há importação ou migração automática.
- O rodapé mostrava 0.3 e a atualização do cache dependia de editar marcadores
  manualmente. O build lê a versão do projeto e gera uma chave pelo conteúdo web/Python.

## Medição reproduzível

Executado no commit anterior e novamente com as correções, usando os mesmos
parâmetros: cinco estratégias, confrontos nas duas posições, 10 simulações por
confronto e por seed, três seeds e limite de 30 rodadas. Total: 600 batalhas em
cada versão. Custos, atributos, renda e composição dos bots foram preservados.

```bash
python -m battle_simulator --mode tournament --strategies aggressive,balanced,defensive,economy,random --simulations 10 --rounds 30 --seeds 3,7,11 --summary-only
```

| Estratégia | Vitórias antes / 240 | Vitórias depois / 240 | Taxa depois |
| --- | ---: | ---: | ---: |
| Agressiva | 178 | 209 | 87,1% |
| Equilibrada | 173 | 90 | 37,5% |
| Defensiva | 45 | 149 | 62,1% |
| Econômica | 166 | 145 | 60,4% |
| Aleatória | 38 | 7 | 2,9% |

Antes: 304 vitórias de quem abriu e 296 de quem respondeu; diferença +1,3 p.p.
Depois: 271 e 329; diferença −9,7 p.p. Não houve empates na amostra.
O limite do teste de regressão de iniciativa continua em 15 p.p.; não foi relaxado.

Esses resultados corrigem a conclusão anterior de que a composição defensiva
era a única causa de seu baixo desempenho. A iniciativa não ficou perfeitamente
equilibrada e a estratégia agressiva continua dominante. Ajustar composição,
renda ou cadência exige uma nova medição com o motor corrigido. Torneios do
simulador não validam o modo interativo, que alterna ações de outra maneira.

## Validação e próximos passos

Os testes Python cobrem identidade após baixas, alcance, recarga, comandos e
determinismo. Os testes JavaScript comparam replay com Python. O teste de navegador
exercita uma partida completa com Pyodide, download, reinício, recarga, seis larguras,
manual, laboratório, torneio e falha do CDN; roda também no CI em Chromium.

Próximas prioridades: playtests do modo interativo, salvar/retomar sessão e
melhorar decisões de proteção/movimento do adversário. Campanha e facções seguem
no roadmap. As versões 0.4.0 e 0.5.0 permanecem preservadas pelas tags originais.
