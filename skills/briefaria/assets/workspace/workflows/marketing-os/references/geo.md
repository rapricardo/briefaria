# GEO: citação em buscas por IA

Busca clássica devolve uma lista ranqueada. ChatGPT, Perplexity e AI Overviews devolvem uma resposta e nomeiam poucas fontes dentro dela. O trabalho deste módulo é tornar a página a fonte correta mais fácil de citar e fazer o restante da web concordar que ela tem autoridade.

## Antes de começar

Leia o brand-context do cliente. Afirmação de entidade depende do que a marca é e do que ela pode afirmar; as Restrições e Provas travadas valem aqui como em qualquer copy.

Estabeleça, inferindo quando óbvio:
1. **As perguntas a conquistar**, escritas como uma pessoa digita no ChatGPT, em português. Se o cliente não souber, gere 15 candidatas a partir do produto e dos clusters de SEO existentes e peça corte.
2. **Se o cliente edita o site.** Define se a saída é diff de conteúdo ou brief para quem mantém o site. Sites de clientes ficam em repositórios próprios; aqui fica o conteúdo e o brief.

## As cinco alavancas

Audite e pontue cada uma de 0 a 100.

### 1. Extraibilidade (25%)

- Resposta direta nas 2-3 primeiras frases sob o heading que faz a pergunta
- Cada seção se sustenta lida isoladamente: sujeito explícito, sem "como dito acima"
- H2/H3 escritos como a pergunta da lista
- Números, datas, definições e comparações em tabela ou lista
- Blocos de resposta de ~100-170 palavras (heurística observada pela comunidade)
- Resposta fora de paywall ou renderização só por JavaScript

Teste rápido: copie uma seção sozinha e veja se ela responde à pergunta.

### 2. Especificidade e evidência (25%)

Modelos citam o que não conseguem gerar sozinhos: números com fonte e data, dados próprios, pesquisa original, entidades nomeadas, metodologia declarada. Página sem nenhum fato que um modelo não inventaria não é citada, mesmo bem ranqueada.

O estudo controlado de referência (Princeton GEO, KDD 2024, arxiv.org/abs/2311.09735) mediu ganhos de visibilidade com citações (~+41%), estatísticas (~+33%), fluência (~+29%) e fontes citadas (~+27%); keyword stuffing não teve efeito. Os números são direcionais; a ordem (evidência acima de palavra-chave) se manteve nas replicações.

Dado de mercado segue a regra do brand-context: fonte, data e recorte explicados, e nunca apresentado como resultado do cliente.

### 3. Clareza de entidade (20%)

- Uma descrição canônica usada em site, LinkedIn, diretórios e perfis
- Razão social, nome do produto e abreviações declarados juntos ao menos uma vez
- Dados estruturados: `Organization`, `Product`, `Article` com `author` e `datePublished`
- Página institucional escrita como verbete, sem manifesto
- Frase de categoria explícita: "{Marca} é {categoria} para {público} que {resultado}"

A descrição canônica sai da seção Produto do brand-context. Descrição inconsistente entre fontes é a falha mais comum e mais barata de corrigir.

### 4. Corroboração (20%)

Modelos pesam o que outras fontes dizem sobre a marca. Verifique presença nas listas que respondem às perguntas-alvo ("melhores X para Y"), em plataformas de avaliação (G2, Reclame Aqui quando houver consumidor final), menções independentes com a descrição canônica, páginas de comparação e comunidades onde a categoria é discutida.

Meça consultando: faça as perguntas-alvo aos motores e registre quem é citado. Esse conjunto é o concorrente real em GEO e costuma diferir do concorrente de SEO.

### 5. Acesso de máquina (10%)

- `robots.txt` sem bloquear crawlers que o cliente quer (lista em `geo-engines.md`). Bloquear ou liberar é decisão de negócio; apresente a escolha.
- `llms.txt` apenas quando houver documentação ou biblioteca grande de conteúdo
- HTML limpo, conteúdo principal sem renderização só no cliente, sem interstitial sobre o texto

## Sinais contra a citação

Verifique explicitamente; remover um costuma custar menos que adicionar alavanca:
- densidade de CTA que faz a página parecer etapa de funil
- popups ou banners sobre o conteúdo principal
- página rasa que repete o que outras cem dizem
- sem autor nomeado nem identidade da fonte
- afirmação sensível a tempo sem data
- superlativo sem evidência ("a principal plataforma de...")

## Fluxo

1. **Linha de base.** Cada pergunta-alvo, em cada motor disponível, **no mínimo três vezes**. Registre por consulta: marca mencionada, domínio citado (eventos diferentes), quem mais foi citado, o que a resposta afirmou.
2. **Auditoria** das cinco alavancas, com nota e total ponderado.
3. **Diagnóstico** da alavanca limitante; corrigir as outras não move nada antes dela.
4. **Reescrita.** Conteúdo revisado de fato: estrutura com resposta primeiro, headings, tabelas e JSON-LD prontos.
5. **Remedição** marcada: mesmas perguntas, mesmos motores, data definida (padrão: +30 dias).

## Relatório

Salve em `clientes/{slug}/entregas/geo-{dominio}-{AAAA-MM-DD}.md`:

```
# Auditoria GEO — {domínio}
{data} · Citabilidade: XX/100

## Linha de base: quem é citado hoje   (pergunta | marca citada? | quem foi citado | o que a resposta afirmou)
## Alavanca limitante
## Placar
## Reescritas          (antes/depois, página a página)
## Schema a adicionar  (JSON-LD completo)
## Remedir em {data}   (consultas exatas)
## O que não consegui determinar
```

## Honestidade

- Nenhum motor publica critério de citação; tudo aqui é inferido de comportamento observado. Declare isso.
- Citação varia entre sessões e regiões; uma observação não é medida.
- Não prometa citação. Prometa extraibilidade, densidade de evidência e consistência de entidade, que estão sob controle do cliente.
- Não estime tráfego vindo de IA; explique o que é e o que não é mensurável.
- Comportamento dos motores muda em semanas. Com busca disponível, verifique antes de recomendar.

## Encaminhamentos

- Qualidade do texto da página → [conteúdo](content.md)
- Problemas gerais de marketing → [auditoria](audit.md)
- SEO técnico (crawl, redirects, Core Web Vitals) fica fora desta skill; declare isso
