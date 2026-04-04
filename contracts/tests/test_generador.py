"""
Tests: test_generador.py
Descripcio: Tests per a la generacio automatica d'eleccions
            a partir de propostes que assoleixen el llindar.
Estat: PLACEHOLDER (tests definits, pendents d'execucio)
Depend: conftest.py, artifacts compilats
Referencia: DT-04 (Generador d'eleccions amb llindar)
"""

import pytest


class TestGeneradorEleccions:
    """Tests per al metode intern _generar_eleccio()."""

    @pytest.mark.skip(reason="Pendent: requereix localnet i artifacts compilats")
    def test_eleccio_generada_te_mateixos_candidats(self, app_client):
        """
        Verifica que l'eleccio generada conte exactament els mateixos
        candidats que la proposta original.
        """
        pass

    @pytest.mark.skip(reason="Pendent: requereix localnet i artifacts compilats")
    def test_eleccio_generada_vots_a_zero(self, app_client):
        """
        Verifica que tots els candidats de l'eleccio generada
        comencen amb 0 vots.
        """
        pass

    @pytest.mark.skip(reason="Pendent: requereix localnet i artifacts compilats")
    def test_proposta_tancada_despres_de_generacio(self, app_client):
        """
        Verifica que un cop generada l'eleccio, no es pot votar
        mes la proposta (validar_proposta_activa falla).
        """
        pass

    @pytest.mark.skip(reason="Pendent: requereix localnet i artifacts compilats")
    def test_llindar_50_per_cent(self, app_client):
        """
        Verifica que el llindar es exactament el 50% del cens.
        Amb cens=10, calen 5 vots per generar l'eleccio.
        """
        pass
