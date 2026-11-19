# Auditoria de site e funil

Transforma uma URL em documento de decisão: o que está quebrado, quanto custa, o que corrigir primeiro e com que confiança.

## Antes de começar

Leia `clientes/{slug}/brand-context.md`. Em auditoria de concorrente ou prospect, leia o brand-context do cliente que contratou a análise. Sem brand-context, faça a auditoria e declare no relatório que os achados estão sem contexto de marca.

Defina o registro pelo pedido: site próprio (lista de correção direta), prospect (abre pelo custo do problema e pelo que já funciona) ou concorrente (inteligência analítica, sem julgamento de qualidade). Pergunte só se a conversa não deixar claro.

## Fluxo

### 1. Reconhecimento

Busque a URL e, quando existirem, a página de preço ou oferta, uma página de produto, a página institucional e o conteúdo mais visitado. Cinco páginas bastam. Registre headline, subtítulo, cada CTA com o texto exato, modelo de preço, provas visíveis e as três primeiras objeções de um comprador cético.

### 2. Análise em seis dimensões

Com subagentes disponíveis, rode uma dimensão por subagente, em paralelo, cada um com a URL, o brand-context e seu trecho de `audit-rubric.md`. Sem subagentes, siga a ordem da tabela; mensagem informa conversão.

| # | Dimensão | Peso | O que examina |
|---|---|---|---|
| 1 | Mensagem e posicionamento | 25% | Clareza da proposta, especificidade da headline, diferenciação, jargão, entendimento em 5 segundos |
| 2 | Conversão | 20% | Hierarquia e texto dos CTAs, atrito de formulário, objeções, posição das provas, reversão de risco |
| 3 | Busca e descoberta | 20% | Title/meta, estrutura de headings, intenção de busca, links internos, indexação, citabilidade em IA |
| 4 | Posição competitiva | 15% | Categoria declarada, alternativas nomeadas, custo de troca, o que os três concorrentes óbvios dizem |
| 5 | Confiança | 10% | Densidade e especificidade de prova, validação de terceiros, sinais de design, transparência |
| 6 | Crescimento e retenção | 10% | Legibilidade de preço, superfícies de aquisição, expansão, ciclo de vida |

Por dimensão: nota 0-100 pela rubrica, os três achados de maior valor e uma coisa que já funciona. Sempre inclua o que funciona; relatório só negativo perde credibilidade.

Leia `audit-rubric.md` antes de pontuar. Nota sem rubrica é pior que ausência de nota.

### 3. Síntese

Calcule o total ponderado e identifique o padrão comum aos achados, por exemplo: "os problemas de conversão decorrem da headline não dizer para quem é o produto". Classifique cada achado em impacto × esforço. O plano de ação é o quadrante alto impacto/baixo esforço, em ordem; o resto vai para o apêndice.

Se o problema estiver na oferta ou no posicionamento, diga isso. Copy melhor não corrige oferta fraca; encaminhe para [posicionamento](positioning.md).

### 4. Relatório

Salve em `clientes/{slug}/entregas/auditoria-{dominio}-{AAAA-MM-DD}.md`:

```
# Auditoria — {domínio}
{data} · Nota: XX/100 (sobre N% das dimensões) · Base: {páginas acessadas}

## O ponto central
## Placar        (dimensão, nota, peso, contribuição, veredito de uma linha)
## Corrigir primeiro   (3-5 itens: o quê, por quê, texto substituto escrito, esforço P/M/G, confiança A/M/B)
## O que já funciona
## Achados completos   (por dimensão)
## O que não consegui determinar
## Apêndice: itens de menor prioridade
```

Escreva o texto substituto. "A headline é vaga" não é entregável; "trocar *Transforme sua operação* por *{headline nova}*" é.

## Disciplina de nota

As notas são heurísticas de julgamento de marketing e não medem desempenho. Declare isso no relatório. Dimensão não inspecionada fica sem nota; aplique a regra de cobertura da rubrica. Não ancore em nota sugerida pelo usuário: forme a sua e compare depois.

Diagnóstico interno de material (nota de auditoria, score de copy) é legítimo e não pode aparecer em material externo do cliente.

## Encaminhamentos

- Achados de copy → [conteúdo](content.md), levando os achados sem refazer a pesquisa
- Visibilidade em busca por IA → [GEO](geo.md)
- Qualidade do tráfego pago → [anúncios](paid-ads.md)
- Lacunas descobertas no brand-context → registrar na seção Lacunas do brand-context
