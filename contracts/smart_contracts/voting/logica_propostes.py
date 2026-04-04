"""
Modul: logica_propostes.py
Descripcio: Documentacio de la logica de propostes d'eleccions.
            El codi esta implementat a contract.py (metodes crear_propuesta,
            cargar_censo_propuesta i votar_propuesta).
Estat: IMPLEMENTAT (integrat a contract.py)
Depend: constants.py, verificador.py
Referencia: Decisio tecnica DT-03 (Box Storage per a propostes)
Autor: Marc Link (@linkcla)

Flux de propostes (versio actual):

  1. Un membre del cens generic crida crear_propuesta(nom, candidats, total_cens)
     - Valida que el creador pertany al cens generic
     - Valida que la proposta no existeix
     - Registra candidats, inicialitza vots a 0
     - Declara el total de cens esperat (no el carrega encara)
     - Registra qui ha creat la proposta (autoritzacio)

  2. El creador crida cargar_censo_propuesta(nom, lot_adreces) repetidament
     - Maxim 4 adreces per transaccio (restriccio AVM)
     - Nomes el creador pot carregar el cens de la seva proposta
     - Controla que no es superi el total declarat
     - Un cop carregat tot el cens, la proposta queda activa per votar

  3. Membres del cens de la proposta criden votar_propuesta(nom)
     - Valida cens, doble vot, proposta activa (cens complet + no convertida)
     - Incrementa comptador de vots
     - Si vots >= llindar (ceil(50% cens)), genera l'eleccio automaticament

Millores respecte la versio anterior:
  - El cens es carrega per lots (evita limits de gas per tx grans)
  - Autoritzacio del creador (nomes ell carrega el cens)
  - Control del total de cens declarat vs carregat
  - La proposta no es pot votar fins que el cens estigui complet
"""
