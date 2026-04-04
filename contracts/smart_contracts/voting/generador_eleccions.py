"""
Modul: generador_eleccions.py
Descripcio: Documentacio de la generacio automatica d'eleccions.
            El codi esta implementat a contract.py (metode _generar_eleccion).
Estat: IMPLEMENTAT (integrat a contract.py)
Depend: constants.py
Referencia: Decisio tecnica DT-04 (generacio automatica amb llindar)
Autor: Marc Link (@linkcla)

Flux de generacio:

  1. votar_propuesta() incrementa el comptador de vots
  2. votar_propuesta() crida _generar_eleccion(nom_proposta)
  3. _generar_eleccion() calcula el llindar:
     threshold = (total_cens // 2) + (total_cens % 2)
     Arrodoniment cap amunt: amb cens=5, llindar=3 (no 2)
  4. Si vots >= llindar:
     a. Copia els candidats de la proposta a l'eleccio
     b. Inicialitza un DynamicArray[UInt64] amb zeros (un per candidat)
     c. El cens de l'eleccio es el mateix que el de la proposta
        (ja registrat al BoxMap censo_direcciones amb la mateixa clau)

Consideracions:
  - La generacio es atomica: si falla, el vot a la proposta tambe falla
  - Un cop generada l'eleccio, la proposta es considera tancada
    (validar_propuesta_activa impedeix nous vots)
  - El cens ha d'estar completament carregat abans de poder votar
    la proposta (propuestas_censo_cargado == censo_totales)
"""
