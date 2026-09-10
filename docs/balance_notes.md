# Notas de balanceamento: iniciativa

## Problema observado

Até esta revisão, a iniciativa era ordenada apenas por velocidade. Como a
ordenação do Python é estável e as ordens do Jogador 1 entravam primeiro na
lista, todas as unidades empatadas em velocidade do Jogador 1 agiam antes das
equivalentes do Jogador 2. O round-robin espelhado reduzia o efeito sobre a
classificação das estratégias, mas não corrigia a regra dentro da batalha.

## Experimento

O benchmark usa o elenco completo, confrontos espelhados, 20 batalhas por seed,
30 rodadas e oito seeds-base independentes:

```bash
python -m battle_simulator --mode tournament \
  --strategies aggressive,balanced,defensive,economy,random \
  --simulations 20 --rounds 30 \
  --seeds 3,7,11,19,29,43,71,101 \
  --summary-only
```

São 20 confrontos dirigidos por seed e 3.200 batalhas no total. Cada repetição
usa uma sub-seed determinística e não sobreposta, derivada da seed-base. A métrica
principal separa a vitória de quem abriu os empates de velocidade da vitória de
quem respondeu. Empates não entram no denominador da taxa de vitória.

| Regra | Abriu e venceu | Respondeu e venceu | Taxa de quem abriu | Diferença |
|---|---:|---:|---:|---:|
| Anterior: lotes, Jogador 1 sempre primeiro | 2.484 | 716 | 77,6% | +55,2 p.p. |
| Atual: ações intercaladas e abertura alternada | 1.752 | 1.448 | 54,8% | +9,5 p.p. |

A diferença caiu 82,8%. O resultado anterior foi capturado imediatamente antes
da mudança com os mesmos parâmetros; o resultado atual é reproduzível pelo
comando acima e também aparece no bloco **Equilíbrio de iniciativa** da interface
web.

### Resultado atual por seed

| Seed | Abriu e venceu | Respondeu e venceu | Taxa de quem abriu | Diferença |
|---:|---:|---:|---:|---:|
| 3 | 219 | 181 | 54,8% | +9,5 p.p. |
| 7 | 219 | 181 | 54,8% | +9,5 p.p. |
| 11 | 221 | 179 | 55,2% | +10,5 p.p. |
| 19 | 219 | 181 | 54,8% | +9,5 p.p. |
| 29 | 217 | 183 | 54,2% | +8,5 p.p. |
| 43 | 218 | 182 | 54,5% | +9,0 p.p. |
| 71 | 222 | 178 | 55,5% | +11,0 p.p. |
| 101 | 217 | 183 | 54,2% | +8,5 p.p. |

## Correção aplicada

A regra principal de velocidade não mudou. A correção atua apenas quando duas
ou mais unidades têm a mesma velocidade:

1. as ações dos dois lados são intercaladas, em vez de executar todo o lote de
   um lado;
2. a seed define qual lado abre os empates na primeira rodada;
3. essa prioridade troca de lado a cada rodada.

Isso preserva determinismo e replay, distribui a abertura entre os assentos e
evita que um exército inteiro ataque antes de o oponente responder. Nenhum
atributo de unidade, custo, renda, dano, alvo ou heurística de bot foi alterado.

## Cobertura de regressão

Os testes verificam que:

- ações de mesma velocidade intercalam `1, 2, 1, 2`;
- a prioridade inverte na rodada seguinte;
- seeds pares e ímpares distribuem a abertura entre os dois lados;
- torneios agregam corretamente várias seeds e contabilizam iniciativa;
- uma amostra curta com todo o elenco mantém a diferença absoluta em até 10
  pontos percentuais.

## Limites da conclusão

A iniciativa ainda tem efeito real: em um empate de velocidade com dano letal,
agir primeiro continua sendo valioso. O objetivo desta correção mínima é reduzir
e distribuir esse efeito, não simular dano simultâneo. A amostra também mede os
bots e atributos atuais; mudanças futuras de composição devem repetir o
benchmark e ajustar o limite do teste somente com evidência nova.
