"""
Modul: algorand_reader.py
Descripcio: Llegeix l'estat de les eleccions des de la blockchain Algorand
            via l'API REST d'algod. Cada node universitari usa aquest modul
            per obtenir de forma independent els resultats electorals (candidats
            i recompte de vots) emmagatzemats al Box Storage del contracte
            SistemaVotacion.

            El contracte emmagatzema les dades electorals en boxes amb prefixos
            de 2 bytes definits a constants.py:
              - "ec" (P_ELEC_CAND): candidats codificats com a DynamicArray[String]
              - "ev" (P_ELEC_VOT): vots codificats com a DynamicArray[UInt64]

            Les claus de les boxes segueixen el format:
              prefix + abi_encode_string(nom_eleccio)

            On abi_encode_string codifica el nom en format ARC-4:
              2 bytes (big-endian) amb la longitud + bytes UTF-8 del nom.

            Exemple: per l'eleccio "Rector2026":
              Clau candidats = b"ec" + b"\x00\x0aRector2026"
              Clau vots      = b"ev" + b"\x00\x0aRector2026"

Referencia: BLOCKCHAIN.pdf §7.3.3 (Gestor d'ancoratge)
Depend:     constants.py (prefixos P_ELEC_CAND = b"ec", P_ELEC_VOT = b"ev")
"""

import base64
import logging
import struct
from typing import Optional

from algosdk.v2client.algod import AlgodClient

from .models import ElectionState

logger = logging.getLogger(__name__)

# Prefixos de box del contracte SistemaVotacion.
# Replicats aqui des de contracts/smart_contracts/voting/constants.py
# per evitar una dependencia directa amb el paquet del contracte.
P_ELEC_CAND = b"ec"  # Box que emmagatzema els candidats d'una eleccio
P_ELEC_VOT = b"ev"  # Box que emmagatzema els vots d'una eleccio


def _abi_encode_string(s: str) -> bytes:
    """
    Codifica una cadena de text en format ARC-4 (ABI d'Algorand).

    El format ARC-4 per a strings consisteix en:
      - 2 bytes big-endian: longitud de la cadena en bytes
      - N bytes: contingut UTF-8 de la cadena

    Aquesta codificacio es necessaria per construir les claus de les boxes,
    ja que el contracte SistemaVotacion usa noms d'eleccio codificats en
    ARC-4 com a part de la clau de cada box.

    Args:
        s: Cadena de text a codificar (ex: "Rector2026").

    Returns:
        Bytes amb el format [2 bytes longitud][contingut UTF-8].

    Exemple:
        >>> _abi_encode_string("AB")
        b'\\x00\\x02AB'
        >>> _abi_encode_string("")
        b'\\x00\\x00'
    """
    encoded = s.encode("utf-8")
    return struct.pack(">H", len(encoded)) + encoded


def _decode_dynamic_string_array(raw: bytes) -> list[str]:
    """
    Descodifica un DynamicArray[String] codificat en format ARC-4.

    El contracte SistemaVotacion emmagatzema la llista de candidats d'una
    eleccio com a DynamicArray[String] dins la box amb prefix "ec".
    Aquesta funcio descodifica els bytes crus per obtenir la llista de noms.

    Format binari ARC-4 d'un DynamicArray[String]:
      [2 bytes: nombre d'elements (big-endian uint16)]
      [2 bytes per element: offset relatiu a la posicio del primer offset]
      [per cada element: 2 bytes longitud + bytes UTF-8 del contingut]

    Els offsets son relatius al byte immediatament posterior al camp de count
    (byte 2 del buffer).

    Args:
        raw: Bytes crus llegits directament de la box d'Algorand.

    Returns:
        Llista de cadenes de text (noms de candidats).
        Retorna llista buida si l'array es buit o les dades son insuficients.

    Exemple:
        Per a ["Alice", "Bob"], el format binari seria:
          count=2, offset_alice, offset_bob, len("Alice")+Alice, len("Bob")+Bob
    """
    if len(raw) < 2:
        return []

    num_elements = struct.unpack(">H", raw[0:2])[0]
    if num_elements == 0:
        return []

    # Llegir els offsets de cada element (relatius a la posicio post-count)
    offsets = []
    for i in range(num_elements):
        offset_pos = 2 + i * 2
        offset = struct.unpack(">H", raw[offset_pos : offset_pos + 2])[0]
        offsets.append(offset)

    # Descodificar cada string usant el seu offset
    strings = []
    for offset in offsets:
        abs_offset = 2 + offset  # Offset absolut dins el buffer (post-count)
        str_len = struct.unpack(">H", raw[abs_offset : abs_offset + 2])[0]
        str_bytes = raw[abs_offset + 2 : abs_offset + 2 + str_len]
        strings.append(str_bytes.decode("utf-8"))

    return strings


