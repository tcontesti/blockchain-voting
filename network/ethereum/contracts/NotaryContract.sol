// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/**
 * @title NotaryContract
 * @notice Contracte intel·ligent d'ancoratge distribuït K-de-N.
 *         Cada universitat envia el hash SHA-256 de l'estat final
 *         d'una elecció d'Algorand. Quan K universitats coincideixen
 *         en el mateix hash, el contracte l'ancora com a resultat oficial.
 * @dev Desplegat a Ethereum (Sepolia Testnet o Hardhat local).
 *      Referencia: BLOCKCHAIN.pdf §7.3.3, §9.7
 */
contract NotaryContract {
    uint256 public immutable threshold;
    address[] public universityList;
    mapping(address => bool) public isWhitelisted;

    struct ElectionRecord {
        bytes32 officialHash;
        bool finalized;
        uint256 submissionCount;
        mapping(address => bytes32) submissions;
        mapping(address => bool) hasSubmitted;
    }

    mapping(string => ElectionRecord) private elections;

    event HashSubmitted(
        string indexed electionId,
        address indexed university,
        bytes32 hash
    );

    event ElectionFinalized(
        string indexed electionId,
        bytes32 officialHash,
        uint256 confirmations
    );

    modifier onlyWhitelisted() {
        require(isWhitelisted[msg.sender], "No autoritzat: adreca fora de la whitelist");
        _;
    }

    /**
     * @param _universities Llista d'adreces de les universitats autoritzades (N)
     * @param _threshold Nombre minim d'acords necessaris (K)
     */
    constructor(address[] memory _universities, uint256 _threshold) {
        require(_universities.length > 0, "Cal almenys una universitat");
        require(
            _threshold > 0 && _threshold <= _universities.length,
            "Llindar invalid: ha de ser 1 <= K <= N"
        );

        threshold = _threshold;

        for (uint256 i = 0; i < _universities.length; i++) {
            address uni = _universities[i];
            require(uni != address(0), "Adreca zero no permesa");
            require(!isWhitelisted[uni], "Adreca duplicada");
            isWhitelisted[uni] = true;
            universityList.push(uni);
        }
    }

    /**
     * @notice Envia el hash de l'estat final d'una eleccio.
     *         Si K universitats envien el mateix hash, l'eleccio es finalitza.
     * @param electionId Identificador de l'eleccio (nom de la proposta)
     * @param hash Hash SHA-256 de l'estat canonic de l'eleccio
     */
    function submitHash(
        string calldata electionId,
        bytes32 hash
    ) external onlyWhitelisted {
        ElectionRecord storage record = elections[electionId];
        require(!record.finalized, "Eleccio ja finalitzada");
        require(!record.hasSubmitted[msg.sender], "Ja has enviat el hash per aquesta eleccio");

        record.submissions[msg.sender] = hash;
        record.hasSubmitted[msg.sender] = true;
        record.submissionCount++;

        emit HashSubmitted(electionId, msg.sender, hash);

        // Comptar quantes universitats han enviat el MATEIX hash
        uint256 matchCount = 0;
        for (uint256 i = 0; i < universityList.length; i++) {
            if (
                record.hasSubmitted[universityList[i]] &&
                record.submissions[universityList[i]] == hash
            ) {
                matchCount++;
            }
        }

        if (matchCount >= threshold) {
            record.finalized = true;
            record.officialHash = hash;
            emit ElectionFinalized(electionId, hash, matchCount);
        }
    }

    /**
     * @notice Consulta l'estat d'ancoratge d'una eleccio.
     */
    function getElectionStatus(
        string calldata electionId
    )
        external
        view
        returns (bool finalized, bytes32 officialHash, uint256 submissions)
    {
        ElectionRecord storage r = elections[electionId];
        return (r.finalized, r.officialHash, r.submissionCount);
    }

    /**
     * @notice Consulta el hash enviat per una universitat concreta.
     */
    function getSubmission(
        string calldata electionId,
        address university
    ) external view returns (bytes32) {
        return elections[electionId].submissions[university];
    }

    /**
     * @notice Comprova si una universitat ja ha enviat hash per una eleccio.
     */
    function hasSubmitted(
        string calldata electionId,
        address university
    ) external view returns (bool) {
        return elections[electionId].hasSubmitted[university];
    }

    /**
     * @notice Retorna el nombre total d'universitats autoritzades (N).
     */
    function getUniversityCount() external view returns (uint256) {
        return universityList.length;
    }
}
