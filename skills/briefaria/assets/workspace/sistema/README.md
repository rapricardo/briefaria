# Sistema de decisão — operação de marketing

Método de trabalho da Máquina de Marketing para tudo que precede a produção visual:
posicionamento, arquitetura de site, teses, texto estrutural, briefs de campanha.

Dois princípios sustentam o resto.

**Um: função dominante.** Nenhum trabalho tenta maximizar tudo. Escolhe-se uma função
dominante, aceitam-se perdas deliberadas, e cada peça cumpre uma missão declarada.

**Dois: quem produz não critica.** O mesmo modelo produzindo e revisando devolve o
próprio viés com outra roupa. Produção e crítica rodam em agentes separados, com
modelos diferentes, sem contexto compartilhado e contra rubrica escrita antes do
artefato existir.

---

## 1. Dois armazéns

| | Onde | O que é | Move? |
|---|---|---|---|
| **Conhecimento** | `clientes/{slug}/{projeto}/` | Os documentos. Duram. | Nunca |
| **Fila** | `sistema/fila/` | Fichas de 20 linhas que apontam para documentos. | Sempre |

Documento não viaja entre pastas. O que viaja é a ficha; o estado do trabalho mora
no campo `estagio` dela. Histórico é do git.

Uma fila só para a agência inteira, fichas marcadas por cliente. Pasta vazia é o
estado saudável — é assim que se lê o sistema de relance. Se `2-criticar/` acumula
fichas por dois dias, o crítico parou.

```
sistema/
  fila/
    1-produzir/      ficha esperando produção
    2-criticar/      artefato pronto, esperando crítica
    3-revisar/       crítica escrita, volta para o produtor
    4-humano/        SUA caixa de entrada — o único lugar que você abre
    _ledger.md       append-only: quando, o quê, quem, veredito
  rubricas/          critérios de avaliação, compartilhados, versionados
  papeis/            instruções de produtor e crítico
  templates/         ficha, fichas de decisão, esqueleto de projeto
  agendamentos/      os prompts das tarefas agendadas
```

---

## 2. A estrutura de documentos

Todo projeto de ideação nasce com esta árvore (`sistema/templates/projeto/`):

```
clientes/{slug}/{projeto}/
  00-briefing/    missão, restrições, não-negociáveis, o que não pode ser dito
  01-contexto/    economia da oferta, ICP, provas disponíveis e provas vetadas
  02-decisoes/    função dominante · inventário · jornadas · mapa de páginas
  03-teses/       5W2H por oferta · tese por página · mapa de teses
  04-texto/       WHY, FAQ, CTA por página
  05-critica/     uma crítica por rodada, datada, preservada
  06-aprovado/    congelado depois do gate — libera a fase visual
  07-producao/    briefs de imagem, vídeo, site — só referenciam 06
```

Numerada porque a sequência precisa ser legível na listagem da pasta.

**Nada existe em `07` antes de `06` estar fechado.** É essa regra, sozinha, que garante
esforço de ideação antes de qualquer pixel. Sem ela o sistema é enfeite, porque
alguém sempre vai querer ver layout antes da tese estar aprovada.

`05` preservado importa mais do que parece: é como se descobre, em três meses, se a
crítica está ficando complacente ou se a rubrica precisa apertar.

---

## 3. As cinco regras

1. **Só markdown** nas pastas do sistema e da ideação. Imagem, Figma, PDF e planilha
   entram por referência — caminho ou URL. O crítico precisa ler o estado inteiro como
   texto, e binário mata diff.
2. **Documento nunca muda de pasta.** Estado em nome de arquivo quebra todo link que
   aponta para ele.
3. **Um documento, uma decisão.** Documento que responde três perguntas não passa em
   gate nenhum, porque se aprova uma parte e reprova outra.
4. **Rubrica fora do cliente.** Rubrica dentro do projeto vira rubrica negociável, e
   rubrica negociável é o viés voltando pela porta dos fundos.
5. **Ficha morta é apagada.** Missão fechada, ficha sai da fila e vira uma linha no
   ledger. A fila não é arquivo.

---

## 4. Os três gates humanos

Fora destes três, o loop produtor↔crítico roda sozinho.

| Gate | Documento | Por que é seu |
|---|---|---|
| **G1 — Função dominante** | `02-decisoes/funcao-dominante.md` | Define o que será sacrificado. Irreversível na prática. |
| **G2 — Mapa de teses** | `03-teses/mapa-de-teses.md` | Dez minutos aqui evitam reescrever o site inteiro. |
| **G3 — Liberação visual** | `06-aprovado/` | Destrava orçamento de produção. |

O agente que chega num gate move a ficha para `fila/4-humano/` e para. Não existe
gate aprovado por agente.

---

## 5. Os papéis

**Produtor**. Lê a ficha, o briefing e o contexto. Escreve o artefato no lugar
declarado e move a ficha. Entrega **só o artefato** — sem notas de raciocínio, sem
autoavaliação, sem "escolhi X porque". Defesa junto do trabalho transforma o crítico
em revisor de defesa.

**Crítico** (modelo diferente, e papel diferente). Recebe ficha, artefato e rubrica.
Nunca recebe o que o produtor pensou. A instrução não é "avalie a qualidade" — é uma
persona com objetivo próprio, tipicamente o próprio visitante do ICP com pressa e
sem interesse em quem escreveu. Mudar a função-objetivo quebra mais viés do que
trocar o peso do modelo.

**Saída do crítico é estruturada**, nunca prosa: veredito, nota por critério, defeitos
com localização exata e a regra violada. Prosa faz o produtor negociar; defeito
localizado ele conserta ou contesta.

**O crítico não reescreve.** Se escrever a versão corrigida, virou produtor e o segundo
ponto de vista acabou.

---

## 6. As regras de loop

- **Máximo 2 rodadas.** Na terceira a ficha vai para `4-humano/` com o resumo do
  desacordo. Desacordo persistente é sintoma de briefing ruim, e briefing é humano.
- **Veredito decide o destino**: `aprova` → próximo estágio ou gate; `revisa` → volta
  para `3-revisar/` com rodada+1; `refaz` → volta para `1-produzir/`, rodada zerada,
  com o defeito estrutural nomeado.
- **Toda transição escreve uma linha no ledger.** É como se descobre qual etapa
  emperrou sem abrir cinco pastas.

---

## 7. Onde nasce o viés

Em ordem de retorno, e a ordem importa porque a terceira é a cara e a menos eficaz:

1. **Rubrica compartilhada.** A maior. Rubrica que pergunta "um concorrente colaria o
   nome dele aqui?" é teste de empresa, e qualquer modelo pontuando por ela produz
   copy de mecanismo. Trocar o modelo sem trocar a rubrica não muda nada.
2. **Contexto compartilhado.** Crítico que vê o raciocínio do produtor ancora nele.
   Sessão nova a cada disparo resolve de graça.
3. **Pesos compartilhados.** Real, e a menor das três.

---

## 8. Pipeline

1. Escolher a função dominante · 2. Ficha estratégica da função · 3. Inventário de
ofertas, públicos e restrições · 4. Jornadas · 5. Mapa de páginas · **G1** ·
6. 5W2H por oferta · 7. Tese por página · 8. Mapa de teses · **G2** · 9. WHY, FAQ e
CTA · 10. Revisão 1 · **G3** · 11. Direção criativa e visual.

Primeiro se decide o que precisa ser comunicado e por que importa para o visitante.
Depois se decide como aquilo parece, move, soa e impressiona.
