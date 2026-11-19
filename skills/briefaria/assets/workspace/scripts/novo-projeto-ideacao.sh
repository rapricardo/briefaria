#!/usr/bin/env bash
# Instancia a árvore de ideação de um projeto.
# uso: scripts/novo-projeto-ideacao.sh <slug-cliente> <slug-projeto>
set -euo pipefail
RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CLIENTE="${1:?slug do cliente}"
PROJETO="${2:?slug do projeto}"
DESTINO="$RAIZ/clientes/$CLIENTE/$PROJETO"

[ -d "$RAIZ/clientes/$CLIENTE" ] || { echo "cliente não existe: $CLIENTE"; exit 1; }
[ -e "$DESTINO" ] && { echo "já existe: $DESTINO"; exit 1; }

cp -R "$RAIZ/sistema/templates/projeto" "$DESTINO"
echo "criado: clientes/$CLIENTE/$PROJETO"
echo "próximo passo: preencher 00-briefing/ e 01-contexto/, depois abrir a ficha de G1."
