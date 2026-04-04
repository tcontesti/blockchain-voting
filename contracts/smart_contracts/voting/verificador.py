"""
Modul: verificador.py
Descripcio: Funcions de verificacio del Smart Contract de votacio.
            Comprova pertinenca al cens, prevencio de doble vot,
            existencia de propostes i eleccions.
            Implementa el patro Guard (DT-02) desacoblat del router.
Estat: IMPLEMENTAT
Depend: constants.py (prefixos de BoxMap)
Referencia: Decisio tecnica DT-02 (Verificacio desacoblada via Guard)
"""

from algopy import arc4, BoxMap


# ==========================================================
# VERIFICACIO DE CENS
# ==========================================================

def verificar_cens(
    censo_direcciones: BoxMap,
    censo: arc4.String,
    votante: arc4.Address,
) -> None:
    """
    Verifica que l'adreca pertany al cens especificat.
    Llanca assert si l'adreca no es al cens.
    Complexitat: O(1) via BoxMap lookup.
    """
    clave = arc4.Tuple((censo, votante))
    assert clave in censo_direcciones, \
        "[ERROR] No estas en el cens per realitzar aquesta accio."


def verificar_inexistencia_cens(
    censo_direcciones: BoxMap,
    censo: arc4.String,
    votante: arc4.Address,
) -> None:
    """
    Verifica que l'adreca NO pertany al cens (per evitar duplicats).
    Llanca assert si l'adreca ja es al cens.
    """
    clave = arc4.Tuple((censo, votante))
    assert clave not in censo_direcciones, \
        "[ERROR] L'adreca ja es al cens per a aquesta accio."


# ==========================================================
# VERIFICACIO DE PROPOSTES
# ==========================================================

def validar_proposta(
    propuestas_votos: BoxMap,
    propuesta: arc4.String,
    ha_d_existir: bool,
) -> None:
    """
    Valida l'existencia o inexistencia d'una proposta.
    Si ha_d_existir=True, llanca error si no existeix.
    Si ha_d_existir=False, llanca error si ja existeix.
    """
    if ha_d_existir:
        assert propuesta in propuestas_votos, \
            "[ERROR] La proposta d'eleccions no existeix."
    else:
        assert propuesta not in propuestas_votos, \
            "[ERROR] La proposta d'eleccions ja existeix."


def validar_no_doble_vot_proposta(
    propuestas_registros: BoxMap,
    propuesta: arc4.String,
    votante: arc4.Address,
) -> None:
    """
    Verifica que l'adreca no ha votat previament en aquesta proposta.
    Prevencio de doble vot en O(1) via BoxMap.
    """
    clave = arc4.Tuple((propuesta, votante))
    assert clave not in propuestas_registros, \
        "[ERROR] Aquesta adreca ja ha votat en aquesta proposta."


def validar_proposta_activa(
    elecciones_candidatos: BoxMap,
    propuesta: arc4.String,
) -> None:
    """
    Verifica que la proposta no ha passat encara a ser una eleccio.
    Un cop generada l'eleccio, la proposta es tanca.
    """
    assert propuesta not in elecciones_candidatos, \
        "[ERROR] La proposta ja ha passat a ser una eleccio."


# ==========================================================
# VERIFICACIO D'ELECCIONS
# ==========================================================

def validar_existencia_eleccio(
    elecciones_candidatos: BoxMap,
    nom_eleccio: arc4.String,
) -> None:
    """
    Verifica que l'eleccio existeix (te candidats registrats).
    """
    assert nom_eleccio in elecciones_candidatos, \
        "[ERROR] L'eleccio no existeix."


def validar_candidat_en_eleccio(
    elecciones_votos: BoxMap,
    nom_eleccio: arc4.String,
    candidat: arc4.String,
) -> None:
    """
    Verifica que el candidat pertany a l'eleccio indicada.
    Comprova directament al BoxMap de vots (O(1)).
    """
    clave = arc4.Tuple((nom_eleccio, candidat))
    assert clave in elecciones_votos, \
        "[ERROR] El candidat no pertany a aquesta eleccio."


def validar_no_doble_vot_eleccio(
    elecciones_registros: BoxMap,
    nom_eleccio: arc4.String,
    votante: arc4.Address,
) -> None:
    """
    Verifica que l'adreca no ha votat previament en aquesta eleccio.
    Prevencio de doble vot en O(1) via BoxMap.
    """
    clave = arc4.Tuple((nom_eleccio, votante))
    assert clave not in elecciones_registros, \
        "[ERROR] Aquesta adreca ja ha votat en aquesta eleccio."
