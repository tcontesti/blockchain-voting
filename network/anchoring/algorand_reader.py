"""
Modul: algorand_reader.py
Descripcio: Llegeix l'estat de les eleccions des de la blockchain Algorand
            via l'API REST d'algod. Descodifica els valors de Box Storage
            codificats en ARC-4.
Referencia: BLOCKCHAIN.pdf §7.3.3 (Gestor d'ancoratge)
Depend: constants.py (prefixos de box: P_ELEC_CAND = b"ec", P_ELEC_VOT = b"ev")
"""

import base64
import logging
import struct
from typing import Optional

from algosdk.v2client.algod import AlgodClient

from .models import ElectionState

logger = logging.getLogger(__name__)

# Prefixos de box del contracte (replicats de constants.py)
P_ELEC_CAND = b"ec"
P_ELEC_VOT = b"ev"


def _abi_encode_string(s: str) -> bytes:
    """Codifica una cadena en format ARC-4 (2 bytes longitud + UTF-8)."""
    encoded = s.encode("utf-8")
    return struct.pack(">H", len(encoded)) + encoded


def _decode_dynamic_string_array(raw: bytes) -> list[str]:
    """
    Descodifica un DynamicArray[String] ARC-4.

    Format:
      [2 bytes: num_elements]
      [2 bytes offset per element] x num_elements
      [per cada element: 2 bytes longitud + bytes UTF-8]
    """
    if len(raw) < 2:
        return []

    num_elements = struct.unpack(">H", raw[0:2])[0]
    if num_elements == 0:
        return []

    # Llegir offsets (relatius a l'inici de l'array)
    offsets = []
    for i in range(num_elements):
        offset_pos = 2 + i * 2
        offset = struct.unpack(">H", raw[offset_pos:offset_pos + 2])[0]
        offsets.append(offset)

    # Descodificar cada string
    strings = []
    for offset in offsets:
        abs_offset = 2 + offset  # offset relatiu al byte 2
        str_len = struct.unpack(">H", raw[abs_offset:abs_offset + 2])[0]
        str_bytes = raw[abs_offset + 2:abs_offset + 2 + str_len]
        strings.append(str_bytes.decode("utf-8"))

    return strings


def _decode_dynamic_uint64_array(raw: bytes) -> list[int]:
    """
    Descodifica un DynamicArray[UInt64] ARC-4.

    Format:
      [2 bytes: num_elements]
      [8 bytes big-endian uint64 per element] x num_elements
    """
    if len(raw) < 2:
        return []

    num_elements = struct.unpack(">H", raw[0:2])[0]
    values = []
    for i in range(num_elements):
        pos = 2 + i * 8
        value = struct.unpack(">Q", raw[pos:pos + 8])[0]
        values.append(value)

    return values


class AlgorandElectionReader:
    """Llegeix l'estat de les eleccions des d'Algorand box storage."""

    def __init__(self, algod_client: AlgodClient, app_id: int):
        self.algod = algod_client
        self.app_id = app_id

    def _get_box_value(self, box_name: bytes) -> Optional[bytes]:
        """Llegeix el valor d'una box pel seu nom (bytes)."""
        try:
            b64_name = base64.b64encode(box_name).decode("ascii")
            result = self.algod.application_box_by_name(
                self.app_id, box_name
            )
            return base64.b64decode(result["value"])
        except Exception as e:
            logger.debug(f"Box no trobada: {box_name!r} -> {e}")
            return None

    def read_election_state(self, election_name: str) -> Optional[ElectionState]:
        """
        Llegeix l'estat complet d'una eleccio des de les boxes d'Algorand.

        Llegeix:
          - Box "ec" + abi(election_name) -> candidats (DynamicArray[String])
          - Box "ev" + abi(election_name) -> vots (DynamicArray[UInt64])

        Returns:
            ElectionState o None si l'eleccio no existeix
        """
        key_suffix = _abi_encode_string(election_name)

        # Llegir candidats
        cand_box_name = P_ELEC_CAND + key_suffix
        cand_raw = self._get_box_value(cand_box_name)
        if cand_raw is None:
            logger.warning(f"Eleccio '{election_name}' no trobada (sense candidats)")
            return None

        candidates = _decode_dynamic_string_array(cand_raw)

        # Llegir vots
        votes_box_name = P_ELEC_VOT + key_suffix
        votes_raw = self._get_box_value(votes_box_name)
        votes = _decode_dynamic_uint64_array(votes_raw) if votes_raw else [0] * len(candidates)

        # Obtenir el round actual
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
        Llista totes les eleccions actives escanejant les boxes amb prefix 'ec'.

        Returns:
            Llista de noms d'eleccions
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
            if box_name.startswith(P_ELEC_CAND):
                # Extreure el nom: descodificar la part ARC-4 string
                suffix = box_name[len(P_ELEC_CAND):]
                if len(suffix) >= 2:
                    str_len = struct.unpack(">H", suffix[0:2])[0]
                    name = suffix[2:2 + str_len].decode("utf-8")
                    election_names.append(name)

        return election_names
