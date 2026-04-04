"""
Modul: constants.py
Descripcio: Constants compartides per tots els moduls del Smart Contract
            de votacio. Inclou prefixos de BoxMap, llindars i identificadors.
Estat: IMPLEMENTAT
Depend: cap
Referencia: Decisio tecnica DT-03 (Box Storage vs Local State)
"""

from typing import Final

# ==========================================================
# PREFIXOS DE BOX STORAGE
# Cada prefix ha de ser unic i curt (2 bytes) per minimitzar
# el cost d'emmagatzematge a la blockchain.
# ==========================================================

# Cens electoral
P_CENSO_DIR: Final[bytes] = b"cd"        # (eleccio, adreca) -> bool
P_CENSO_TOT: Final[bytes] = b"ct"        # eleccio -> total persones

# Propostes d'eleccions
P_PROP_CAND: Final[bytes] = b"pc"        # proposta -> candidats[]
P_PROP_VOT: Final[bytes] = b"pv"         # proposta -> total vots a favor
P_PROP_REG: Final[bytes] = b"pr"         # (proposta, adreca) -> ha votat?
P_PROP_CENSO_CARG: Final[bytes] = b"pg"  # proposta -> adreces carregades al cens
P_PROP_CRADOR: Final[bytes] = b"pk"      # proposta -> adreca del creador

# Eleccions actives
P_ELEC_CAND: Final[bytes] = b"ec"        # eleccio -> candidats[]
P_ELEC_VOT: Final[bytes] = b"ev"         # eleccio -> vots[] (DynamicArray indexat per candidat)
P_ELEC_REG: Final[bytes] = b"er"         # (eleccio, adreca) -> ha votat?

# ==========================================================
# CONSTANTS GLOBALS
# ==========================================================

# Cens generic: cens compartit per a totes les propostes
CENSO_GENERICO: Final[str] = "CENSO_GENERAL"
