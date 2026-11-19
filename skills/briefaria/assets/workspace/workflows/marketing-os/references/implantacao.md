# Implantação do marketing do cliente

Ordem de trabalho para pôr o marketing de um cliente de pé, como uma agência faria: entender o mandato, diagnosticar, decidir, planejar, construir a base, rodar campanhas e aprender. O brand-context é uma etapa da fase de Estratégia; o plano de marketing, a fundação de ativos e o ciclo de campanha completam o conjunto.

O estado de cada cliente fica em `clientes/{slug}/implantacao.md`, uma tabela com as etapas abaixo, status e evidência. `python3 scripts/implantacao.py --client {slug}` mostra o progresso, as etapas prontas para começar e as inconsistências.

## Fluxo

```
F0 Mandato ─► F1 Diagnóstico ─► F2 Estratégia ─► F3 Plano ─► F4 Fundação ─► F5 Campanhas ─► F6 Operação
                    ▲                ▲                ▲                              │              │
                    │                └──── trimestral ┴──────────────────────────────┴── aprendizados.md
                    └──────────────────── reauditoria trimestral ──────────────────────────────────┘
```

Cada fase produz o insumo da seguinte. F5 e F6 formam um ciclo: resultado de campanha vira aprendizado, aprendizado ajusta o plano, e a revisão trimestral pode reabrir posicionamento e brand-context.

## Etapas

Coluna "Depende de": a etapa começa quando as dependências estão `feito` ou `n/a`. Módulos ficam em `references/`.

### F0 — Mandato

O que o cliente contratou, para quê, com que recursos e com que autonomia. Artefato único: `clientes/{slug}/mandato.md` (template em `templates/cliente/mandato.md`).

| ID | Etapa | Pronto quando | Depende de |
|---|---|---|---|
| M1 | Objetivo comercial e metas | Resultado de negócio que o marketing serve, meta com prazo ou declaração explícita de que ainda não há meta | — |
| M2 | Escopo, canais e orçamento | Canais autorizados, entregáveis, fora de escopo, verba de mídia e produção (ou [LACUNA]) | M1 |
| M3 | Aprovações e autonomia | Quem aprova o quê, prazo de aprovação, o que o agente faz sozinho, o que exige autorização explícita | M1 |
| M4 | Acessos e dados | Lista de sistemas (site, analytics, contas de anúncio, CRM, redes, histórico) com responsável e situação de acesso; credenciais fora do repositório | M2 |
| M5 | Cadência | Frequência de relatório e reunião, formato do relatório, canal de contato | M3 |

### F1 — Diagnóstico

Fotografia do ponto de partida antes de qualquer decisão. Etapas D1-D7 podem correr em paralelo; com subagentes, uma por subagente.

| ID | Etapa | Módulo | Artefato | Pronto quando | Depende de |
|---|---|---|---|---|---|
| D1 | Inventário de ativos e canais | auditoria | `entregas/inventario-{data}.md` | Site, perfis, conteúdos, campanhas ativas ou passadas, materiais de venda, com URL e situação | M4 |
| D2 | Auditoria de site e funil | [auditoria](audit.md) | `entregas/auditoria-{dominio}-{data}.md` | Nota com cobertura declarada, "Corrigir primeiro" com texto substituto | D1 |
| D3 | Linha de base GEO | [GEO](geo.md) | `entregas/geo-{dominio}-{data}.md` | Perguntas-alvo consultadas 3x por motor, quem é citado, data de remedição | D1 |
| D4 | Dados e medição atuais | [aprendizado](measurement.md) | `entregas/medicao-diagnostico-{data}.md` | O que é medido, onde, com que confiança; histórico de resultados disponível; lacunas de tracking | M4 |
| D5 | Mercado e categoria | [pesquisa](research.md) | dossiê em `estrategia/research/` | Tamanho e dinâmica com fonte e recorte; o que os dados não permitem concluir | M1 |
| D6 | Concorrência | [concorrência](competitive.md) | `entregas/concorrencia-{data}.md` + `competitors.json` | Leitura por concorrente, mapa, exposições, o que evitar | M1 |
| D7 | Voz do cliente | [hooks](hooks.md) (corpus) | `estrategia/research/corpus-{data}.md` | Frases literais de clientes e prospects sobre dor, alternativa e resultado, com fonte (avaliações, vendas, atendimento, entrevistas) | M4 |
| D8 | Síntese do diagnóstico | [estratégia](strategy.md) | `entregas/diagnostico-{data}.md` | O ponto central: onde está o problema (oferta, mensagem, distribuição, destino, medição), hipótese principal e o que a refutaria | D2, D4, D5, D6, D7 |

