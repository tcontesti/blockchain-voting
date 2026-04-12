"""
Modul: models.py
Descripcio: Models de dades que representen l'estat d'una eleccio a la
            blockchain Algorand. Aquestes estructures son el format intermedi
            entre la lectura del Box Storage (algorand_reader.py) i el calcul
            del hash deterministic (hasher.py).

            En el flux del sistema de votacio, cada node universitari:
              1. Llegeix les boxes d'Algorand -> obte un ElectionState
              2. Passa l'ElectionState al hasher -> obte el hash SHA-256
              3. (Futur) Envia el hash a un contracte Ethereum per a consens K-de-N

Referencia: BLOCKCHAIN.pdf §7.3.3 (Estat de les eleccions)
"""

from dataclasses import dataclass


@dataclass
class ElectionState:
    """
    Estat complet d'una eleccio llegit des de la blockchain Algorand.

    Representa l'instant concret dels resultats electorals tal com estan
    emmagatzemats a les boxes del contracte SistemaVotacion:
      - Box amb prefix "ec" (P_ELEC_CAND): llista de candidats
      - Box amb prefix "ev" (P_ELEC_VOT): recompte de vots per candidat

    L'ordre dels candidats i dels vots es corresponent: votes[i] es el
    nombre de vots que ha rebut candidates[i].

    Atributs:
        election_name: Identificador unic de l'eleccio (ex: "Rector2026").
                       Coincideix amb la clau usada al Box Storage.
        candidates:    Llista ordenada de noms de candidats, tal com es van
                       registrar a la proposta original (crear_propuesta).
        votes:         Recompte de vots per a cada candidat. La posicio i-esima
                       correspon al candidat i-esim de la llista.
        block_round:   Round d'Algorand en el qual es va llegir l'estat.
                       Util per a auditoria i verificacio temporal.
    """
    election_name: str
    candidates: list[str]
    votes: list[int]
    block_round: int = 0
