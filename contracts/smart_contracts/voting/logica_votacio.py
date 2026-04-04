"""
Modul: logica_votacio.py
Descripcio: Documentacio de la logica de votacio per a eleccions actives.
            Implementa votacio per pluralitat simple (un candidat per votant).
            El metode Schulze (preferencies ordenades amb matriu de parells)
            esta dissenyat pero pendent d'implementacio completa.
Estat: PARCIAL
  - Votacio per pluralitat: IMPLEMENTAT (a contract.py)
  - Votacio Schulze (preferencies): PENDENT (issue #29)
Depend: constants.py, verificador.py
Referencia: Decisio tecnica DT-04 (Operacions atomiques)
Autor: Marc Link (@linkcla)

Flux de votacio actual (pluralitat simple):

  1. Votant crida votar_eleccion(nom_eleccio, candidat)
     - Valida cens del votant
     - Valida existencia de l'eleccio
     - Cerca l'index del candidat dins el DynamicArray
     - Valida doble vot
     - Registra vot i incrementa el comptador a l'index del candidat

  Emmagatzematge de vots (versio actual):
     elecciones_votos: BoxMap[String, DynamicArray[UInt64]]
     - Clau: nom de l'eleccio
     - Valor: array de comptadors, un per candidat (mateixa posicio que a elecciones_candidatos)
     - Exemple: candidats=["A","B","C"], vots=[5,3,7] -> C te 7 vots

Flux Schulze (pendent, issue #29):

  1. Votant crida votar_schulze(nom_eleccio, ranking: DynamicArray[String])
     - ranking[0] = candidat preferit, ranking[N-1] = menys preferit
     - Per a cada parell (i,j) on i < j en el ranking:
       matriu_schulze[(eleccio, ranking[i], ranking[j])] += 1
     - Complexitat per vot: O(N^2) escriptures al Box Storage

  2. Consulta: calcular_guanyador_schulze(nom_eleccio)
     - Llegeix la matriu de preferencies
     - Aplica l'algoritme de camins mes forts (Floyd-Warshall modificat)
     - Retorna el guanyador Condorcet
"""