### F2 — Estratégia

Decisões que todas as peças vão herdar. Saem com status `vigente` depois de aprovadas.

| ID | Etapa | Módulo | Artefato | Pronto quando | Depende de |
|---|---|---|---|---|---|
| E1 | ICP e segmentos | [estratégia](strategy.md) | `icp.md` | Papéis de compra, critério de qualificação, recortes priorizados, descarte | D5, D7, D8 |
| E2 | Posicionamento, oferta e preço | [posicionamento](positioning.md) | `estrategia/posicionamento.md` | Declaração com cláusulas exclusivas marcadas, moldura escolhida e rejeitada, oferta nos quatro eixos, estrutura de preço | E1, D6 |
| E3 | Mensagem por público | [conteúdo](content.md) | `estrategia/mensagem.md` | Mensagem central, mensagem por decisor ou trilha, objeções com resposta, prova disponível para cada afirmação | E2 |
| E4 | Brand-context | SKILL.md (contrato) | `brand-context.md` | Oito seções preenchidas ou com [LACUNA], `validar_cliente.py` sem erro | E1, E2, E3 |

### F3 — Plano

Um documento: `estrategia/plano.md` (template em `templates/cliente/plano-marketing.md`), período no frontmatter, status `vigente`, citado no Mapa de leitura. Substitui documentos avulsos de funil, canais, medição e conteúdo. Plano novo substitui o anterior; o que se aprendeu vai para `aprendizados.md` e `decisoes.md`.

| ID | Etapa | Módulo | Pronto quando | Depende de |
|---|---|---|---|---|
| P1 | Funil e jornada | [estratégia](strategy.md) | Estágios, ação esperada e CTA por estágio, definição de lead qualificado, passagem para vendas com prazo de resposta | E4 |
| P2 | Mix de canais | [estratégia](strategy.md), [social](social.md), [email](email.md), [anúncios](paid-ads.md) | Função de cada canal no funil, prioridade, verba, o que fica de fora e por quê | P1, M2 |
| P3 | Plano de medição | [aprendizado](measurement.md) | Métrica-norte, indicador por estágio, eventos de conversão, padrão de UTM, onde se lê, linha de base | P1, D4 |
| P4 | Conteúdo | [conteúdo](content.md), [social](social.md), [GEO](geo.md) | Pilares ligados às mensagens, formatos, peça-mãe e derivados, cadência compatível com a capacidade de produção | E3, P2 |
| P5 | Roadmap de 90 dias e backlog | [estratégia](strategy.md) | Sequência de campanhas e entregas da fundação; backlog de experimentos com hipótese, custo e evidência; prioridade explicada | P1, P2, P3, P4 |

### F4 — Fundação

Ativos que as campanhas usam. Itens que dependem do repositório do site produzem brief e copy aqui; a implementação acontece lá.

| ID | Etapa | Módulo | Artefato | Pronto quando | Depende de |
|---|---|---|---|---|---|
| A1 | Tracking implementado | [aprendizado](measurement.md) | registro no plano, seção Medição | Eventos do P3 disparam em teste, UTMs padronizadas, origem chega ao CRM | P3 |
| A2 | Identidade visual operacional | `imagen`, `marketing-direcao-de-arte` | `branding.json`, templates de peça | Branding sem campos de template; peça-teste aprovada | E4 |
| A3 | Destino com a mensagem nova | [auditoria](audit.md) → [conteúdo](content.md) | `entregas/copy-{pagina}-{data}.md` | Copy aprovada e publicada nas páginas de destino do P1, sem claims bloqueados | E3, D2, P1 |
| A4 | Conteúdo-pilar e GEO on-page | [GEO](geo.md), [conteúdo](content.md) | páginas-pilar, JSON-LD, descrição canônica | Páginas do P4 publicadas; descrição canônica igual em site e perfis | E3, D3, P4 |
| A5 | Perfis e canais prontos | [social](social.md) | registro no plano | Perfis do P2 com descrição canônica, link de destino e responsável | E4, P2 |
| A6 | Material de vendas | [conteúdo](content.md), [email](email.md) | `estrategia/vendas.md` | Pitch, perguntas de diagnóstico, objeções, material por etapa, sequência de outbound | E3, P1 |
| A7 | Infraestrutura de email | [email](email.md) | registro no plano | SPF, DKIM e DMARC, base com consentimento, descadastro; ou `n/a` se email não está no P2 | P2 |

