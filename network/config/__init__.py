"""
Paquet: config
Descripcio: Configuracio de la xarxa de nodes universitaris. Defineix les
            tres universitats participants (UIB, UPC, UAB), el llindar de
            consens K=2, i proporciona funcions per carregar les credencials
            des de variables d'entorn.

            Fitxers:
              - universities.json: Definicio estatica de les universitats
                (noms, identificadors, referencies a variables d'entorn)
              - network_config.py: Carregador Python que llegeix el JSON
                i resol els secrets (mnemonics Algorand) des de l'entorn

Referencia: BLOCKCHAIN.pdf §3.2.2 (Nodes institucionals), §10.1 (Configuracio)
"""
