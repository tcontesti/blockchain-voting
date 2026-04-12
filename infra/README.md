# Infraestructura — Desplegament de nodes Algorand

Configuracio, orquestracio i scripts per desplegar la xarxa Algorand
on s'executa el Smart Contract de votacio.

Responsable: Dylan Luigi Canning (@dylanluigi)

---

## Estructura

```
infra/
  algorand/
    docker-compose.yml       — Orquestracio de la xarxa Algorand (localnet)
    Dockerfile               — Imatge personalitzada del node (si cal)
    config/                  — Fitxers de configuracio dels nodes
      genesis.json           — Configuracio genesis de la xarxa
      node-config.json       — Parametres del node Algorand
      kmd-config.json        — Configuracio del Key Management Daemon
    scripts/                 — Scripts d'operacions
      start-network.sh       — Arrancar la xarxa completa
      stop-network.sh        — Aturar la xarxa
      reset-network.sh       — Reiniciar la xarxa (esborrar dades)
      create-accounts.sh     — Crear comptes de prova
      fund-accounts.sh       — Finançar comptes amb Algos de prova
  README.md                  — Aquest fitxer
```

## Prerequisits

- Docker >= 24.0
- Docker Compose >= 2.20
- AlgoKit >= 2.0 (opcional, per a comandes simplificades)

## Ús rapid

```bash
# Arrancar la xarxa Algorand local
cd infra/algorand
docker-compose up -d

# Verificar que els nodes estan funcionant
docker-compose ps

# Crear comptes de prova
./scripts/create-accounts.sh

# Aturar la xarxa
docker-compose down
```

## Connexio amb el Smart Contract

Un cop la xarxa esta en marxa, configurar les variables al fitxer `.env`
de l'arrel del projecte:

```
ALGOD_SERVER=http://localhost
ALGOD_PORT=4001
ALGOD_TOKEN=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
```

Despres desplegar el SC:

```bash
cd contracts/
algokit project run build
algokit project deploy localnet
```

## Notes

- La xarxa localnet es exclusivament per a desenvolupament i testing
- Les dades es perden quan es fa `docker-compose down -v`
- Per a persistencia entre reinicis, no esborrar els volums Docker
