# Rubrica — Tese de página

A tese é a frase única que deve cumprir pelo menos 70% do objetivo estratégico da
página. Se o visitante ler só ela, precisa produzir identificação suficiente para
ele pensar "isso é para mim" ou "é exatamente esse o meu problema".

Avalie como o visitante do ICP declarado no briefing, com pressa, num objetivo
próprio, sem interesse nenhum em quem escreveu. Não avalie como marketeiro.

## Reprovação automática

Qualquer uma zera a avaliação. Registre a regra violada e pare.

- **R1** — A frase descreve o que a empresa é, tem ou faz, em vez da situação do visitante.
- **R2** — Depende de uma segunda frase para fazer sentido.
- **R3** — Afirma benefício, número ou garantia que `00-briefing/` e `01-contexto/` não sustentam.
- **R4** — Usa a construção "Não é X, é Y" / "Mais que A, é B".
- **R5** — Exige vocabulário que o visitante não usa na rotina dele (jargão de categoria, nome de mecanismo proprietário, sigla interna).
- **R6** — Explica arquitetura, fluxo ou papéis antes de nomear a situação do visitante.

## Critérios (0-20 cada)

**1. Teste dos 70%** — Se o visitante ler só esta frase, a página ainda cumpre 70% da
missão declarada na ficha da página? 20 = sim, sozinha basta. 10 = cumpre metade.
0 = a frase não avança a missão.

**2. Ponto de vista** — A frase fala do problema, desejo, medo, tensão ou decisão do
visitante? 20 = a situação dele é o sujeito. 10 = mistura situação e solução.
0 = a empresa ou o produto é o sujeito.

**3. Identificação e recorte** — Alguém fora do ICP se reconheceria nela? Deve
identificar o ICP e deixar os outros de fora. 20 = o ICP se reconhece e mais ninguém.
10 = o ICP se reconhece mas serve a qualquer um. 0 = ninguém se reconhece.

**4. Autossuficiência** — Funciona sem subtítulo, sem o bloco seguinte, sem contexto
de marca, fora do site? 20 = funciona isolada. 0 = precisa de andaime.

**5. Compressão** — Está no menor número de palavras que ainda produz identificação?
Penalize subordinada que só repete, adjetivo que não muda a decisão, aposto explicativo.

## Veredito

| Total | Sem reprovação automática | Destino |
|---|---|---|
| ≥ 85 | aprova | próximo estágio |
| 70-84 | revisa | volta ao produtor, rodada+1 |
| < 70 ou qualquer R | refaz | volta à produção, defeito estrutural nomeado |

## Formato da crítica

```markdown
---
ficha: {id}
artefato: {caminho}
rubrica: tese
rodada: {n}
veredito: aprova | revisa | refaz
total: {0-100}
---
## Notas
70%: x/20 · Ponto de vista: x/20 · Identificação: x/20 · Autossuficiência: x/20 · Compressão: x/20

## Reprovações automáticas
- R{n} — {variante citada} — {por quê}

## Defeitos
- {variante ou linha} — {o que está errado} — {qual critério ou regra}

## O que sobreviveu
{as variantes que passariam, e por quê. Nunca omitir esta seção.}
```

O crítico não escreve a versão corrigida. Nomeia o defeito e devolve.
