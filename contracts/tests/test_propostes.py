"""
Tests: test_propostes.py
Descripcio: Tests per a la logica de propostes: creacio, votacio
            i generacio automatica d'eleccions.
Estat: PLACEHOLDER (tests definits, pendents d'execucio)
Depend: conftest.py, artifacts compilats
Referencia: HU-06 (Crear proposta), HU-07 (Votar proposta)
"""

import pytest


class TestCrearProposta:
    """Tests per al metode crear_proposta()."""

    @pytest.mark.skip(reason="Pendent: requereix localnet i artifacts compilats")
    def test_crear_proposta_valida(self, app_client):
        """
        Verifica que un membre del cens pot crear una proposta
        amb candidats i cens.
        AC1 de HU-06.
        """
        pass

    @pytest.mark.skip(reason="Pendent: requereix localnet i artifacts compilats")
    def test_crear_proposta_duplicada_falla(self, app_client):
        """
        Verifica que no es pot crear una proposta amb un nom
        que ja existeix.
        """
        pass

    @pytest.mark.skip(reason="Pendent: requereix localnet i artifacts compilats")
    def test_crear_proposta_sense_cens_falla(self, app_client):
        """
        Verifica que no es pot crear una proposta amb cens buit.
        """
        pass

    @pytest.mark.skip(reason="Pendent: requereix localnet i artifacts compilats")
    def test_crear_proposta_fora_cens_falla(self, app_client):
        """
        Verifica que un usuari fora del cens generic no pot
        crear propostes.
        """
        pass


class TestVotarProposta:
    """Tests per al metode votar_proposta()."""

    @pytest.mark.skip(reason="Pendent: requereix localnet i artifacts compilats")
    def test_votar_proposta_valid(self, app_client):
        """
        Verifica que un membre del cens de la proposta pot votar.
        AC1 de HU-07.
        """
        pass

    @pytest.mark.skip(reason="Pendent: requereix localnet i artifacts compilats")
    def test_votar_proposta_genera_eleccio(self, app_client):
        """
        Verifica que quan s'assoleix el llindar (50% del cens),
        es genera automaticament una eleccio amb els mateixos candidats.
        AC2 de HU-07: generacio automatica d'eleccio.
        """
        pass

    @pytest.mark.skip(reason="Pendent: requereix localnet i artifacts compilats")
    def test_votar_proposta_sota_llindar_no_genera(self, app_client):
        """
        Verifica que si no s'assoleix el llindar, no es genera eleccio.
        """
        pass
