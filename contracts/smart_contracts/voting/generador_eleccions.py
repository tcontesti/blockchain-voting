"""
Modul: generador_eleccions.py
Descripcio: Logica de generacio automatica d'eleccions a partir de propostes.
            Quan una proposta assoleix el llindar de vots (50% del cens),
            es genera una eleccio amb els mateixos candidats i cens.
Estat: IMPLEMENTAT
Depend: constants.py
Referencia: Decisio tecnica DT-04 (itxn.submit quan llindar assolit)

NOTA: En la implementacio actual, la generacio d'eleccions es fa dins
el mateix Smart Contract (no via inner transaction / itxn.submit).
Aixo es perque els candidats i el cens ja estan al Box Storage del SC.
Una inner transaction seria necessaria si l'eleccio es desplegues com
un SC independent, cosa que es pot considerar en futures iteracions
per a escalabilitat.
"""

# La logica de generacio esta integrada al router.py
# (metode _generar_eleccio, cridat automaticament des de votar_proposta)
#
# Flux:
#
# 1. votar_proposta() incrementa el comptador de vots
# 2. votar_proposta() crida _generar_eleccio(nom_proposta)
# 3. _generar_eleccio() calcula el llindar: total_cens // 2
# 4. Si vots >= llindar:
#    a. Copia els candidats de la proposta a l'eleccio
#    b. Inicialitza els comptadors de vots a 0 per a cada candidat
#    c. El cens de l'eleccio es el mateix que el de la proposta
#       (ja registrat al BoxMap censo_direcciones amb la mateixa clau)
#
# Consideracions:
# - El llindar es configurable via THRESHOLD_DIVISOR a constants.py
# - La generacio es atomica: si falla, el vot a la proposta tambe falla
# - Un cop generada l'eleccio, la proposta es considera tancada
#   (validar_proposta_activa impedeix nous vots)
