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
    """Tests per al metode intern _generar_eleccion()."""

    @pytest.mark.skip(reason="Pendent: requereix localnet i artifacts compilats")
    def test_eleccio_generada_te_mateixos_candidats(self, app_client):
        """
        Verifica que l'eleccio generada conte exactament els mateixos
        candidats que la proposta original.
        """
        pass

    @pytest.mark.skip(reason="Pendent: requereix localnet i artifacts compilats")
    def test_eleccio_generada_vots_array_zeros(self, app_client):
        """
        Verifica que el DynamicArray de vots de l'eleccio generada
        conte tots zeros, amb la mateixa longitud que el nombre
        de candidats.
        """
        pass

    @pytest.mark.skip(reason="Pendent: requereix localnet i artifacts compilats")
    def test_proposta_tancada_despres_de_generacio(self, app_client):
        """
        Verifica que un cop generada l'eleccio, no es pot votar
        mes la proposta (validar_propuesta_activa falla).
        """
        pass

    @pytest.mark.skip(reason="Pendent: requereix localnet i artifacts compilats")
    def test_llindar_arrodonit_amunt(self, app_client):
        """
        Verifica que el llindar es ceil(50% cens).
        Amb cens=5: llindar=3 (no 2).
        Amb cens=4: llindar=2.
        Amb cens=3: llindar=2 (no 1).
        """
        pass

    @pytest.mark.skip(reason="Pendent: requereix localnet i artifacts compilats")
    def test_cens_proposta_compartit_amb_eleccio(self, app_client):
        """
        Verifica que el cens de l'eleccio generada es el mateix
        que el de la proposta (mateixa clau al BoxMap).
        """
        pass
