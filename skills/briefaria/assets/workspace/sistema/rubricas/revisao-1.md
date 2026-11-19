# Rubrica — Revisão 1 (compressão e ponto de vista)

Gate que roda sobre `04-texto/` antes de qualquer decisão de imagem, estilo, vídeo,
3D, animação ou layout. Aplica-se **bloco a bloco**, não ao documento inteiro.

## Filtro de existência

Antes de avaliar qualquer bloco: **que pergunta do visitante este bloco responde?**
Se a resposta for vaga, o bloco não deve existir. Marque `REMOVER`.

## As três perguntas

**1. É sobre o usuário ou sobre a empresa?**
Cada frase fala do problema, desejo, decisão ou dúvida do visitante. A empresa entra
quando é necessária para explicar como acontece, por que acreditar ou com quem se
está lidando — e só aí.

Traduções obrigatórias:

| Pergunta da empresa | Pergunta do visitante |
|---|---|
| Como funciona nossa solução | O que eu preciso entender antes de decidir? |
| Nossos diferenciais | Por que eu deveria escolher esse caminho? |
| Benefícios | O que muda para mim? |
| Sobre nós | Por que eu deveria confiar em vocês? |

**2. Tudo que cabe em uma frase está em uma frase?**
Corte explicação, subtítulo redundante, parágrafo e seção criados para repetir ideia
que já cabe numa frase.

**3. Toda ação que cabe em uma palavra está em uma palavra?**
Botão, tab, link e comando reduzidos quando o contexto já explica a ação: Entender,
Comparar, Simular, Conversar, Começar, Enviar, Voltar. O texto ao redor explica; a
ação só age.

**4. Consequência.** Se o bloco puder ser removido sem prejudicar a decisão do
visitante, deve ser removido.

## Estrutura verbal mínima

Fora de páginas cujo objetivo dominante é Informar, a página se reduz a quatro peças.
Bloco que não for uma delas precisa justificar existência pelo filtro acima.

| Peça | Pergunta mental | Missão |
|---|---|---|
| Tese | É para mim? | Gera identificação. |
| WHY | Por que dar o próximo passo? | Por que resolver assim faz sentido para o visitante. |
| FAQ | O que ainda pode me impedir? | Remove fricção real. Não é depósito de conteúdo restante. |
| CTA | Qual é o próximo passo? | Ação clara, curta, coerente com a decisão já construída. |

## Saída

Uma linha por bloco:

```
{bloco} · {MANTER | COMPRIMIR | REESCREVER | REMOVER} · {pergunta do visitante que ele responde, ou "nenhuma"} · {defeito}
```

Veredito da página: `aprova` se nenhum bloco for REESCREVER ou REMOVER; `revisa` se
houver até dois; `refaz` acima disso ou se a tese não sobreviver.