def _decode_dynamic_uint64_array(raw: bytes) -> list[int]:
    """
    Descodifica un DynamicArray[UInt64] codificat en format ARC-4.

    El contracte SistemaVotacion emmagatzema el recompte de vots de cada
    candidat com a DynamicArray[UInt64] dins la box amb prefix "ev".
    La posicio i-esima del resultat correspon als vots del candidat i-esim.

    Format binari ARC-4 d'un DynamicArray[UInt64]:
      [2 bytes: nombre d'elements (big-endian uint16)]
      [8 bytes per element: valor uint64 big-endian]

    A diferencia de DynamicArray[String], els UInt64 tenen mida fixa (8 bytes)
    i no necessiten offsets.

    Args:
        raw: Bytes crus llegits directament de la box d'Algorand.

    Returns:
        Llista d'enters (recompte de vots per candidat).
        Retorna llista buida si l'array es buit o les dades son insuficients.

    Exemple:
        Per a [42, 31, 27] (vots de 3 candidats):
          count=3, seguint de tres blocs de 8 bytes cadascun.
    """
    if len(raw) < 2:
        return []

    num_elements = struct.unpack(">H", raw[0:2])[0]
    values = []
    for i in range(num_elements):
        pos = 2 + i * 8
        value = struct.unpack(">Q", raw[pos : pos + 8])[0]
        values.append(value)

    return values


