"""
Modul: contract.py (Router principal)
Descripcio: Smart Contract principal del sistema de votacio electronica.
            Implementa el patro Router (DT-01) via ARC4Contract.
            En algopy, l'enrutament es automatic: cada @abimethod
            genera una entrada al router ABI compilat a TEAL.
            Integra verificador (DT-02), propostes (DT-03),
            votacio (DT-04) i generador d'eleccions.
Estat: IMPLEMENTAT (votacio pluralitat) / PARCIAL (Schulze pendent)
Depend: constants.py (prefixos BoxMap)
Referencia: Decisions tecniques DT-01 a DT-05, seccio 7.3.2 document d'abast
Autor: Marc Link (@linkcla)
"""

from algopy import ARC4Contract, arc4, BoxMap, Txn, UInt64, urange
from algopy.arc4 import abimethod
from .constants import (
    P_CENSO_DIR,
    P_CENSO_TOT,
    P_PROP_CAND,
    P_PROP_VOT,
    P_PROP_REG,
    P_PROP_CENSO_CARG,
    P_PROP_CRADOR,
    P_ELEC_CAND,
    P_ELEC_VOT,
    P_ELEC_REG,
    CENSO_GENERICO,
)


class SistemaVotacion(ARC4Contract):

    def __init__(self) -> None:
        # ==========================================================
        # 1. CENSO ELECTORAL
        # ==========================================================
        # Clave: (Eleccion, Direccion). Valor: True
        self.censo_direcciones = BoxMap(arc4.Tuple[arc4.String, arc4.Address], arc4.Bool, key_prefix=P_CENSO_DIR)

        # Clave: Eleccion. Valor: Total de personas en ese censo (Para calcular el threshold)
        self.censo_totales = BoxMap(arc4.String, arc4.UInt64, key_prefix=P_CENSO_TOT)

        # ==========================================================
        # 2. ESTADO DE PROPUESTAS DE ELECCIONES
        # ==========================================================
        self.propuestas_candidatos = BoxMap(arc4.String, arc4.DynamicArray[arc4.String], key_prefix=P_PROP_CAND)
        self.propuestas_votos = BoxMap(arc4.String, arc4.UInt64, key_prefix=P_PROP_VOT)
        self.propuestas_registros_votos = BoxMap(
            arc4.Tuple[arc4.String, arc4.Address], arc4.Bool, key_prefix=P_PROP_REG
        )
        self.propuestas_censo_cargado = BoxMap(arc4.String, arc4.UInt64, key_prefix=P_PROP_CENSO_CARG)
        self.propuestas_creador = BoxMap(arc4.String, arc4.Address, key_prefix=P_PROP_CRADOR)

        # ==========================================================
        # 3. ESTADO DE ELECCIONES ACTIVAS
        # ==========================================================
        self.elecciones_candidatos = BoxMap(arc4.String, arc4.DynamicArray[arc4.String], key_prefix=P_ELEC_CAND)
        self.elecciones_votos = BoxMap(arc4.String, arc4.DynamicArray[arc4.UInt64], key_prefix=P_ELEC_VOT)
        self.elecciones_registros_votos = BoxMap(
            arc4.Tuple[arc4.String, arc4.Address], arc4.Bool, key_prefix=P_ELEC_REG
        )

    # ==========================================================
    # LOGICA DE CARGA DE CENSO GLOBAL
    # ==========================================================
    # NOTA: SOLO SE PUEDE LLAMAR CON UN MAXIMO DE 7 DIRECCIONES POR TRANSACCION.
    @abimethod
    def cargar_censo_global(self, direcciones: arc4.DynamicArray[arc4.Address]) -> None:
        """Carga el censo global por lotes."""
        # En un futuro esta funcion estara restringida a una autoridad que se encargue de controlar el censo.
        # Actualmente cualquiera la puede llamar.

        # Investigar los *Transaction Groups* para agrupar 16 transacciones en un unico bloque.
        # Asi podemos cargar 112 usuarios de golpe.
        assert direcciones.length > 0, "[ERROR] Ha de enviar al menos una direccion para incrementar el censo."
        assert (
            direcciones.length <= 7
        ), "[ERROR] Solo se pueden enviar un maximo de 7 por limitaciones de atomicidad. Llame varias veces."

        for direccion in direcciones:
            self._verificar_inexistencia_usuario_censo(arc4.String(CENSO_GENERICO), direccion)
            clave_censo = arc4.Tuple((arc4.String(CENSO_GENERICO), direccion))
            self.censo_direcciones[clave_censo] = arc4.Bool(True)

        total_actual = self.censo_totales.get(arc4.String(CENSO_GENERICO), default=arc4.UInt64(0))
        self.censo_totales[arc4.String(CENSO_GENERICO)] = arc4.UInt64(total_actual.native + direcciones.length)

    # ==========================================================
    # LOGICA DE PROPUESTAS
    # ==========================================================
    @abimethod
    def crear_propuesta(
        self, nombre_propuesta: arc4.String, candidatos: arc4.DynamicArray[arc4.String], total_censo: arc4.UInt64
    ) -> None:
        """Inicializa la propuesta y declara el tamano final del censo."""
        self._verificar_censo(arc4.String(CENSO_GENERICO), arc4.Address(Txn.sender))
        self._validar_propuesta(nombre_propuesta, existente=arc4.Bool(False))

        assert candidatos.length > 0, "[ERROR] Ha de existir al menos un candidato en la propuesta."
        assert total_censo.native > 0, "[ERROR] El censo total declarado no puede ser 0."

        self.propuestas_votos[nombre_propuesta] = arc4.UInt64(0)
        self.propuestas_candidatos[nombre_propuesta] = candidatos.copy()

        # Guardamos el total que esperamos cargar
        self.censo_totales[nombre_propuesta] = total_censo

        # Inicializamos el contador de cargados a 0
        self.propuestas_censo_cargado[nombre_propuesta] = arc4.UInt64(0)

        # Guardar quien ha creado la propuesta para despues permitir que solo el
        # sea quien pueda agregar el censo de la propuesta.
        self.propuestas_creador[nombre_propuesta] = arc4.Address(Txn.sender)

    @abimethod
    def cargar_censo_propuesta(
        self, nombre_propuesta: arc4.String, censo_lote: arc4.DynamicArray[arc4.Address]
    ) -> None:
        """Carga el censo de la propuesta. Se pueden enviar lotes de como maximo 4 direcciones por transaccion."""
        self._validar_propuesta(nombre_propuesta, existente=arc4.Bool(True))
        self._validar_creador_propuesta(nombre_propuesta, arc4.Address(Txn.sender))

        assert censo_lote.length > 0, "[ERROR] Ha de enviar al menos una direccion para incrementar el censo."
        assert (
            censo_lote.length <= 4
        ), "[ERROR] Solo se pueden enviar un maximo de 4 por limitaciones de atomicidad. Llame varias veces."

        cargados_actualmente = self.propuestas_censo_cargado[nombre_propuesta]
        total_esperado = self.censo_totales[nombre_propuesta]
        self._validar_limite_censo_propuesta(cargados_actualmente, total_esperado, censo_lote.length)

        for direccion in censo_lote:
            self._verificar_inexistencia_usuario_censo(nombre_propuesta, direccion)

            clave_censo = arc4.Tuple((nombre_propuesta, direccion))
            self.censo_direcciones[clave_censo] = arc4.Bool(True)

        # Actualizamos el contador de direcciones cargadas
        self.propuestas_censo_cargado[nombre_propuesta] = arc4.UInt64(cargados_actualmente.native + censo_lote.length)

    # ==========================================================
    # LOGICA DE VOTAR PROPUESTA
    # ==========================================================
    @abimethod
    def votar_propuesta(self, nombre_propuesta: arc4.String) -> None:
        """Registra un voto sobre una propuesta."""
        self._validar_propuesta(nombre_propuesta, existente=arc4.Bool(True))

        direccion_sender = arc4.Address(Txn.sender)
        self._verificar_censo(nombre_propuesta, direccion_sender)
        self._validar_propuesta_activa(nombre_propuesta)
        self._validar_no_doble_voto_propuestas(nombre_propuesta, direccion_sender)

        # Registrar el voto
        clave_registro = arc4.Tuple((nombre_propuesta, direccion_sender))
        self.propuestas_registros_votos[clave_registro] = arc4.Bool(True)
        self.propuestas_votos[nombre_propuesta] = arc4.UInt64(self.propuestas_votos[nombre_propuesta].native + 1)

        self._generar_eleccion(nombre_propuesta)

    # ==========================================================
    # GENERADOR DE ELECCIONES
    # ==========================================================
    def _generar_eleccion(self, nombre_propuesta: arc4.String) -> None:
        """Crea la eleccion cuando la propuesta alcanza el umbral."""
        # Calculamos la mitad del censo como umbral (arredondeado hacia arriba)
        total_censo = self.censo_totales[nombre_propuesta].native
        threshold_propuesta = (total_censo // 2) + (total_censo % 2)
        votos_propuesta = self.propuestas_votos[nombre_propuesta].native

        # Si no se llega al umbral, no se genera la eleccion
        if votos_propuesta < threshold_propuesta:
            return

        candidatos = self.propuestas_candidatos[nombre_propuesta].copy()
        self.elecciones_candidatos[nombre_propuesta] = candidatos.copy()

        votos_iniciales = arc4.DynamicArray[arc4.UInt64]()
        for i in urange(candidatos.length):
            votos_iniciales.append(arc4.UInt64(0))

        self.elecciones_votos[nombre_propuesta] = votos_iniciales.copy()

    # ==========================================================
    # LOGICA DE VOTACION
    # ==========================================================
    @abimethod
    def votar_eleccion(self, nombre_eleccion: arc4.String, candidato: arc4.String) -> None:
        """Registra un voto en una eleccion activa."""
        direccion_sender = arc4.Address(Txn.sender)
        self._verificar_censo(nombre_eleccion, direccion_sender)

        self._validar_existencia_votacion(nombre_eleccion)
        indice_candidato = self._validar_candidato_en_eleccion(nombre_eleccion, candidato)

        self._validar_no_doble_voto_elecciones(nombre_eleccion, direccion_sender)

        # Guardamos que ha votado
        clave_registro = arc4.Tuple((nombre_eleccion, direccion_sender))
        self.elecciones_registros_votos[clave_registro] = arc4.Bool(True)

        votos = self.elecciones_votos[nombre_eleccion].copy()
        votos[indice_candidato.native] = arc4.UInt64(votos[indice_candidato.native].native + 1)
        self.elecciones_votos[nombre_eleccion] = votos.copy()

    # ==========================================================
    # VERIFICADORES
    # ==========================================================
    def _verificar_censo(self, censo: arc4.String, votante: arc4.Address) -> None:
        """Comprueba que la direccion pertenece al censo indicado."""
        clave = arc4.Tuple((censo, votante))
        assert clave in self.censo_direcciones, "[ERROR] No estas en el censo para realizar esta accion."

    def _verificar_inexistencia_usuario_censo(self, censo: arc4.String, votante: arc4.Address) -> None:
        """Comprueba que la direccion no esta ya registrada en el censo."""
        clave = arc4.Tuple((censo, votante))
        assert clave not in self.censo_direcciones, "[ERROR] La direccion ya esta en el censo para esta accion."

    def _validar_propuesta(self, propuesta: arc4.String, existente: arc4.Bool) -> None:
        """Valida si la propuesta existe o no segun el contexto del atributo 'existente'."""
        if existente.native:
            assert propuesta in self.propuestas_votos, "[ERROR] La propuesta de elecciones no existe."
        else:
            assert propuesta not in self.propuestas_votos, "[ERROR] La propuesta de elecciones ya existe."

    def _validar_propuesta_activa(self, propuesta: arc4.String) -> None:
        """Comprueba que la propuesta ya esta configurada y que no ha pasado a ser una eleccion."""
        assert (
            self.propuestas_censo_cargado[propuesta].native == self.censo_totales[propuesta].native
        ), "[ERROR] La propuesta aun se esta configurando (censo incompleto)."
        assert propuesta not in self.elecciones_candidatos, "[ERROR] La propuesta ya ha pasado a ser una eleccion."

    def _validar_creador_propuesta(self, propuesta: arc4.String, creador: arc4.Address) -> None:
        """Comprueba que quien llama es el creador de la propuesta."""
        assert (
            self.propuestas_creador[propuesta] == creador
        ), "[ERROR] Solo el creador de la propuesta puede realizar esta accion."

    def _validar_limite_censo_propuesta(
        self, cargados_actualmente: arc4.UInt64, total_esperado: arc4.UInt64, longitud_lote: UInt64
    ) -> None:
        """Evita cargar mas direcciones que las declaradas para la propuesta."""
        assert (
            cargados_actualmente.native + longitud_lote <= total_esperado.native
        ), "[ERROR] Superas el limite del censo declarado para esta propuesta."

    def _validar_no_doble_voto_propuestas(self, propuesta: arc4.String, votante: arc4.Address) -> None:
        """Evita que una direccion vote dos veces en la misma propuesta."""
        clave = arc4.Tuple((propuesta, votante))
        assert clave not in self.propuestas_registros_votos, "[ERROR] Esta direccion ya ha votado."

    def _validar_existencia_votacion(self, nombre_eleccion: arc4.String) -> None:
        """Comprueba que la eleccion existe."""
        assert nombre_eleccion in self.elecciones_candidatos, "[ERROR] La eleccion no existe."

    def _validar_candidato_en_eleccion(self, nombre_eleccion: arc4.String, candidato: arc4.String) -> arc4.UInt64:
        """Valida que el candidato esta en la eleccion y retorna su indice."""
        candidatos = self.elecciones_candidatos[nombre_eleccion].copy()

        indice_candidato = arc4.UInt64(0)
        for c in candidatos:
            if c == candidato:
                return indice_candidato
            indice_candidato = arc4.UInt64(indice_candidato.native + 1)

        assert False, "[ERROR] El candidato no pertenece a esta eleccion."

    def _validar_no_doble_voto_elecciones(self, propuesta: arc4.String, votante: arc4.Address) -> None:
        """Evita que una direccion vote dos veces en la misma eleccion."""
        clave = arc4.Tuple((propuesta, votante))
        assert clave not in self.elecciones_registros_votos, "[ERROR] Esta direccion ya ha votado en esta eleccion."
