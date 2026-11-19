# Motor de hooks

Os primeiros 1-3 segundos decidem se o restante do anúncio ou vídeo é visto. Este módulo gera hooks por método e diagnostica qual camada falhou quando o desempenho cai. É usado por [anúncios](paid-ads.md), [conteúdo](content.md), [social](social.md) e [concorrência](competitive.md).

## Três componentes

Um hook de vídeo tem três componentes simultâneos, cada um com uma carga diferente:

1. **Ação visual**: o que acontece na tela no primeiro segundo; ganha a parada
2. **Fala**: a primeira frase dita (pessoa ou voiceover); abre o argumento
3. **Texto em tela**: legenda ou sobreposição; acrescenta a aposta ou o chamado ao público

Regra de não duplicação: se o texto repete a fala, um dos dois foi desperdiçado. Em peça estática a mesma regra vale para visual, headline e linha de apoio. Escreva os três em todo hook:

> Visual: mão rasgando um boleto vencido ao meio
> Fala: "Esse cliente comprou de novo. A prazo."
> Texto: "distribuidor: leia isto"

## Corpus antes de gerar

Hook escrito de imaginação converge para os mesmos clichês. Monte o corpus:
- anúncios vencedores da conta e os anúncios de concorrente com mais tempo no ar (Meta Ad Library, Google Ads Transparency Center)
- avaliações de clientes: G2, Reclame Aqui, Google Meu Negócio, comentários em marketplaces
- comentários sob anúncios e posts da marca e dos concorrentes
- transcrições de vendas e atendimento quando o cliente fornecer (ver `aprendizados.md` do cliente)
- discussões da categoria em comunidades e grupos

Frase literal do cliente supera paráfrase do marketing. Cite a fonte de cada hook na matriz. Sem corpus disponível, gere mesmo assim e rotule o lote como *hipóteses sem base, validar com custo baixo*.

## Sequência de geração

1. **Segmento**: um segmento por lote; use os papéis e públicos do brand-context
2. **Motivação**: a dor ou o desejo, nas palavras do corpus
3. **Tática**: da taxonomia abaixo, espalhando o lote por várias táticas
4. **Formato**: talking head, demonstração, estático, UGC, tela dividida, screencast; tática × formato = um hook

A quantidade segue o pedido e o teste planejado. Um lote exploratório se beneficia de pelo menos 6 táticas diferentes; a correção de um hook dispensa matriz.

## Taxonomia de táticas

| # | Tática | O que é | Diferente de | Falha quando |
|---|---|---|---|---|
| 1 | Chamado | Nomeia o público na primeira linha | Identidade (papel × autoimagem) | O chamado é mais amplo que a segmentação |
| 2 | Pergunta | Abre uma questão que o espectador quer resolver | Lacuna de curiosidade | A resposta é "não" e rolagem |
| 3 | Contrário | Ataca uma crença que o público tem | Contraste | A crença atacada é espantalho |
| 4 | Contraste | Antes/depois ou nós/eles lado a lado | Contrário | O "antes" não é reconhecível como o presente do espectador |
| 5 | Demonstração | O produto fazendo a coisa difícil, sem preparação | Resultado | A demonstração precisa de contexto para impressionar |
| 6 | Quebra de padrão | Algo visualmente estranho ao feed | Demonstração | A quebra não tem relação com a mensagem |
| 7 | Dado de abertura | Um número que reenquadra o problema | Prova social | Número redondo, sem fonte ou inacreditável |
| 8 | Perda | O que o status quo custa agora | Agitação no corpo | O público ainda não reconhece o problema |
| 9 | Resultado | O estado depois, específico | Demonstração | Resultado genérico ("economize tempo e dinheiro") |
| 10 | Testemunha | Pessoa real no meio da experiência, linguagem UGC | Depoimento | Produção polida quebra a leitura de pessoa real |
| 11 | Autoridade | A credencial fala primeiro | Prova social | A credencial não sustenta a afirmação |
| 12 | Prova social | Volume e consenso | Autoridade | O número não pode ser comprovado; nunca invente |
| 13 | História em andamento | Começa no conflito, sem preâmbulo | Testemunha | O desfecho não chega até o fim da sequência inicial |
| 14 | Resposta implícita | Monta a situação para o espectador concluir | Pergunta | O salto de inferência é grande demais |
| 15 | Inimigo comum | Alia-se ao espectador contra o jeito antigo, o incumbente | Contrário | O inimigo é uma escolha passada do próprio espectador |
| 16 | Cavalo de Troia | Formato nativo (print de notas, conversa de WhatsApp, resposta a comentário) | Quebra de padrão | A revelação parece traição |
| 17 | Lacuna de curiosidade | Retém o mecanismo e promete revelar | Pergunta | A revelação não entrega o prometido |
| 18 | Identidade | Espelha a autoimagem | Chamado | Bajula em vez de reconhecer |