class AlgorandElectionReader:
    """
    Lector d'estat electoral des de la blockchain Algorand.

    Cada node universitari instancia un AlgorandElectionReader connectat
    al seu node algod per llegir de forma independent l'estat de les
    eleccions. Aixo garanteix que cada universitat verifica els resultats
    per si mateixa, sense dependre de cap altre node.

    El lector accedeix al Box Storage del contracte SistemaVotacion
    (identificat per app_id) i descodifica les estructures ARC-4 per
    obtenir els candidats i els vots de cada eleccio.

    Atributs:
        algod:  Client de connexio al node algod d'Algorand.
        app_id: Identificador de l'aplicacio (APP_ID) del contracte
                SistemaVotacion desplegat a la blockchain.
    """

    def __init__(self, algod_client: AlgodClient, app_id: int):
        """
        Inicialitza el lector d'eleccions.

        Args:
            algod_client: Client AlgodClient connectat a un node Algorand
                          (localnet per a desenvolupament, testnet/mainnet
                          per a produccio).
            app_id:       APP_ID del contracte SistemaVotacion desplegat.
                          S'obte despres d'executar deploy.py.
        """
        self.algod = algod_client
        self.app_id = app_id

    def _get_box_value(self, box_name: bytes) -> Optional[bytes]:
        """
        Llegeix el valor d'una box del contracte pel seu nom.

        Les boxes d'Algorand son parelles clau-valor associades a una
        aplicacio. Cada box te un nom (bytes) i un valor (bytes).
        Aquesta funcio consulta l'API REST d'algod per obtenir el valor.

        Args:
            box_name: Nom de la box en bytes (ex: b"ec\\x00\\x0aRector2026").

        Returns:
            Bytes crus del valor de la box, o None si la box no existeix
            (l'eleccio encara no s'ha creat o el nom es incorrecte).
        """
        try:
            result = self.algod.application_box_by_name(self.app_id, box_name)
            return base64.b64decode(result["value"])
        except Exception as e:
            logger.debug(f"Box no trobada: {box_name!r} -> {e}")
            return None

    def read_election_state(self, election_name: str) -> Optional[ElectionState]:
        """
        Llegeix l'estat complet d'una eleccio des de les boxes d'Algorand.

        Construeix les claus de box usant el prefix corresponent + el nom
        de l'eleccio codificat en ARC-4, i descodifica els valors:
          - Box "ec" + abi(nom): candidats (DynamicArray[String])
          - Box "ev" + abi(nom): vots (DynamicArray[UInt64])

        Si la box de candidats no existeix, l'eleccio no s'ha creat encara
        al contracte. Si la box de vots no existeix pero la de candidats si,
        s'assumeix que tots els candidats tenen 0 vots (eleccio recent).

        Args:
            election_name: Nom identificador de l'eleccio (ex: "Rector2026").
                           Ha de coincidir exactament amb el nom usat a
                           crear_propuesta() del contracte.

        Returns:
            ElectionState amb els candidats, vots i round actual,
            o None si l'eleccio no existeix al contracte.
        """
        key_suffix = _abi_encode_string(election_name)

        # Llegir candidats des de la box amb prefix "ec"
        cand_box_name = P_ELEC_CAND + key_suffix
        cand_raw = self._get_box_value(cand_box_name)
        if cand_raw is None:
            logger.warning(f"Eleccio '{election_name}' no trobada (sense candidats)")
            return None

        candidates = _decode_dynamic_string_array(cand_raw)

        # Llegir vots des de la box amb prefix "ev"
        votes_box_name = P_ELEC_VOT + key_suffix
        votes_raw = self._get_box_value(votes_box_name)
        votes = _decode_dynamic_uint64_array(votes_raw) if votes_raw else [0] * len(candidates)

        # Obtenir el round actual d'Algorand per referencia temporal
        try:
            status = self.algod.status()
            block_round = status.get("last-round", 0)
        except Exception:
            block_round = 0

        return ElectionState(
            election_name=election_name,
            candidates=candidates,
            votes=votes,
            block_round=block_round,
        )

    def get_all_election_names(self) -> list[str]:
        """
        Llista totes les eleccions actives escanejant les boxes del contracte.

        Recorre totes les boxes de l'aplicacio i filtra les que comencen
        amb el prefix "ec" (P_ELEC_CAND). Per a cada box trobada, extreu
        el nom de l'eleccio descodificant la part ARC-4 de la clau.

        Aixo permet al servei d'ancoratge descobrir automaticament quines
        eleccions existeixen al contracte sense necessitat de mantenir un
        registre extern.

        Returns:
            Llista de noms d'eleccions (ex: ["Rector2026", "Dega2026"]).
            Retorna llista buida si no hi ha eleccions o si hi ha un error
            de connexio amb el node algod.
        """
        try:
            boxes_response = self.algod.application_boxes(self.app_id)
            boxes = boxes_response.get("boxes", [])
        except Exception as e:
            logger.error(f"Error llegint boxes de l'aplicacio {self.app_id}: {e}")
            return []

        election_names = []
        for box_info in boxes:
            box_name = base64.b64decode(box_info["name"])
            # Filtrar nomes les boxes de candidats (prefix "ec")
            if box_name.startswith(P_ELEC_CAND):
                # La part posterior al prefix es el nom ARC-4: [2 bytes len][UTF-8]
                suffix = box_name[len(P_ELEC_CAND) :]
                if len(suffix) >= 2:
                    str_len = struct.unpack(">H", suffix[0:2])[0]
                    name = suffix[2 : 2 + str_len].decode("utf-8")
                    election_names.append(name)

        return election_names
