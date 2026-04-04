"""
Tests: test_propostes.py
Descripcio: Tests per a la logica de propostes: creacio, carrega de cens
            per lots, votacio i generacio automatica d'eleccions.
Estat: PLACEHOLDER (tests definits, pendents d'execucio)
Depend: conftest.py, artifacts compilats
Referencia: HU-06 (Crear proposta), HU-07 (Votar proposta)
"""

import pytest


class TestCrearProposta:
    """Tests per al metode crear_propuesta()."""

    @pytest.mark.skip(reason="Pendent: requereix localnet i artifacts compilats")
    def test_crear_proposta_valida(self, app_client):
        """
        Verifica que un membre del cens pot crear una proposta
        amb candidats i total de cens declarat.
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
    def test_crear_proposta_sense_candidats_falla(self, app_client):
        """
        Verifica que no es pot crear una proposta sense candidats.
        """
        pass

    @pytest.mark.skip(reason="Pendent: requereix localnet i artifacts compilats")
    def test_crear_proposta_cens_zero_falla(self, app_client):
        """
        Verifica que no es pot crear una proposta amb total_censo=0.
        """
        pass

    @pytest.mark.skip(reason="Pendent: requereix localnet i artifacts compilats")
    def test_crear_proposta_fora_cens_falla(self, app_client):
        """
        Verifica que un usuari fora del cens generic no pot
        crear propostes.
        """
        pass


class TestCarregarCensProposta:
    """Tests per al metode cargar_censo_propuesta()."""

    @pytest.mark.skip(reason="Pendent: requereix localnet i artifacts compilats")
    def test_carregar_cens_creador_ok(self, app_client):
        """
        Verifica que el creador de la proposta pot carregar
        adreces al cens en lots de fins a 4.
        """
        pass

    @pytest.mark.skip(reason="Pendent: requereix localnet i artifacts compilats")
    def test_carregar_cens_no_creador_falla(self, app_client):
        """
        Verifica que nomes el creador pot carregar el cens.
        Un altre membre del cens generic no pot fer-ho.
        """
        pass

    @pytest.mark.skip(reason="Pendent: requereix localnet i artifacts compilats")
    def test_carregar_cens_supera_limit_falla(self, app_client):
        """
        Verifica que no es poden carregar mes adreces que el
        total declarat a crear_propuesta().
        """
        pass

    @pytest.mark.skip(reason="Pendent: requereix localnet i artifacts compilats")
    def test_carregar_cens_lot_maxim_4(self, app_client):
        """
        Verifica que enviar mes de 4 adreces per transaccio falla.
        """
        pass


class TestVotarProposta:
    """Tests per al metode votar_propuesta()."""

    @pytest.mark.skip(reason="Pendent: requereix localnet i artifacts compilats")
    def test_votar_proposta_valid(self, app_client):
        """
        Verifica que un membre del cens de la proposta pot votar
        un cop el cens esta completament carregat.
        AC1 de HU-07.
        """
        pass

    @pytest.mark.skip(reason="Pendent: requereix localnet i artifacts compilats")
    def test_votar_proposta_cens_incomplet_falla(self, app_client):
        """
        Verifica que no es pot votar una proposta si el cens
        no esta completament carregat.
        """
        pass

    @pytest.mark.skip(reason="Pendent: requereix localnet i artifacts compilats")
    def test_votar_proposta_genera_eleccio(self, app_client):
        """
        Verifica que quan s'assoleix el llindar (ceil(50% cens)),
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
