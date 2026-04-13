"""
Paquet: anchoring
Descripcio: Capa d'ancoratge distribuit dels resultats electorals. Proporciona
            les eines necessaries perque cada node universitari pugui:
              1. Llegir l'estat electoral des d'Algorand (algorand_reader)
              2. Calcular el hash SHA-256 deterministic (hasher)
              3. Verificar el consens K-de-N entre nodes (consensus)
              4. Enviar el hash al contracte NotaryContract d'Ethereum (ethereum_submitter)
              5. Orquestrar tot el flux d'ancoratge (anchoring_service)

            Moduls:
              - models.py: Estructures de dades (ElectionState)
              - algorand_reader.py: Lectura i descodificacio ARC-4 del Box Storage
              - hasher.py: Hash SHA-256 deterministic amb JSON canonic
              - consensus.py: Logica de consens K-de-N
              - ethereum_submitter.py: Enviament de hashes a Ethereum via Web3.py
              - anchoring_service.py: Orquestrador del flux complet

Referencia: BLOCKCHAIN.pdf §7.3.3 (Gestor d'ancoratge), §9.7 (Verificabilitat)
"""
