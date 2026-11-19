# Email

Email é o canal que o remetente controla e o canal em que texto genérico custa mais: o leitor concedeu acesso uma vez e pode revogar para sempre. Cada email precisa justificar o próximo.

Leia o brand-context. Antes de entregar, revise com a skill `anti-slop-ptbr` quando disponível.

## Antes de escrever

Estabeleça, inferindo quando possível:
1. **Tipo de sequência**: boas-vindas, nutrição, lançamento, reativação, abandono, onboarding, follow-up comercial, outbound
2. **O que o leitor acabou de fazer**: o gatilho define o email 1
3. **A conversão única**: sequência com dois objetivos não atinge nenhum
4. **Realidade de envio**: tamanho da base, taxas atuais, ferramenta. Sem linha de base, declare que projeção é impossível.

## Arquiteturas

Quantidade e intervalo são padrões ajustáveis ao ciclo de compra: um produto barato decide em dias; um contrato B2B, em meses.

### Boas-vindas (5 emails: dias 0 / 1 / 3 / 5 / 8)
1. **Entrega + uma ação**: o que foi prometido, na hora, e o próximo passo único
2. **Mecanismo**: por que existe, o que defende, por que funciona
3. **O melhor material**: conteúdo, ferramenta ou caso mais forte, sem pedido
4. **Objeção**: o principal motivo de não comprar, tratado de frente
5. **Oferta direta**: pedido claro, com prazo ou motivo real para agir agora

### Nutrição (6 emails, ~semanal)
Alterna conteúdo e pedido em ~3:1. Cada email de conteúdo vale a abertura sozinho. Rode famílias de ângulo entre envios: problema → mecanismo → prova → contrário → identidade → oferta.

### Lançamento (8 emails em ~10 dias)
1. Problema, sem produto
2. Mecanismo, o que vem aí
3. Abertura com oferta completa
4. Prova + FAQ
5. Desmonte de objeção
6. Caso ou demonstração
7. Últimas 48h: reafirma a oferta sem novidade
8. Horas finais: o email mais curto, um link

**Prazo verdadeiro sempre.** Se a condição não encerra, o email não diz que encerra. Sem prazo real, use custo de esperar.

### Reativação (3 emails)
1. "Ainda quer receber?", sem culpa
2. O melhor do que perdeu
3. Despedida com descadastro por inação; **remova de fato quem não responde**

### Outbound B2B
Primeiro email com até ~120 palavras: gatilho observável da conta, problema provável, uma pergunta. Personalização vem de sinal público e verificável da empresa. Contas e sinais saem do ICP do brand-context; sequência de 3-4 toques com intervalo de dias úteis. Envio continua sujeito a autorização explícita.

## Assunto

- ~40 caracteres sobrevivem ao celular; informação principal no início
- Específico supera engenhoso; curiosidade se desgasta ao longo da sequência
- O texto de pré-visualização é o segundo assunto; escreva deliberadamente
- Assunto que o corpo não cumpre troca abertura barata por clique perdido
- "Re:" e "Enc:" falsos, caixa alta e 🚨 prejudicam entregabilidade e confiança

Gere alternativas de assunto conforme o teste planejado e escolha pelo critério de [conteúdo](content.md).

## Corpo

- Um objetivo, um link principal (pode repetir; não pode competir)
- Escreva para uma pessoa, com o vocabulário dela (avaliações, atendimento, vendas)
- A primeira frase funciona sozinha no painel de pré-visualização
- Parágrafos curtos
- Visual de texto simples rende mais na maioria dos envios B2B
- Assine como pessoa quando a marca permitir
- O P.S. é lido com frequência alta: use para reafirmar a oferta ou um aparte humano

## Entregabilidade mínima

- SPF, DKIM e DMARC configurados antes de enviar volume
- Nunca lista comprada ou raspada
- Remover inativos em cronograma
- Aquecer domínio novo gradualmente
- Descadastro em um clique, visível e respeitado (exigência legal e LGPD)

## Saída

Salve no brief da campanha ou em `clientes/{slug}/entregas/email-{sequencia}-{AAAA-MM-DD}.md`. Escreva todos os emails por inteiro:

```
# {Tipo de sequência} — {produto}
Objetivo: {conversão} · Envios: {n} · Cadência: {dias}

## Email 1 — {função}
Assunto: {escolhido}
Assuntos alternativos: {2}
Pré-visualização: {texto}
---
{corpo completo}
---
Envio: dia X · Segmentação/regras de pulo: {se houver}

## Plano de teste   (uma variável, qual email, o que cada resultado significaria)
## Verificar        (afirmações, prazos e premissas a confirmar)
```

## Métricas

Taxa de abertura ficou pouco confiável com bots e pré-carregamento; pese cliques e respostas. Não projete receita de sequência não enviada; descreva as alavancas. Teste de assunto segue a disciplina de [aprendizado](measurement.md).
