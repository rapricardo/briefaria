## Quando usar DaVinci Resolve em vez de Remotion

Remotion e ideal para composicao programatica e reproducivel. Usar DaVinci quando:

- **Multi-camera:** edicao com multiplos angulos sincronizados
- **Color grading avancado:** curvas, LUTs, matching entre takes
- **Efeitos visuais complexos:** tracking, compositing, particulas
- **Audio mix profissional:** equalizacao, compressao, espacializacao
- **Edicao interativa:** o editor precisa ajustar frame-a-frame manualmente
- **Formatos especificos:** entrega em ProRes, DNxHR, ou outros codecs profissionais

Regra geral: se o video pode ser descrito como "sequencia de assets com timing definido", Remotion resolve. Se precisa de decisoes artisticas frame-a-frame, usar DaVinci.


Para FCPXML use `scripts/storyboard_to_fcpxml.py --help`. Em sandbox, inclua `--base-path /caminho/do/workspace` para remapear paths. Inclua voiceover quando houver narração separada; diálogo integrado usa `--has-clip-audio --skip-sfx`.
