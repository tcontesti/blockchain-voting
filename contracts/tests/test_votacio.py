"""
Tests: test_votacio.py
Descripcio: Tests unitaris per a la logica de votacio en eleccions.
            Cobreix votacio per pluralitat, consulta de resultats
            i prevencio de vots invalids.
Estat: PLACEHOLDER (tests definits, pendents d'execucio)
Depend: conftest.py, artifacts compilats
Referencia: HU-03 (Emetre vot), HU-05 (Prevencio doble vot)
"""

import pytest


class TestVotacioEleccio:
    """Tests per al metode votar_eleccio()."""

    @pytest.mark.skip(reason="Pendent: requereix localnet i artifacts compilats")
    def test_vot_valid(self, app_client):
        """
        Verifica que un votant del cens pot emetre un vot valid.
        AC1 de HU-03: el vot es registra correctament al SC.
        """
        pass

    @pytest.mark.skip(reason="Pendent: requereix localnet i artifacts compilats")
    def test_vot_incrementa_comptador(self, app_client):
        """
        Verifica que el comptador del candidat s'incrementa en 1.
        AC2 de HU-03: el recompte reflecteix el vot.
        """
        pass

    @pytest.mark.skip(reason="Pendent: requereix localnet i artifacts compilats")
    def test_vot_candidat_inexistent_falla(self, app_client):
        """
        Verifica que votar per un candidat que no pertany a l'eleccio
        llanca un error.
        """
        pass

    @pytest.mark.skip(reason="Pendent: requereix localnet i artifacts compilats")
    def test_vot_eleccio_inexistent_falla(self, app_client):
        """
        Verifica que votar en una eleccio que no existeix llanca error.
        """
        pass


class TestConsultaResultats:
    """Tests per al metode consultar_resultats()."""

    @pytest.mark.skip(reason="Pendent: requereix localnet i artifacts compilats")
    def test_resultats_inicials_zero(self, app_client):
        """
        Verifica que els resultats d'una eleccio nova son 0 per a
        tots els candidats.
        """
        pass

    @pytest.mark.skip(reason="Pendent: requereix localnet i artifacts compilats")
    def test_resultats_despres_de_vots(self, app_client):
        """
        Verifica que consultar_resultats retorna el total correcte
        despres de multiples vots.
        """
        pass
