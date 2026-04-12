#!/usr/bin/env bash
# Script: stop-network.sh
# Descripcio: Atura la xarxa Algorand localnet.
# Responsable: Dylan Luigi Canning (@dylanluigi)
#
# Us:
#   cd infra/algorand
#   ./scripts/stop-network.sh
#
# Per esborrar totes les dades (reset complet):
#   ./scripts/stop-network.sh --clean

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_DIR="$(dirname "$SCRIPT_DIR")"

cd "$COMPOSE_DIR"

if [[ "${1:-}" == "--clean" ]]; then
    echo "Aturant la xarxa i esborrant totes les dades..."
    docker-compose down -v
    echo "Xarxa aturada. Volums esborrats."
else
    echo "Aturant la xarxa (les dades es conserven)..."
    docker-compose down
    echo "Xarxa aturada. Per esborrar dades: $0 --clean"
fi
