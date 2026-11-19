# Operação, campanha e contratos

Execute os comandos a partir da raiz do workspace.

## Criar e retomar

Use `scripts/setup-project.py` pela skill `setup`. `marketing` cria `formato: multi` e pipeline com objetos de fase; produção audiovisual usa strings. Leia ambos sem reescrever o schema:

```json
{"pipeline": {"roteiro": "pending"}}
```
```json
{"pipeline": {"conteudo": {"status": "in_progress", "skills": ["marketing-os"], "entregaveis": ["conteudo/"]}}}
```

Atualize somente o estado e os campos afetados. Preserve IDs de conta/campanha/anúncio, payloads, aprovações, outputs e metadata. `voiceover` é o nome da fase nos novos vídeos; `audio/` é a pasta. Se um projeto legado usa `audio`, preserve a chave e seus consumidores.

Antes de executar uma fase de produção, rode `python3 scripts/preflight.py --project <projeto> --fase <fase>`. Em marketing, o preflight verifica o estado; a adequação dos insumos depende do pedido. `pending` indica trabalho por fazer, não autorização de publicação. `done` só descreve a fase concluída; uma peça pronta não prova que foi publicada.

## Campanha, peças e resultados

Reutilize `brief.md` ou `campaign-brief.md`, escolhendo o que já contém a direção vigente. Não duplique os dois. Na campanha nova, `brief.md` é suficiente.

Quando houver múltiplas peças ou acompanhamento de resultado, mantenha no brief uma tabela com: ID estável da peça, hipótese, canal/formato, caminho do arquivo/projeto, ID externo quando existir, estado de aprovação/publicação e fonte do resultado. Reutilize IDs existentes. Referências de arquivos podem ser relativas ao brief; identifique a base.

Uma peça visual com pipeline próprio é criada assim:

```bash
python3 scripts/setup-project.py new-project --client slug --type carrossel --name campanha-peca --formato 1:1 --no-activate
```

`--no-activate` preserva `_ativo` da campanha. Registre no brief da peça o caminho da campanha e seu ID na tabela; acrescente a referência da peça ao brief da campanha. Assets ficam na pasta de produção, ligados por referência. Relatórios e entregas avulsas ficam em `clientes/{slug}/entregas/{modulo}-{assunto}-{AAAA-MM-DD}.md`. `multi` não é proporção para gerar mídia: defina 16:9, 9:16 ou 1:1 no projeto da peça.

## Governança existente

Se o projeto usa [fila de ideação](../../../sistema/README.md), acompanhe a ficha existente.

Integrações e cadências só executam quando disponíveis e autorizadas. Não crie automações nem envie mensagens como consequência implícita de planejar uma campanha.

Ao concluir fase, use `scripts/session_log.py --project <projeto> --fase <fase> --action "ação" --details "resultado"`. Não crie registro de fase para uma simples pergunta. Ao corrigir um bloqueio comprovadamente resolvido, atualize seu campo no estado vigente e registre a correção no log.
