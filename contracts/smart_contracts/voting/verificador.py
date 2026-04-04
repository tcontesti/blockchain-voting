"""
Modul: verificador.py
Descripcio: Documentacio de les funcions de verificacio del Smart Contract.
            Totes les verificacions estan implementades com a metodes privats
            dins la classe SistemaVotacion a contract.py.
            Implementa el patro Guard (DT-02) desacoblat del router.
Estat: IMPLEMENTAT (integrat a contract.py)
Depend: constants.py (prefixos de BoxMap)
Referencia: Decisio tecnica DT-02 (Verificacio desacoblada via Guard)
Autor: Marc Link (@linkcla)

Verificadors implementats a contract.py:

  _verificar_censo(censo, votante)
      Verifica pertinenca al cens. O(1) via BoxMap.

  _verificar_inexistencia_usuario_censo(censo, votante)
      Verifica que l'adreca NO pertany al cens (evitar duplicats).

  _validar_propuesta(propuesta, existente)
      Valida existencia o inexistencia d'una proposta.

  _validar_propuesta_activa(propuesta)
      Comprova que la proposta te el cens completament carregat
      i que no s'ha convertit encara en eleccio.

  _validar_creador_propuesta(propuesta, creador)
      Comprova que qui crida es el creador de la proposta.
      Nomes el creador pot carregar el cens de la seva proposta.

  _validar_limite_censo_propuesta(cargados, total, longitud_lote)
      Evita carregar mes adreces que les declarades al crear la proposta.

  _validar_no_doble_voto_propuestas(propuesta, votante)
      Prevencio de doble vot en propostes. O(1) via BoxMap.

  _validar_existencia_votacion(nombre_eleccion)
      Verifica que l'eleccio existeix.

  _validar_candidato_en_eleccion(nombre_eleccion, candidato)
      Valida que el candidat pertany a l'eleccio.
      Retorna l'index del candidat dins el DynamicArray.

  _validar_no_doble_voto_elecciones(propuesta, votante)
      Prevencio de doble vot en eleccions. O(1) via BoxMap.
"""
