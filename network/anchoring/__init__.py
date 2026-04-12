"""
Paquet: anchoring
Descripcio: Capa de lectura i verificacio de l'estat electoral des de la
            blockchain Algorand. Proporciona les eines necessaries perque
            cada node universitari pugui llegir de forma independent els
            resultats d'una eleccio (candidats i recompte de vots) emmagatzemats
            al Box Storage del contracte SistemaVotacion, i calcular-ne un
            hash SHA-256 deterministic que serveix com a empremta digital
            verificable del resultat.

            Moduls:
              - models.py: Estructures de dades (ElectionState)
              - algorand_reader.py: Lectura i descodificacio ARC-4 del Box Storage
              - hasher.py: Hash SHA-256 deterministic amb JSON canonic

Referencia: BLOCKCHAIN.pdf §7.3.3 (Gestor d'ancoratge), §9.7 (Verificabilitat)
"""
