# Posicionamento, oferta e preço

Módulo mais a montante. Quando testes de copy dão resultado plano, anúncios cansam rápido e auditorias acusam mensagem genérica, a causa costuma estar aqui. Diga isso quando perceber: reescrever palavras sobre posicionamento fraco desperdiça o trimestre.

Leia o brand-context do cliente e a decisão vigente que ele aponta. Este módulo também produz as seções Produto, Público e Posicionamento do brand-context; uma conclusão aprovada atualiza esse arquivo.

## Posicionamento

Posicionamento é o conjunto de decisões sobre com o que o produto é comparado, para que o mercado consiga situá-lo e precificá-lo sem esforço. Tagline é consequência.

### Os cinco insumos, nesta ordem

1. **Alternativas reais**: o que o cliente faria sem o produto, incluindo planilha, estagiário, banco tradicional e não fazer nada. "Não fazer nada" lidera a maioria das categorias.
2. **Atributos exclusivos**: o que o produto tem e as alternativas não: funcionalidade, modelo de negócio, dados, distribuição, velocidade, estrutura de preço.
3. **Valor**: o que esses atributos permitem, traduzido em resultado pelo qual alguém paga.
4. **Segmento de melhor encaixe**: quem sente esse valor com mais intensidade. Posicione para quem precisa comprar, e não para todos que poderiam.
5. **Moldura de categoria**: o contexto de mercado que torna o valor óbvio. O mesmo produto pode ser "um X mais barato", "um Y para {segmento}" ou "uma categoria nova"; cada moldura define expectativa, concorrente e âncora de preço.

### Declaração

```
Para {segmento de melhor encaixe}
que {situação ou dor que torna a compra necessária},
{produto} é {moldura de categoria}
que {a afirmação de valor},
diferente de {a alternativa principal},
porque {o atributo exclusivo que torna a afirmação crível}.
```

Teste cada cláusula: o concorrente mais próximo poderia colar o próprio nome nela? Se sim, a cláusula é decoração. Retrabalhe até que pelo menos o par "diferente de / porque" seja exclusivo.

### Sinais de que o posicionamento é o problema

- Variantes fortes de copy produzem resultados iguais → o argumento falha, e as palavras não importam
- Reuniões de venda exigem longa explicação do que o produto é → falha de moldura de categoria
- Objeção de preço domina → âncora de alternativa errada (comparam com algo mais barato que o comparável real)
- Vitórias concentradas em segmento que ninguém mira → o mercado achou a posição; siga-o

## Oferta

A oferta é o acordo, e o acordo costuma pesar mais que a descrição dele. Quatro eixos:
- **Resultado desejado**: concreto, nomeado, o que o comprador contaria a um colega
- **Probabilidade percebida**: prova, especificidade, garantia, histórico. A maioria das ofertas fracas falha aqui: a promessa é boa e ninguém acredita.
- **Tempo até o primeiro resultado**: encurte reorganizando o início antes de reescrever a promessa
- **Esforço e sacrifício**: cada passo removido vale mais que uma funcionalidade adicionada

Fortalecimento, do mais barato ao mais caro:
1. **Reversão de risco**: teste, piloto, condição sem compromisso, pagamento por resultado. Se o cliente recusa todas, pergunte o motivo; a resposta costuma revelar falta de confiança na própria retenção.
2. **Caminho rápido**: um primeiro valor em pouco tempo, mesmo que o valor completo leve semanas
3. **Prova nomeada**: um resultado específico e verificável supera cinco depoimentos anônimos; respeite as Provas travadas do brand-context
4. **Pacote explícito**: enumerar o que está incluído e o valor de cada parte
5. **Escassez real**: capacidade, turma, mudança de preço de fato. Urgência fabricada custa reputação permanente. Sem escassez real, use custo de esperar.

## Preço

A camada estratégica que o marketing controla:

- **A métrica pesa mais que o valor**: por usuário, por uso, por resultado, por transação, fixo. A métrica certa cresce com o valor que o cliente recebe.
- **Três níveis** por padrão: âncora, alvo e entrada. Um nível perde o efeito de âncora; cinco viram projeto de comparação.
- **"Fale conosco" como único preço** filtra para venda consultiva e elimina autoatendimento. Pode ser deliberado; registre quando for.
- **Página de preço** responde acima da dobra: quanto custa, o que inclui, qual é o meu. Nomeie níveis pelo comprador ("Revenda / Rede / Indústria") e não por adjetivo. O FAQ abaixo da tabela trata as três objeções reais.
- **Reajuste**: novo preço primeiro para novos clientes; comunique pelo que foi entregue desde o último preço.

Restrições do brand-context prevalecem: se o cliente proíbe taxas ou simuladores em página, a recomendação de preço fica no material interno e de vendas.

## Saída

Salve em `clientes/{slug}/estrategia/posicionamento.md` com frontmatter `status: proposta` e `data`. Quando a pessoa responsável aprovar, o status passa a `vigente`, o anterior vai para `_arquivo/`, a decisão entra em `decisoes.md` (moldura escolhida e rejeitada, uma linha cada) e o brand-context é atualizado na mesma mudança.

```
# Posicionamento e oferta — {produto}

## Declaração          (seis cláusulas, com as exclusivas marcadas)
## Decisão de moldura  (moldura escolhida, o que ganha, o que custa, alternativa rejeitada e por quê)
## Oferta              (oferta atual nos quatro eixos / oferta redesenhada / diferenças)
## Preço               (estrutura recomendada, tabela de níveis, respostas acima da dobra)
## Cascata             (páginas, anúncios, emails e materiais que precisam de retrabalho)
## O que não consegui determinar
```

## Honestidade

Posicionamento é hipótese até o mercado responder. Apresente a moldura principal e a alternativa rejeitada mais forte, com a evidência de cada. Preço sem dado de disposição a pagar é palpite estruturado; diga qual pesquisa (cinco entrevistas já ajudam) transformaria o palpite em decisão. Não fabrique atributo exclusivo: se nada for exclusivo, esse é o achado, e ele vai para a liderança do cliente antes de ir para a copy.

## Encaminhamentos

- Execução de página, anúncio e email → [conteúdo](content.md), [email](email.md)
- Mapa de concorrentes para a moldura → [concorrência](competitive.md)
- Prioridade e calendário da cascata → [estratégia](strategy.md)
