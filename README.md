# Briefaria

Skill para operar marketing e produção de conteúdo de várias marcas a partir de arquivos locais. Mantém contexto de marca, campanhas, peças, aprovações e resultados ligados por referência. Inclui os scripts que criam projetos, executam as etapas de mídia e publicam carrosséis no Instagram.

## Instalação

Use o **Codex** ou o **Claude Code** com acesso a arquivos e terminal, em macOS ou Linux com Python 3.11+. A skill completa está em `skills/briefaria/`.

A partir do checkout, execute para instalar o runtime e a skill em um novo workspace local.

```bash
git clone https://github.com/rapricardo/briefaria.git
cd briefaria
python3 skills/briefaria/scripts/init-workspace.py ../meu-marketing
mkdir -p ../meu-marketing/.agents/skills
cp -R skills/briefaria ../meu-marketing/.agents/skills/
cd ../meu-marketing
```

Para Claude Code, use `.claude/skills` no lugar de `.agents/skills` nos dois comandos de instalação. Abra uma nova sessão do agente em `meu-marketing`.

> Use a skill briefaria. Cadastre minha marca, preencha o contexto com os dados deste briefing e proponha a primeira campanha.

Para retomar uma peça, indique o cliente, o projeto e o resultado desejado.

> Retome o vídeo da campanha de lançamento. Use a gravação existente, prepare os cortes e exporte um MP4 vertical.

## O que está incluído

- **Estratégia** · implantação por cliente, pesquisa, posicionamento, oferta, auditoria de site e GEO.
- **Campanhas** · brief, fila de ideação, copy, calendário editorial, mídia paga e registro de resultados.
- **Produção** · carrossel, vídeo gravado e vídeo gerado. Transcrição local, cortes, storyboard, narração, imagens, clips, efeitos, composição e exportação.
- **Distribuição** · arquivos e legendas prontos para o canal e integração opcional com Instagram e Cloudflare R2.

Planejamento e organização de projetos usam Python padrão. Transcrição e edição podem rodar localmente. Renderização e serviços externos têm dependências por fase. Veja o [manual do workspace](skills/briefaria/assets/workspace/MANUAL.md) para instalar as ferramentas e configurar suas próprias credenciais.

## Teste local

Depois da instalação, na raiz do workspace:

```bash
python3 scripts/e2e/marketing_workflow.py --output /tmp/briefaria-e2e.json
```

O teste usa um cliente fictício e verifica cadastro, implantação, campanha, criação de peças, preservação do projeto ativo, estado e preflight. A execução funciona sem chaves de API. Com FFmpeg no PATH, teste também a edição de um vídeo sintético:

```bash
python3 scripts/e2e/edicao_workflow.py --output /tmp/briefaria-edicao-e2e.json
```

## Licença

[MIT](LICENSE). Os módulos de estratégia incluem adaptações de [Marketing OS](https://github.com/Yuzzyuk/marketing-os). HyperFrames, Remotion, whisper.cpp e as integrações são dependências externas, cada uma com seus próprios termos.