### F5 — Campanhas

Ciclo repetido por campanha; o estado de cada uma fica no brief ([operação](operations.md)). No checklist do cliente, F5 registra a primeira campanha que completar o ciclo e as campanhas em curso.

1. **Brief** (`brief.md`): objetivo, hipótese, público, oferta, canal e formato, métrica, regra de decisão, verba e prazo. Origem: item do roadmap P5.
2. **Ângulos e hooks** ([hooks](hooks.md)), a partir do corpus D7.
3. **Copy e peças** ([conteúdo](content.md), [social](social.md), [email](email.md)).
4. **Produção** pela escada de fidelidade ([hooks](hooks.md), [operação](operations.md)).
5. **Revisão de marca e compliance** (`workflows/marketing-revisao-brand`, personas `cliente-*`) contra Restrições e Provas.
6. **Publicação ou ativação** com autorização explícita; IDs externos registrados no brief.
7. **Leitura e decisão** ([aprendizado](measurement.md)): repetir, variar, interromper ou observar mais; padrão confirmado sobe para `aprendizados.md`.

| ID | Etapa | Pronto quando | Depende de |
|---|---|---|---|
| C1 | Primeira campanha com ciclo completo | Os sete passos acima registrados no brief, com resultado lido e decisão tomada | P5, A1, A3 |

### F6 — Operação contínua

| ID | Rotina | O que faz | Depende de |
|---|---|---|---|
| O1 | Semanal | Lê campanhas ativas, atualiza briefs, monitora concorrência quando o mandato pede | C1 |
| O2 | Mensal | Relatório no formato do M5, atualiza `aprendizados.md`, reprioriza o backlog do P5 | C1, M5 |
| O3 | Trimestral | Remede GEO (D3), revisa auditoria leve (D2), revisa posicionamento e brand-context à luz dos aprendizados, escreve o plano do trimestre seguinte | O2 |

Rotinas registram a data da última execução na coluna de evidência. A rotina mensal confere se a pasta `estrategia/` tem só documentos vigentes e se `decisoes.md` registra os resultados das decisões do mês.

## Status e evidência

Status permitidos: `pendente`, `em andamento`, `parcial`, `feito`, `n/a`, `bloqueado`.

- `feito` exige evidência: caminho de arquivo (relativo à pasta do cliente, entre crases) que exista e cumpra o "pronto quando". Documento de estratégia precisa estar `vigente`.
- `parcial` indica artefato existente que não cumpre todo o critério; a nota diz o que falta.
- `n/a` exige motivo (exemplo: email fora do escopo do mandato).
- `bloqueado` exige o motivo e de quem depende o desbloqueio.

## Cliente em andamento

Cliente que já tem material começa pelo levantamento: preencha `implantacao.md` com o status de cada etapa a partir do que existe, aponte a evidência e marque `parcial` quando o artefato for anterior a uma decisão vigente ou não cumprir o critério. Em seguida, siga as etapas prontas para começar que o script indicar, na ordem das fases. Material produzido antes de F2 é revisado contra o brand-context antes de ser publicado.

## Pedidos pontuais

Um pedido de peça, análise ou correção segue sem exigir a implantação completa. Consulte o checklist do cliente e declare na entrega o limite causado por etapas pendentes, por exemplo:
- copy sem E4: saída sem contexto de marca validado;
- campanha paga sem A1: resultado não mensurável;
- campanha apontando para destino sem A3: conversão limitada pela página;
- vídeo de produção completa para ângulo não testado: custo acima da evidência.

Publicação, envio e mudança de campanha continuam dependendo de autorização explícita, como em toda a skill.

## Atualização

Ao concluir uma etapa, atualize a linha no `implantacao.md` (status, evidência, data) no mesmo trabalho que gerou o artefato. Quando uma etapa de F2 muda, as etapas que dependem dela voltam a `parcial` até revisão; o script aponta quais são.
