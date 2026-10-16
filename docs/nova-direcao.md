# Crônicas da Fronteira: exércitos, turnos e terrenos

## Direção acordada

O foco é um jogo tático comandado pelo jogador. O laboratório continua útil
para testar regras, mas não define a experiência principal.

As referências indicadas pelo autor são BattleCry: Ashes of Berhyte e Guerra
de Cartas. De [BattleCry, da Berzerk Studio](https://www.kongregate.com/en/games/berzerkstudio/battlecry),
interessam a montagem do exército, os equipamentos e a campanha. De
[Card Wars](https://upload.snakesandlattes.com/rules/a/AdventureTimeCardWarsFinnvsJake.pdf),
interessam terrenos, identidades das cartas e combinações entre peças. O jogo
físico e o aplicativo têm regras diferentes; usamos essas referências como
direção, sem assumir que seus sistemas completos serão transplantados.

Visual escolhido: mistura de exércitos medievais com personagens e terrenos
expressivos. Arte original, silhuetas distintas, equipamento legível,
pintura com contornos e contraste entre verde, pergaminho, azul e ferrugem.

## Entregue na primeira etapa — 0.11

- Uma rodada contém preparação, turno completo do jogador, turno completo
  rival e revisão. O jogador começa todas as rodadas desta escaramuça PvE.
- Cada tropa pode agir uma vez. A ordem das ações do jogador fica livre:
  romper a frente antes de usar outra tropa agora pode criar uma sequência.
- A última ação passa a vez. Encerrar antecipadamente dispensa as restantes.
- O rival age uma tropa por comando Python, com origem, alvo, impacto, cura,
  proteção, movimento ou espera apresentados em sequência pela interface.
- Velocidade 1×/2×, conclusão sem animações e respeito a movimento reduzido.
- Salvamento após cada ação aceita, incluindo no meio do turno rival.
- Novo cenário e seis tropas ilustradas no jogo principal; o laboratório
  preserva seus vetores e suas regras.
- A interface passa a destacar Crônicas da Fronteira, nome já presente no jogo.

![Interface real da versão 0.11](images/combate-0.11.png)

[Ver o estudo de direção visual](images/direcao-artistica-v1.png).

## Ritmo: resultado medido, sem promessa de equilíbrio

Foram usadas 60 combinações: cinco bots, três políticas fixas de recrutamento
e quatro seeds (0, 1, 11, 12), com limite de 12 rodadas. O jogador automatizado
prioriza cura e ataques; isso é diagnóstico, não substitui playtest humano.

| Regras | Média de rodadas | No limite | Vitórias do jogador |
| --- | ---: | ---: | ---: |
| 0.10, ações alternadas, renda 6 | 9,32 | 32/60 | 35/60 |
| 0.11, turnos completos, renda 6 | 9,42 | 33/60 | 42/60 |
| Experimento, renda 4 | 8,65 | 25/60 | 48/60 |
| Experimento, renda 3 | 7,78 | 10/60 | 60/60 |

A mudança melhora o controle das sequências, mas **não resolveu a duração**.
A prioridade do jogador aumenta sua vantagem. Reduzir a renda encurtou
partidas e aumentou ainda mais essa vantagem; esses experimentos não foram
aplicados. Os dados completos ficam em [turnos-medicao.json](turnos-medicao.json).

Reprodução atual: python tools/measure_gameplay.py. Para a base anterior,
execute o medidor com --source apontando para a revisão fa8a708. Experimentos
alteraram apenas resource_income de ambas as bases para 3 ou 4, após criar a
sessão. Parâmetros e políticas permaneceram iguais.

## Próximas etapas propostas — ainda não implementadas

1. **Uma missão curta com objetivo concreto.** Tomar e manter a ponte por duas
   rodadas, ou destruir uma máquina de cerco; vitória não depende sempre de
   esvaziar o mesmo forte. Medir tempo humano, decisões e clareza da vitória.
2. **Terrenos que mudam decisões.** Testar três setores (planície, bosque e
   ruína), com espaço limitado e um efeito simples por setor. A formação atual
   de frente/fundo não deve ser confundida com esses novos setores.
3. **Cartas de ordem.** Um pequeno conjunto de manobras com custo e limite por
   turno: deslocar, preparar uma defesa ou concentrar um ataque. Evitar dar
   ações ilimitadas ao lado que já possui mais tropas.
4. **Montagem de tropas.** Separar corpo, equipamento e função, com orçamento
   total de exército. Começar com poucas combinações realmente distintas;
   ampliar elenco quando seus papéis estiverem demonstrados.
5. **Campanha curta e progressiva.** Três missões que ensinem uma novidade por
   vez, liberando equipamentos e cartas por objetivos. Medir repetição antes
   de criar uma campanha longa.

A próxima revisão de ritmo deve também medir vantagem de iniciativa e
capacidade de reação: um turno completo de foco de fogo pode eliminar peças
antes de elas responderem. Terrenos, objetivos e defesas devem criar respostas
legíveis; simplesmente reduzir vida ou renda não demonstrou isso.

## Arte e arquivos

Estudo: docs/images/direcao-artistica-v1.png. Cenário: web/frontier-field-v1.png.
Atlas com seis células (3 × 2): web/frontier-troops-v1.png. Ordem de leitura:
Soldado, Arqueiro, Guardião; Médico, Tanque, Lanceiro. As células são exibidas
por CSS; nenhum código de regras depende da arte.

Imagens geradas com a ferramenta integrada de geração de imagens; prompts
exatos em [art-prompts.json](art-prompts.json). A primeira aplicação usa
animações de apresentação dos sprites (destaque, deslocamento, impacto e
queda), e não esqueletos ou quadros desenhados de ataque. Sprites adicionais,
equipamentos modulares e terrenos com efeitos ficam para etapas próprias.

## Compatibilidade

As regras interativas passam a tactical-v6. Partidas tactical-v5 não são
reinterpretadas com turnos diferentes: a cópia anterior é preservada para
download e pode ser aberta na versão anterior. A versão 0.11 retoma seus
próprios salvamentos, inclusive durante o turno da IA.