Táticas 7, 11 e 12 dependem da seção Provas do brand-context. Prova travada bloqueia a tática; não substitua por número plausível.

## Sequência inicial

Os segundos 3-15 estendem a premissa do hook. Quem parou por "Esse cliente comprou de novo. A prazo." fica para saber como; tour de funcionalidades perde a pessoa. Todo teste de hook também testa a sequência inicial: se ela mudou junto, o veredito sobre o hook é inconclusivo.

## Funil de diagnóstico

Leia de cima para baixo e corrija só a primeira etapa quebrada.

| Métrica | Isola | Se quebrada, corrigir |
|---|---|---|
| Thumbstop (views 3s / impressões) | Visual + texto em tela | Ação visual, primeiro quadro |
| Retenção (views 15s / views 3s) | Fala + sequência inicial | Extensão da premissa |
| CTR (com retenção saudável) | Argumento + clareza do CTA | Oferta como dita no anúncio |
| Conversão (com CTR saudável) | Pós-clique | Página de destino, coerência com o anúncio ([auditoria](audit.md)); parar de mexer no anúncio |

Corrigir problema de conversão com hooks novos é o desperdício mais comum em teste criativo.

## Escada de fidelidade

Custo de produção acompanha a evidência. Neste repo:

1. **Degrau 1: texto e estáticos simples.** Ângulos novos saem como estático ou carrossel pela skill `imagen`, ou texto em tela sobre take existente.
2. **Degrau 2: movimento barato.** Ângulos que sobrevivem ganham leitura UGC, screencast gravado ou corte com `video-clips` e `voiceover`.
3. **Degrau 3: produção.** Só ângulo validado entra no pipeline completo (`pipeline-operator` → `render`).

Pular degrau produz um anúncio bonito de argumento não provado. Ângulo provado em formato não testado vem antes de ângulo novo em formato provado.

## Formatos estáticos

1. Tabela nós × eles: duas colunas, 4-6 linhas
2. Dado em destaque: um número grande, uma linha de contexto, fonte
3. Card de avaliação: avaliação real com nome e autorização
4. Antes/depois: dois painéis, uma legenda cada
5. Bilhete do fundador: carta em texto simples, assinada
6. Card de FAQ: a objeção mais dura e a resposta honesta
7. Checklist: "sinais de que você precisa de X", 4-5 itens
8. Recibo comparativo: custo do jeito antigo item a item contra uma linha do novo
9. Print nativo: notas do celular ou conversa de WhatsApp com o argumento
10. Headline sobre produto: produto ou tela com uma afirmação forte
11. Citação ampliada: uma frase de cliente em tipo grande
12. Card de oferta: oferta, âncora, reversão de risco

Cada estático passa pela checagem de três componentes.

## Saída

Salve no brief da campanha ou em `clientes/{slug}/entregas/hooks-{assunto}-{AAAA-MM-DD}.md`:

```
# Matriz de hooks — {marca / segmento}
{data} · Corpus: {fontes} · {n} hooks em {n} táticas

| # | Tática | Formato | Visual | Fala/Headline | Texto/Apoio | Fonte do corpus |

## Primeiros testes recomendados   (3-5 hooks, por quê, lacuna de cobertura que preenchem)
## Plano de escada                 (o que sai como estático agora, o que ganha movimento se sobreviver)
```

## Encaminhamentos

- Brief de produção dos hooks vencedores → [anúncios](paid-ads.md)
- Texto após a sequência inicial → [conteúdo](content.md)
- Roteiro de vídeo a partir do hook → `pipeline-operator`, fase roteiro
- Agrupar hooks de concorrente → [concorrência](competitive.md)
