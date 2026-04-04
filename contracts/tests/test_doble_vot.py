"""
Tests: test_doble_vot.py
Descripcio: Tests de prevencio de doble vot tant en propostes
            com en eleccions. Critica per a la integritat electoral.
Estat: PLACEHOLDER (tests definits, pendents d'execucio)
Depend: conftest.py, artifacts compilats
Referencia: HU-05 (Prevencio doble vot), DT-02 (Verificador Guard)
"""

import pytest


class TestDobleVotPropostes:
    """Tests de prevencio de doble vot en propostes."""

    @pytest.mark.skip(reason="Pendent: requereix localnet i artifacts compilats")
    def test_primer_vot_proposta_acceptat(self, app_client):
        """
        Verifica que el primer vot d'un votant en una proposta
        es acceptat correctament.
        """
        pass

    @pytest.mark.skip(reason="Pendent: requereix localnet i artifacts compilats")
    def test_segon_vot_proposta_rebutjat(self, app_client):
        """
        Verifica que un segon vot del mateix votant en la mateixa
        proposta llanca error i NO modifica l'estat.
        AC1 de HU-05: la transaccio es reverteix completament.
        """
        pass


class TestDobleVotEleccions:
    """Tests de prevencio de doble vot en eleccions."""

    @pytest.mark.skip(reason="Pendent: requereix localnet i artifacts compilats")
    def test_primer_vot_eleccio_acceptat(self, app_client):
        """
        Verifica que el primer vot d'un votant en una eleccio
        es acceptat correctament.
        """
        pass

    @pytest.mark.skip(reason="Pendent: requereix localnet i artifacts compilats")
    def test_segon_vot_eleccio_rebutjat(self, app_client):
        """
        Verifica que un segon vot del mateix votant en la mateixa
        eleccio llanca error.
        AC1 de HU-05: la transaccio falla completament.
        """
        pass

    @pytest.mark.skip(reason="Pendent: requereix localnet i artifacts compilats")
    def test_vot_diferent_eleccio_acceptat(self, app_client):
        """
        Verifica que un votant pot votar en dues eleccions DIFERENTS.
        El doble vot nomes es per a la mateixa eleccio.
        """
        pass
