"""
Modul: contract.py (Router principal)
Descripcio: Smart Contract principal del sistema de votacio.
            Implementa el patro Router (DT-01) via ARC4Contract.
            En algopy, l'enrutament es automatic: cada @abimethod
            genera una entrada al router ABI compilat a TEAL.
            Integra verificador (DT-02), propostes (DT-03),
            votacio (DT-04) i generador d'eleccions.
Estat: IMPLEMENTAT (votacio pluralitat) / PARCIAL (Schulze pendent)
Depend: constants.py (prefixos BoxMap, llindars)
Referencia: Decisions tecniques DT-01 a DT-05, seccio 7.3.2 document d'abast

NOTA IMPORTANT SOBRE LA TECNOLOGIA:
  L'arquitectura original especificava PyTeal amb Cond() manual.
  La implementacio usa algopy (Algorand Python / Puya compiler),
  que es la tecnologia RECOMANADA per Algorand (PyTeal es legacy).
  El compilador Puya genera TEAL optimitzat amb routing ABI automatic.
  Totes les decisions tecniques (DT-01 a DT-05) es compleixen igualment.
"""

from algopy import ARC4Contract, arc4, BoxMap, Txn
from algopy.arc4 import abimethod

from .constants import (
    P_CENSO_DIR, P_CENSO_TOT,
    P_PROP_CAND, P_PROP_VOT, P_PROP_REG,
    P_ELEC_CAND, P_ELEC_VOT, P_ELEC_REG,
    CENSO_GENERICO, THRESHOLD_DIVISOR,
)


