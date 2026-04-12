#!/usr/bin/env bash
# Script: create-accounts.sh
# Descripcio: Crea comptes Algorand de prova a la localnet.
#             Genera 5 comptes i els finança amb Algos de prova.
# Responsable: Dylan Luigi Canning (@dylanluigi)
#
# Us:
#   cd infra/algorand
#   ./scripts/create-accounts.sh
#
# Prerequisit: la xarxa ha d'estar arrancada (start-network.sh)

set -euo pipefail

ALGOD_URL="http://localhost:4001"
KMD_URL="http://localhost:4002"
TOKEN="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
NUM_ACCOUNTS=5

echo "=== Creant $NUM_ACCOUNTS comptes de prova ==="
echo ""

# Verificar que el node esta disponible
if ! curl -s -o /dev/null -w "%{http_code}" "$ALGOD_URL/v2/status" -H "X-Algo-API-Token: $TOKEN" | grep -q "200"; then
    echo "ERROR: El node Algorand no esta disponible a $ALGOD_URL"
    echo "Executa primer: ./scripts/start-network.sh"
    exit 1
fi

echo "Node Algorand operatiu."
echo ""

# Nota: en un entorn localnet amb AlgoKit, es poden crear comptes amb:
#   algokit goal account new
#   algokit goal clerk send -a <amount> -f <genesis_account> -t <new_account>
#
# Dylan: substitueix aquesta seccio amb la teva implementacio
# que pot usar goal directament dins el contenidor Docker:
#   docker exec bv-algod goal account new
#   docker exec bv-algod goal clerk send ...

for i in $(seq 1 $NUM_ACCOUNTS); do
    echo "Creant compte $i de $NUM_ACCOUNTS..."
    # TODO: Dylan — implementar amb goal o algokit
    # docker exec bv-algod goal account new
done

echo ""
echo "=== Comptes creats ==="
echo "Usa 'docker exec bv-algod goal account list' per veure els comptes."
