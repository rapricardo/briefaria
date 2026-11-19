# Comportamento por motor

Os motores diferem o bastante para que um checklist único seja impreciso. O conteúdo abaixo é comportamento observado e orientação publicada, sem critério documentado de citação. **Verifique antes de usar**: essas superfícies mudam em semanas.

## Google AI Overviews / AI Mode

Base: principalmente páginas que já performam na busca orgânica. Ranquear é quase pré-requisito; citabilidade converte ranking em citação.

Move: fundamentos de SEO (o único motor em que eles sustentam o resultado), extraibilidade por trecho, dados estruturados de entidade (`Organization`, `Product`, `Article` com `author` e `datePublished` reais), experiência de primeira mão (autor nomeado com credencial, metodologia, imagem original), frescor em temas sensíveis a tempo.

Schema: o Google retirou os rich results de `HowTo` em 2025 e restringiu os de `FAQPage` para a maioria dos sites. A marcação ainda ajuda compreensão e custa pouco, mas não prometa exibição. Confira a lista atual de rich results antes de recomendar schema para exibição.

Não move: densidade de palavra-chave, páginas de comparação rasas em escala. Schema que não corresponde ao conteúdo visível viola as diretrizes do Google.

A orientação publicada pelo Google é fonte primária; conselho de terceiros, incluindo este arquivo, é secundário.

## ChatGPT (com busca)

Base: recuperação ao vivo somada ao conhecimento prévio do modelo sobre a marca.

Move: consistência de entidade na web aberta, presença nas listas que respondem à pergunta, HTML limpo e rápido, recência, `OAI-SearchBot` liberado quando o cliente quer o tráfego.

Ponto explorável: o modelo descreve marcas a partir de conhecimento desatualizado. Pergunte o nome da marca diretamente e registre a resposta. Corrige-se descrição errada ajustando as fontes que a corroboram.

## Perplexity

Base: recuperação ao vivo agressiva, muitas fontes por resposta, citações visíveis.

Move: resposta direta no topo da página, amplitude de corroboração (ser uma de oito fontes é realista), recência, presença em comunidades para perguntas de opinião, `PerplexityBot` liberado.

É o motor mais barato de medir semana a semana; use como superfície principal de medição.

## Claude, Copilot, Gemini e outros

As táticas específicas não estão estabelecidas. Aplicam-se as alavancas gerais: estrutura extraível, densidade factual com fonte, consistência de entidade e acesso do crawler. Não invente tática específica.

## llms.txt

Arquivo markdown em `/llms.txt` listando páginas-chave com descrições curtas. A adoção é marginal e nenhum motor grande confirmou publicamente que o consome. Recomende como item barato de higiene quando o site tem documentação ou biblioteca grande de conteúdo; nunca como alavanca de citação.

```markdown
# Nome da empresa

> Frase única dizendo o que a empresa faz e para quem.

## Páginas principais
- [Como funciona](https://exemplo.com.br/como-funciona): o que cobre
- [Para quem é](https://exemplo.com.br/para-quem): o que cobre
```

## Crawlers

| Motor | User-agent |
|---|---|
| OpenAI (busca) | `OAI-SearchBot` |
| OpenAI (treino) | `GPTBot` |
| Perplexity | `PerplexityBot` |
| Anthropic | `ClaudeBot` |
| Google, opt-out de treino de IA | `Google-Extended` |

Apresente o trade-off. Bloquear `GPTBot` reduz exposição em treino e pode reduzir citação. Bloquear `Google-Extended` não remove o site do AI Overviews. Confirme as strings atuais antes de escrever no `robots.txt` do cliente.
