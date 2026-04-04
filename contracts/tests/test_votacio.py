"""
Tests: test_votacio.py
Descripcio: Tests unitaris per a la logica de votacio en eleccions.
            Cobreix votacio per pluralitat (array indexat per candidat),
            consulta de resultats i prevencio de vots invalids.
Estat: PLACEHOLDER (tests definits, pendents d'execucio)
Depend: conftest.py, artifacts compilats
Referencia: HU-03 (Emetre vot), HU-05 (Prevencio doble vot)
"""

import pytest


class TestVotacioEleccio:
    """Tests per al metode votar_eleccion()."""

    @pytest.mark.skip(reason="Pendent: requereix localnet i artifacts compilats")
    def test_vot_valid(self, app_client):
        """
        Verifica que un votant del cens pot emetre un vot valid.
        El vot incrementa el comptador a l'index del candidat dins
        el DynamicArray de vots.
        AC1 de HU-03.
        """
        pass

    @pytest.mark.skip(reason="Pendent: requereix localnet i artifacts compilats")
    def test_vot_incrementa_comptador_candidat_correcte(self, app_client):
        """
        Verifica que el comptador s'incrementa nomes per al candidat
        votat i no per als altres.
        Amb candidats=["A","B","C"] i vot per "B",
        vots ha de ser [0,1,0].
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

    @pytest.mark.skip(reason="Pendent: requereix localnet i artifacts compilats")
    def test_vot_fora_cens_falla(self, app_client):
        """
        Verifica que una adreca fora del cens de l'eleccio
        no pot votar.
        """
        pass

    @pytest.mark.skip(reason="Pendent: requereix localnet i artifacts compilats")
    def test_multiples_vots_diferents_votants(self, app_client):
        """
        Verifica que multiples votants poden votar correctament
        i els comptadors s'acumulen be.
        """
        pass
