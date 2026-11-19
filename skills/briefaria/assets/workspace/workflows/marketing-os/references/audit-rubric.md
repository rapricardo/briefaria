# Rubrica de auditoria

Pontue cada dimensão de 0 a 100. Escolha a faixa cuja descrição é verdadeira na maior parte e ajuste até ±7 dentro dela.

## Faixas

| Faixa | Significado |
|---|---|
| 90-100 | Referência da categoria; serviria de exemplo para outros |
| 75-89 | Forte; execução competente, lacunas pequenas |
| 60-74 | Funcional e genérico; a maioria dos sites B2B está aqui |
| 40-59 | Perdendo resultado; problemas que um operador competente corrigiria nesta semana |
| 20-39 | Quebrado; a dimensão trabalha contra o negócio |
| 0-19 | Ausente ou prejudicial |

Calibração: a mediana de sites reais fica entre 55 e 70. Se a maioria das notas passar de 80, as faixas derivaram.

## 1. Mensagem e posicionamento (25%)

| Sinal | Alto | Baixo |
|---|---|---|
| Teste de 5 segundos | Um estranho diz o que é e para quem | Exige rolar ou deduzir |
| Especificidade | Resultado, número e público nomeados | "Transformar", "potencializar", "next level" |
| Diferenciação | Diz o que faz que as alternativas não fazem | Afirmações que qualquer concorrente assinaria |
| Jargão | Linguagem que o comprador usa | Vocabulário interno, categoria inventada |
| Consistência | Headline, subtítulo e CTA defendem a mesma coisa | Três propostas de valor na mesma página |

Teto de 60: a headline não nomeia público nem resultado.

## 2. Conversão (20%)

| Sinal | Alto | Baixo |
|---|---|---|
| Hierarquia de CTA | Uma ação principal dominante | 4+ CTAs com o mesmo peso |
| Texto do CTA | Diz o que acontece em seguida | "Saiba mais", "Enviar" |
| Atrito | Número de campos proporcional ao compromisso | Formulário longo para conversa inicial |
| Objeções | As 3 principais respondidas na página | Ausentes ou enterradas no FAQ |
| Posição da prova | Ao lado da afirmação que sustenta | Faixa de logos isolada |
| Reversão de risco | Garantia, teste ou condição clara perto do CTA | Ausente |

Teto de 50: sem CTA principal claro na primeira dobra.

## 3. Busca e descoberta (20%)

| Sinal | Alto | Baixo |
|---|---|---|
| Title | Único, termo principal no início, até ~60 caracteres | Só a marca, ou truncado |
| Meta description | Escrita para o clique | Ausente, duplicada ou automática |
| Headings | Um H1, hierarquia lógica | Vários H1, heading usado como estilo |
| Intenção | A página responde à busca que mira | Home mirando consulta informacional |
| Links internos | Links contextuais para aprofundamento | Só menu |
| Citabilidade | Respostas diretas, dados estruturados, fatos extraíveis | Prosa promocional sem fato extraível |

Aprofundamento de busca por IA fica em [GEO](geo.md).

## 4. Posição competitiva (15%)

| Sinal | Alto | Baixo |
|---|---|---|
| Categoria | Clara sobre contra o que compete | Ambígua |
| Alternativas | Conteúdo de comparação honesto | Finge não ter concorrente |
| Troca | Caminho de migração tratado | Ignorado |
| Defensabilidade | Razões difíceis de copiar | Paridade de funcionalidades |

Confira a página equivalente dos três concorrentes óbvios. Se os quatro dizem a mesma coisa, teto de 55.

## 5. Confiança (10%)

| Sinal | Alto | Baixo |
|---|---|---|
| Especificidade | Resultado nomeado, com fonte | "Líder de mercado", "confiança de grandes empresas" |
| Tipo de prova | Pessoas, empresas e números verificáveis | Depoimentos anônimos, banco de imagem |
| Terceiros | Avaliações, certificações, imprensa com link | Selos autodeclarados |
| Design | Consistente, atual, sem elementos quebrados | Template padrão, inconsistente |
| Transparência | Preço, equipe, segurança e contato acessíveis | Algum deles escondido |

Em finanças e saúde, verifique também as restrições do brand-context: claim proibido derruba a dimensão independentemente da execução.

## 6. Crescimento e retenção (10%)

| Sinal | Alto | Baixo |
|---|---|---|
| Preço/condição | O comprador se qualifica sem ligação | Só "fale conosco" sem referência |
| Aquisição | Várias portas de entrada, recurso gratuito | Só a home |
| Expansão | Caminho de upgrade visível | Oferta única e plana |
| Ciclo de vida | Onboarding, ativação e reengajamento inferíveis | Nada inferível |

"Fale conosco" como única condição pode ser decisão deliberada de venda consultiva; registre como escolha e avalie se a página compensa com outro sinal de qualificação.

## Total

```
total = 0,25·mensagem + 0,20·conversão + 0,20·busca
      + 0,15·competitivo + 0,10·confiança + 0,10·crescimento
```

Arredonde ao inteiro mais próximo.

Dimensão não inspecionada não recebe média. Reporte o total sobre o peso inspecionado e declare o denominador: "68/100 sobre 85% das dimensões; preço inacessível".

| Peso inspecionado | Saída permitida |
|---|---|
| ≥80% | Nota completa, com denominador |
| 60-79% | Nota **provisória**, com dimensões ausentes nomeadas |
| <60% | Sem nota geral; achados e "evidência insuficiente para nota" |

Cada sinal recebe um de quatro vereditos: passa, falha, desconhecido, não se aplica. Desconhecido reduz cobertura e não reduz nota.
