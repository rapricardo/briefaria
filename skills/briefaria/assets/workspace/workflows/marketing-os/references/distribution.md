# Distribuição e publicação

Prepare em `publish/` as imagens finais, legenda e demais arquivos da peça. Vincule-os ao brief da campanha. Use o checklist do canal e registre o ID público após confirmação.

## Instagram via API

Configure uma conta profissional e as permissões de publicação no app Meta. Consulte a [documentação da API](https://developers.facebook.com/docs/instagram-platform/). Preencha uma cópia de `.env.meta-instagram.example`, com a versão da API suportada pelo seu app e `META_API_MODE` igual a `facebook_login` ou `instagram_login`. Para R2, preencha `.env.cloudflare-r2.example` com seu bucket e sua base HTTPS pública. Passe `--env-file` com um arquivo dedicado quando operar contas diferentes.

A partir da raiz do workspace, substitua `PECA` pelo caminho da peça. Prepare as imagens no formato aceito pela Meta, por exemplo JPEG. Antes de fazer upload ou publicar, confirme a autorização para as imagens, a conta e a legenda. O upload abaixo torna as imagens acessíveis por URL pública.

```bash
python3 scripts/meta_instagram.py verify --env-file .env.meta-instagram
uv run scripts/r2_assets.py --env-file .env.cloudflare-r2 verify
uv run scripts/r2_assets.py --env-file .env.cloudflare-r2 upload PECA/publish/01.jpg PECA/publish/02.jpg \
  --prefix sua-marca/nome-da-peca --manifest PECA/publish/meta-assets.json
python3 scripts/publish_instagram_carousel.py --env-file .env.meta-instagram \
  --manifest PECA/publish/meta-assets.json --caption-file PECA/publish/legenda.txt \
  --state PECA/publish/meta-state.json --result PECA/publish/meta-result.json
```

Com outra hospedagem, escreva `meta-assets.json` com `{"assets":[{"file":"01.jpg","public_url":"https://..."},{"file":"02.jpg","public_url":"https://..."}]}`.

Em retomadas, reutilize o mesmo `--state` com as mesmas imagens e legenda. Se a Meta aceitou a publicação e a resposta se perdeu, confira a conta e o estado antes de repetir. Guarde o resultado e o ID no brief da campanha. O comando `python3 scripts/meta_instagram.py media --media-id <id>` consulta a publicação.
