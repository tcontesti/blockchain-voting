#!/usr/bin/env bash
# Script: start-network.sh
# Descripcio: Arranca la xarxa Algorand localnet amb Docker Compose.
# Responsable: Dylan Luigi Canning (@dylanluigi)
#
# Us:
#   cd infra/algorand
#   ./scripts/start-network.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_DIR="$(dirname "$SCRIPT_DIR")"

echo "=== Blockchain Voting — Algorand Localnet ==="
echo "Arrancant la xarxa..."

cd "$COMPOSE_DIR"
docker-compose up -d

echo ""
echo "Esperant que els nodes estiguin llestos..."
sleep 5

# Verificar estat
docker-compose ps

echo ""
echo "=== Xarxa arrancada correctament ==="
echo "  algod API:    http://localhost:4001"
echo "  KMD API:      http://localhost:4002"
echo "  Indexer API:  http://localhost:8980"
echo ""
echo "Token per a connexio:"
echo "  aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
echo ""
echo "Per aturar: docker-compose down"
echo "Per logs:   docker-compose logs -f"
