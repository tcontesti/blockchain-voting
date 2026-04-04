"""
Modul: logica_votacio.py
Descripcio: Logica de votacio per a eleccions actives.
            Implementa votacio per pluralitat simple (un candidat per votant).
            El metode Schulze (preferencies ordenades amb matriu de parells)
            esta dissenyat pero pendent d'implementacio completa.
Estat: PARCIAL
  - Votacio per pluralitat: IMPLEMENTAT
  - Votacio Schulze (preferencies): PLACEHOLDER (TODO Sprint 4)
  - Consulta de resultats: IMPLEMENTAT
Depend: constants.py, verificador.py
Referencia: Decisio tecnica DT-04 (Operacions atomiques)

TODO: Implementar votacio Schulze completa.
  El metode Schulze requereix:
  1. Cada votant envia un ranking ordenat de candidats (no un sol candidat)
  2. Es manté una matriu NxN de preferencies parelles al Box Storage
  3. Per a cada parell (A,B), es compta quants votants prefereixen A sobre B
  4. L'algoritme de camins mes forts determina el guanyador
  Limitacio AVM: la matriu NxN amb N candidats requereix N*(N-1)/2 escriptures
  per vot, cosa que pot excedir el budget d'opcodes per transaccio si N > 5.
  Solucio proposada: limitar a 5-7 candidats per eleccio o usar atomic groups.
"""

# La logica de votacio esta integrada al router.py
# (metodes votar_eleccio i consultar_resultats)
#
# Flux de votacio actual (pluralitat simple):
#
# 1. Votant crida votar_eleccio(nom_eleccio, candidat)
#    - Valida existencia de l'eleccio
#    - Valida que el candidat pertany a l'eleccio
#    - Valida cens i doble vot
#    - Registra vot i incrementa comptador del candidat (atomic)
#
# 2. Qualsevol pot cridar consultar_resultats(nom_eleccio, candidat) [readonly]
#    - Retorna el nombre de vots del candidat
#
# Flux Schulze (pendent):
#
# 1. Votant crida votar_schulze(nom_eleccio, ranking: DynamicArray[String])
#    - ranking[0] = candidat preferit, ranking[N-1] = menys preferit
#    - Per a cada parell (i,j) on i < j en el ranking:
#      matriu_schulze[(eleccio, ranking[i], ranking[j])] += 1
#    - Complexitat per vot: O(N^2) escriptures al Box Storage
#
# 2. Consulta: calcular_guanyador_schulze(nom_eleccio) [readonly]
#    - Llegeix la matriu de preferencies
#    - Aplica l'algoritme de camins mes forts (Floyd-Warshall modificat)
#    - Retorna el guanyador Condorcet
