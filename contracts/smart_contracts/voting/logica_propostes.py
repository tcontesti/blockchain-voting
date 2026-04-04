"""
Modul: logica_propostes.py
Descripcio: Logica de gestio de propostes d'eleccions.
            Permet crear propostes amb candidats i cens, i votar-les.
            Quan una proposta assoleix el llindar (50% del cens),
            es genera automaticament una eleccio.
Estat: IMPLEMENTAT
Depend: constants.py, verificador.py
Referencia: Decisio tecnica DT-03 (Box Storage per a propostes)
"""

# NOTA: Aquest modul conté la logica de propostes que s'integra
# dins la classe SistemaVotacio del router.py.
# Les funcions d'utilitat es defineixen aqui per a claredat,
# pero l'execucio real es fa via @abimethod al contract principal.
#
# En algopy/Puya, tot el contracte ha de ser una unica classe
# ARC4Contract. Els moduls auxiliars serveixen per organitzar
# la logica conceptualment.

# La logica de propostes esta integrada directament al router.py
# (metodes crear_proposta i votar_proposta) perque algopy requereix
# que tots els @abimethod estiguin dins la mateixa classe ARC4Contract.
#
# Flux de propostes:
#
# 1. Un membre del cens crida crear_proposta(nom, candidats, cens)
#    - Valida que el creador pertany al cens generic
#    - Valida que la proposta no existeix
#    - Registra candidats, inicialitza vots a 0
#    - Crea el cens especific de la proposta
#
# 2. Membres del cens de la proposta criden votar_proposta(nom)
#    - Valida cens, doble vot, proposta activa
#    - Incrementa comptador de vots
#    - Si vots >= llindar (50% cens), genera l'eleccio automaticament
