---
name: video-script
description: |
  Cria roteiros de video usando o metodo das 5 linhas. Use quando o usuario pedir
  roteiro de video, script de video, voice over, "quero gravar um video sobre X",
  "me ajuda com o roteiro", ou qualquer mencao a producao de conteudo em video.
---

# Video Script — Roteiros com o Metodo das 5 Linhas

Skill para producao de roteiros de video com estrutura narrativa solida.

## Filosofia

Todo bom video conta uma historia. O metodo das 5 linhas garante que, antes de
escrever qualquer palavra do roteiro, voce tenha o esqueleto emocional definido.
As 5 linhas, sozinhas, devem contar a historia completa.

## Workflow de Producao

### Etapa 1 — Coleta de Insumos

Quando o usuario pedir um roteiro, pergunte:

1. **O que sera o video?** (tema, produto, demonstracao, conceito)
2. **Qual o publico-alvo?** (quem vai assistir, qual a dor principal)
3. **Qual a duracao alvo?** (2-5 min / 5-10 min / 10-20 min)
4. **Canal principal?** (YouTube / LinkedIn / Instagram / Multi-canal)

Nao prossiga sem pelo menos os itens 1 e 2 claros.

### Etapa 2 — Nucleo Narrativo (As 5 Linhas)

Construa as 5 linhas junto com o usuario:

1. **Situacao** — Onde o personagem (publico-alvo) esta hoje? O que acontece no dia a dia dele?
2. **Desejo** — O que ele quer alcancar? (gera curiosidade no espectador)
3. **Conflito** — O que impede? Sem conflito nao ha historia. Aqui mora a dor real.
4. **Mudanca** — O ponto de virada. A nova perspectiva, ferramenta ou metodo que muda tudo.
5. **Resultado** — A nova realidade. Como o mundo ficou diferente em relacao ao inicio?

**Exemplo aplicado:**

1. Situacao: Dono de agencia contrata um novo funcionario. Semanas de onboarding. O melhor talento para de produzir para treinar o novato.
2. Desejo: Que cada pessoa nova chegue produzindo no dia 1.
3. Conflito: A operacao vive na cabeca das pessoas. Cada saida reinicia o ciclo do zero.
4. Mudanca: O novo funcionario abre a IA, pergunta "qual e meu papel?" e recebe ficha de cargo, workflow e proximos passos — sem ninguem parar pra explicar.
5. Resultado: Funcionario opera no dia 1. Dono supervisiona a operacao com uma pergunta. Crescimento descolou da contratacao.

### Etapa 3 — Construcao do Roteiro (3 Atos)

Com as 5 linhas definidas, expandir para o roteiro completo:

#### ATO 1 — INTRO (Tom: provocativo)

Estrutura:
1. **Gancho** (5-15s) — Pergunta provocativa ou afirmacao contraintuitiva
2. **Exploracao do problema** (15-45s) — Desenvolver a dor com dados ou cenarios
3. **Ponte para demonstracao** — Frase de transicao que anuncia o que vem

Como as 5 linhas alimentam: Situacao + Desejo + Conflito viram a intro.

#### ATO 2 — DEMONSTRACAO (Tom: didatico, objetivo)

O tom muda: sai do provocativo, entra no instrutivo. O espectador precisa
entender o que esta vendo sem esforco.

Regras:
- Descreva o que esta na tela como se o espectador visse pela primeira vez
- Conecte cada acao ao beneficio que ela gera
- Frases curtas, pausas naturais entre blocos

Como as 5 linhas alimentam: a Mudanca e a demonstracao vivida na tela.

#### ATO 3 — ENCERRAMENTO (Tom: posicionamento + CTA)

Estrutura:
1. **Sintese** (10-20s) — Reconectar a demo ao problema da intro
2. **Reforco de posicionamento** — Frase que reafirma a tese central
3. **CTA** — Adaptar ao canal (inscrever, comentar, link, DM)

Como as 5 linhas alimentam: o Resultado fecha o arco.

## Outputs

### Output 1 — Narrativa (Voice Over)

Texto corrido em 3 blocos (INTRO / DEMO / ENCERRAMENTO). Escrito na primeira
pessoa, como narracao falada. Deve soar natural quando lido em voz alta.

### Output 2 — JSON de Cenas (quando solicitado)

```json
{
  "titulo": "Nome do episodio",
  "duracao_alvo": "5-10 min",
  "canal": "YouTube",
  "cenas": [
    {
      "ato": "intro",
      "cena": 1,
      "narracao": "Texto da narracao...",
      "visual": "Descricao do que aparece na tela"
    }
  ]
}
```

## Adaptacao por Canal

Quando o canal for "multi-canal":
- **YouTube**: formato completo
- **LinkedIn**: cortar para 2-3 min, hook de autoplay nos 3 primeiros segundos
- **Instagram/Reels**: 60-90 segundos, gancho + demo compacta + CTA rapido

## Checklist de Qualidade

- [ ] O gancho prende a atencao nos primeiros 5 segundos?
- [ ] A intro explora o problema antes de apresentar a solucao?
- [ ] A demonstracao e didatica e conecta acoes a resultados?
- [ ] O encerramento reconecta ao problema da intro?
- [ ] O tom da intro e provocativo (nao tutorial generico)?
- [ ] O tom da demo e didatico (nao vendedor)?
- [ ] O roteiro cabe na duracao alvo?
- [ ] O arco emocional esta completo? (Situacao -> Resultado)