class SistemaVotacio(ARC4Contract):
    """
    Smart Contract de votacio electronica descentralitzada.

    Moduls logics (implementats com a grups de metodes):
    - Cens electoral: generar_cens_global
    - Propostes: crear_proposta, votar_proposta
    - Generador d'eleccions: _generar_eleccio (intern)
    - Votacio: votar_eleccio, consultar_resultats
    - Verificadors: _verificar_* i _validar_* (interns)
    """

    def __init__(self) -> None:
        # ==========================================================
        # 1. CENS ELECTORAL (DT-03: Box Storage)
        # ==========================================================
        # Clau: (nom_eleccio, adreca_votant) -> True/False
        self.cens_adreces = BoxMap(
            arc4.Tuple[arc4.String, arc4.Address],
            arc4.Bool,
            key_prefix=P_CENSO_DIR,
        )
        # Clau: nom_eleccio -> total persones al cens
        self.cens_totals = BoxMap(
            arc4.String,
            arc4.UInt64,
            key_prefix=P_CENSO_TOT,
        )

        # ==========================================================
        # 2. PROPOSTES D'ELECCIONS (DT-03: Box Storage)
        # ==========================================================
        # Candidats d'una proposta
        self.propostes_candidats = BoxMap(
            arc4.String,
            arc4.DynamicArray[arc4.String],
            key_prefix=P_PROP_CAND,
        )
        # Total de vots a favor de la proposta
        self.propostes_vots = BoxMap(
            arc4.String,
            arc4.UInt64,
            key_prefix=P_PROP_VOT,
        )
        # Registre de qui ha votat cada proposta
        self.propostes_registres = BoxMap(
            arc4.Tuple[arc4.String, arc4.Address],
            arc4.Bool,
            key_prefix=P_PROP_REG,
        )

        # ==========================================================
        # 3. ELECCIONS ACTIVES (DT-03: Box Storage)
        # ==========================================================
        # Candidats d'una eleccio
        self.eleccions_candidats = BoxMap(
            arc4.String,
            arc4.DynamicArray[arc4.String],
            key_prefix=P_ELEC_CAND,
        )
        # Vots per candidat: (nom_eleccio, candidat) -> total
        self.eleccions_vots = BoxMap(
            arc4.Tuple[arc4.String, arc4.String],
            arc4.UInt64,
            key_prefix=P_ELEC_VOT,
        )
        # Registre de qui ha votat cada eleccio
        self.eleccions_registres = BoxMap(
            arc4.Tuple[arc4.String, arc4.Address],
            arc4.Bool,
            key_prefix=P_ELEC_REG,
        )

    # ==========================================================
    # MODUL: CENS ELECTORAL
    # ==========================================================

    @abimethod
    def generar_cens_global(
        self,
        adreces: arc4.DynamicArray[arc4.Address],
    ) -> None:
        """
        Afegeix adreces al cens generic (CENSO_GENERAL).
        Maxim 7 adreces per transaccio (restriccio AVM).

        TODO: Restringir a una autoritat (creador del SC).
        Ara qualsevol pot cridar-ho, cosa que no es segura en produccio.
        """
        for adreca in adreces:
            self._verificar_inexistencia_cens(
                arc4.String(CENSO_GENERICO), adreca,
            )
            clau = arc4.Tuple((arc4.String(CENSO_GENERICO), adreca))
            self.cens_adreces[clau] = arc4.Bool(True)

        total_actual = self.cens_totals.get(
            arc4.String(CENSO_GENERICO), default=arc4.UInt64(0),
        )
        self.cens_totals[arc4.String(CENSO_GENERICO)] = arc4.UInt64(
            total_actual.native + adreces.length,
        )

    # ==========================================================
    # MODUL: PROPOSTES (DT-03)
    # ==========================================================

    @abimethod
    def crear_proposta(
        self,
        nom_proposta: arc4.String,
        candidats: arc4.DynamicArray[arc4.String],
        cens: arc4.DynamicArray[arc4.Address],
    ) -> None:
        """
        Crea una proposta d'eleccio amb candidats i cens propi.
        Requereix que el creador pertanyi al cens generic.
        """
        self._verificar_cens(
            arc4.String(CENSO_GENERICO), arc4.Address(Txn.sender),
        )
        self._validar_proposta(nom_proposta, ha_d_existir=False)
        assert cens.length > 0, \
            "[ERROR] Ha d'existir almenys una adreca al cens"

        self.propostes_vots[nom_proposta] = arc4.UInt64(0)
        self.propostes_candidats[nom_proposta] = candidats.copy()

        # Crear cens especific per a la proposta/eleccio
        self.cens_totals[nom_proposta] = arc4.UInt64(cens.length)
        for adreca in cens:
            clau = arc4.Tuple((nom_proposta, adreca))
            self.cens_adreces[clau] = arc4.Bool(True)

    @abimethod
    def votar_proposta(self, nom_proposta: arc4.String) -> None:
        """
        Vota a favor d'una proposta.
        Si s'assoleix el llindar, genera l'eleccio automaticament.
        """
        self._validar_proposta(nom_proposta, ha_d_existir=True)
        adreca_votant = arc4.Address(Txn.sender)

        self._verificar_cens(nom_proposta, adreca_votant)
        self._validar_proposta_activa(nom_proposta)
        self._validar_no_doble_vot_proposta(nom_proposta, adreca_votant)

        # Registrar vot (DT-04: atomic)
        clau_registre = arc4.Tuple((nom_proposta, adreca_votant))
        self.propostes_registres[clau_registre] = arc4.Bool(True)

        self.propostes_vots[nom_proposta] = arc4.UInt64(
            self.propostes_vots[nom_proposta].native + 1,
        )

        # Intentar generar l'eleccio si s'assoleix el llindar
        self._generar_eleccio(nom_proposta)

    # ==========================================================
    # MODUL: GENERADOR D'ELECCIONS (DT-04)
    # ==========================================================

    def _generar_eleccio(self, nom_proposta: arc4.String) -> None:
        """
        Genera una eleccio automaticament quan la proposta assoleix
        el llindar de vots (50% del cens de la proposta).
        Els candidats es copien de la proposta.
        """
        llindar = (
            self.cens_totals[nom_proposta].native // THRESHOLD_DIVISOR
        )
        vots = self.propostes_vots[nom_proposta].native

        if vots < llindar:
            return

        # Copiar candidats de la proposta a l'eleccio
        candidats = self.propostes_candidats[nom_proposta].copy()
        self.eleccions_candidats[nom_proposta] = candidats.copy()

        # Inicialitzar comptadors de vots a 0 per a cada candidat
        for candidat in candidats:
            clau_vot = arc4.Tuple((nom_proposta, candidat))
            self.eleccions_vots[clau_vot] = arc4.UInt64(0)

    # ==========================================================
    # MODUL: VOTACIO (DT-04: operacions atomiques)
    # ==========================================================

    @abimethod
    def votar_eleccio(
        self,
        nom_eleccio: arc4.String,
        candidat: arc4.String,
    ) -> None:
        """
        Emet un vot per un candidat en una eleccio activa.
        Votacio per pluralitat simple (un candidat per votant).

        TODO: Implementar votar_schulze() per a preferencies ordenades.
        """
        self._validar_existencia_eleccio(nom_eleccio)
        self._validar_candidat_en_eleccio(nom_eleccio, candidat)

        adreca_votant = arc4.Address(Txn.sender)
        self._verificar_cens(nom_eleccio, adreca_votant)
        self._validar_no_doble_vot_eleccio(nom_eleccio, adreca_votant)

        # Registrar que ha votat (DT-02: prevencio doble vot)
        clau_registre = arc4.Tuple((nom_eleccio, adreca_votant))
        self.eleccions_registres[clau_registre] = arc4.Bool(True)

        # Incrementar vots del candidat (DT-04: atomic)
        clau_vot = arc4.Tuple((nom_eleccio, candidat))
        self.eleccions_vots[clau_vot] = arc4.UInt64(
            self.eleccions_vots[clau_vot].native + 1,
        )

    @abimethod(readonly=True)
    def consultar_resultats(
        self,
        nom_eleccio: arc4.String,
        candidat: arc4.String,
    ) -> arc4.UInt64:
        """
        Consulta el nombre de vots d'un candidat en una eleccio.
        Metode readonly: no modifica l'estat del SC.
        """
        self._validar_existencia_eleccio(nom_eleccio)
        self._validar_candidat_en_eleccio(nom_eleccio, candidat)

        clau_vot = arc4.Tuple((nom_eleccio, candidat))
        return self.eleccions_vots[clau_vot]

    # ==========================================================
    # MODUL: VERIFICADORS (DT-02: Guard desacoblat)
    # Metodes interns de validacio. Si fallen, la transaccio
    # es reverteix completament (comportament atomic de l'AVM).
    # ==========================================================

    def _verificar_cens(
        self, cens: arc4.String, votant: arc4.Address,
    ) -> None:
        """Verifica pertinenca al cens. O(1) via BoxMap."""
        clau = arc4.Tuple((cens, votant))
        assert clau in self.cens_adreces, \
            "[ERROR] No estas al cens per realitzar aquesta accio."

    def _verificar_inexistencia_cens(
        self, cens: arc4.String, votant: arc4.Address,
    ) -> None:
        """Verifica que l'adreca NO pertany al cens."""
        clau = arc4.Tuple((cens, votant))
        assert clau not in self.cens_adreces, \
            "[ERROR] L'adreca ja es al cens per a aquesta accio."

    def _validar_proposta(
        self, proposta: arc4.String, *, ha_d_existir: bool,
    ) -> None:
        """Valida existencia o inexistencia d'una proposta."""
        if ha_d_existir:
            assert proposta in self.propostes_vots, \
                "[ERROR] La proposta d'eleccions no existeix."
        else:
            assert proposta not in self.propostes_vots, \
                "[ERROR] La proposta d'eleccions ja existeix."

    def _validar_no_doble_vot_proposta(
        self, proposta: arc4.String, votant: arc4.Address,
    ) -> None:
        """Prevencio de doble vot en propostes. O(1)."""
        clau = arc4.Tuple((proposta, votant))
        assert clau not in self.propostes_registres, \
            "[ERROR] Aquesta adreca ja ha votat en aquesta proposta."

    def _validar_proposta_activa(self, proposta: arc4.String) -> None:
        """Verifica que la proposta no s'ha convertit en eleccio."""
        assert proposta not in self.eleccions_candidats, \
            "[ERROR] La proposta ja ha passat a ser una eleccio."

    def _validar_existencia_eleccio(
        self, nom_eleccio: arc4.String,
    ) -> None:
        """Verifica que l'eleccio existeix."""
        assert nom_eleccio in self.eleccions_candidats, \
            "[ERROR] L'eleccio no existeix."

    def _validar_candidat_en_eleccio(
        self, nom_eleccio: arc4.String, candidat: arc4.String,
    ) -> None:
        """Verifica que el candidat pertany a l'eleccio. O(1)."""
        clau = arc4.Tuple((nom_eleccio, candidat))
        assert clau in self.eleccions_vots, \
            "[ERROR] El candidat no pertany a aquesta eleccio."

    def _validar_no_doble_vot_eleccio(
        self, nom_eleccio: arc4.String, votant: arc4.Address,
    ) -> None:
        """Prevencio de doble vot en eleccions. O(1)."""
        clau = arc4.Tuple((nom_eleccio, votant))
        assert clau not in self.eleccions_registres, \
            "[ERROR] Aquesta adreca ja ha votat en aquesta eleccio."
