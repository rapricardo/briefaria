# Resultados e aprendizado

## Medição antes da campanha

**Diagnóstico (D4 da [implantação](implantacao.md)).** Liste o que é medido hoje, em qual ferramenta, com que confiança e com que histórico: analytics do site, eventos de conversão, pixels e contas de anúncio, CRM e origem do lead. Registre o que não é possível medir e por quê.

**Plano de medição (P3).** Métrica-norte ligada ao objetivo do mandato; um indicador por estágio do funil; eventos de conversão com nome e gatilho; padrão de UTM; onde cada número é lido; linha de base com período e fonte. Fica na seção Medição do plano de marketing.

**Tracking implementado (A1).** Teste cada evento em ambiente real, confira UTMs em um clique de teste e verifique se a origem chega ao CRM. Registre data e resultado do teste no plano. Campanha paga sem A1 produz resultado sem leitura confiável; declare isso no brief.

## Leitura de resultado

Recupere hipótese e objetivo no brief da campanha. Relacione os dados às peças e IDs externos registrados. Declare período, fonte, definição da métrica, denominador e janela de atribuição quando relevante. Sem vínculo confiável, explicite o limite de atribuição.

Diferencie experimento controlado, comparação observacional e relato qualitativo. Considere sazonalidade, composição de público, mudanças de tracking e seleção de anúncios sobreviventes. Ausência de conversões informadas não significa zero conversões.

Não imponha um número universal de conversões para declarar vencedor. Quando a decisão depender de inferência estatística, use baseline, efeito relevante, desenho e amostra real; calcule com ferramentas disponíveis. Sem essas informações, qualifique o sinal e a decisão reversível possível.

Para um experimento solicitado, defina antes da execução a hipótese, contraste, métrica principal e regra de decisão adequada ao tráfego e ao prazo. Testes de propostas completas medem o pacote; não atribua o resultado a uma palavra isolada.

Atualize no brief ou relatório existente: resultado observado, limite da evidência, aprendizado e próxima ação. Quando o teste fecha ou o padrão se repete entre peças, registre a linha em `clientes/{slug}/aprendizados.md` (data, aprendizado, evidência, força: sinal ou confirmado) e corrija ali o aprendizado que o resultado novo contrariar. Diferencie repetir, variar, interromper e observar mais. Decisões sobre campanhas ativas continuam sujeitas à autorização externa.

Uma correção confirmada atualiza o campo vigente no status ou brief, preservando IDs e metadata; registre o motivo no session-log. Não reabra bloqueios antigos com base em um registro anterior já corrigido. Se fontes recentes divergirem, esclareça a divergência relevante antes de agir.
