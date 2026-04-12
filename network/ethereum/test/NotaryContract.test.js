const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("NotaryContract", function () {
  let notary;
  let universities;
  let outsider;
  const THRESHOLD = 2;

  const ELECTION_ID = "Rector2026";
  const HASH_A = ethers.keccak256(ethers.toUtf8Bytes("resultA"));
  const HASH_B = ethers.keccak256(ethers.toUtf8Bytes("resultB"));

  beforeEach(async function () {
    const signers = await ethers.getSigners();
    universities = signers.slice(0, 3); // UIB, UPC, UAB
    outsider = signers[4];

    const NotaryContract = await ethers.getContractFactory("NotaryContract");
    notary = await NotaryContract.deploy(
      universities.map((u) => u.address),
      THRESHOLD
    );
    await notary.waitForDeployment();
  });

  describe("Desplegament", function () {
    it("configura correctament el llindar", async function () {
      expect(await notary.threshold()).to.equal(THRESHOLD);
    });

    it("registra totes les universitats a la whitelist", async function () {
      for (const uni of universities) {
        expect(await notary.isWhitelisted(uni.address)).to.be.true;
      }
      expect(await notary.getUniversityCount()).to.equal(3);
    });

    it("rebutja llindar zero", async function () {
      const NotaryContract = await ethers.getContractFactory("NotaryContract");
      await expect(
        NotaryContract.deploy([universities[0].address], 0)
      ).to.be.revertedWith("Llindar invalid: ha de ser 1 <= K <= N");
    });

    it("rebutja llindar superior a N", async function () {
      const NotaryContract = await ethers.getContractFactory("NotaryContract");
      await expect(
        NotaryContract.deploy([universities[0].address], 2)
      ).to.be.revertedWith("Llindar invalid: ha de ser 1 <= K <= N");
    });

    it("rebutja llista buida d'universitats", async function () {
      const NotaryContract = await ethers.getContractFactory("NotaryContract");
      await expect(NotaryContract.deploy([], 1)).to.be.revertedWith(
        "Cal almenys una universitat"
      );
    });

    it("rebutja adreces duplicades", async function () {
      const NotaryContract = await ethers.getContractFactory("NotaryContract");
      const addr = universities[0].address;
      await expect(NotaryContract.deploy([addr, addr], 1)).to.be.revertedWith(
        "Adreca duplicada"
      );
    });
  });

  describe("submitHash", function () {
    it("permet a una universitat enviar un hash", async function () {
      await expect(
        notary.connect(universities[0]).submitHash(ELECTION_ID, HASH_A)
      )
        .to.emit(notary, "HashSubmitted")
        .withArgs(ELECTION_ID, universities[0].address, HASH_A);

      const status = await notary.getElectionStatus(ELECTION_ID);
      expect(status.submissions).to.equal(1);
      expect(status.finalized).to.be.false;
    });

    it("rebutja enviament d'una adreca no autoritzada", async function () {
      await expect(
        notary.connect(outsider).submitHash(ELECTION_ID, HASH_A)
      ).to.be.revertedWith("No autoritzat: adreca fora de la whitelist");
    });

    it("rebutja doble enviament de la mateixa universitat", async function () {
      await notary.connect(universities[0]).submitHash(ELECTION_ID, HASH_A);
      await expect(
        notary.connect(universities[0]).submitHash(ELECTION_ID, HASH_A)
      ).to.be.revertedWith("Ja has enviat el hash per aquesta eleccio");
    });

    it("registra el hash correcte per cada universitat", async function () {
      await notary.connect(universities[0]).submitHash(ELECTION_ID, HASH_A);
      await notary.connect(universities[1]).submitHash(ELECTION_ID, HASH_B);

      expect(
        await notary.getSubmission(ELECTION_ID, universities[0].address)
      ).to.equal(HASH_A);
      expect(
        await notary.getSubmission(ELECTION_ID, universities[1].address)
      ).to.equal(HASH_B);
    });

    it("marca hasSubmitted correctament", async function () {
      expect(
        await notary.hasSubmitted(ELECTION_ID, universities[0].address)
      ).to.be.false;

      await notary.connect(universities[0]).submitHash(ELECTION_ID, HASH_A);

      expect(
        await notary.hasSubmitted(ELECTION_ID, universities[0].address)
      ).to.be.true;
    });
  });

  describe("Consens K-de-N", function () {
    it("finalitza quan K universitats envien el mateix hash", async function () {
      await notary.connect(universities[0]).submitHash(ELECTION_ID, HASH_A);

      await expect(
        notary.connect(universities[1]).submitHash(ELECTION_ID, HASH_A)
      ).to.emit(notary, "ElectionFinalized");

      const status = await notary.getElectionStatus(ELECTION_ID);
      expect(status.finalized).to.be.true;
      expect(status.officialHash).to.equal(HASH_A);
    });

    it("NO finalitza si els hashes no coincideixen", async function () {
      await notary.connect(universities[0]).submitHash(ELECTION_ID, HASH_A);
      await notary.connect(universities[1]).submitHash(ELECTION_ID, HASH_B);

      const status = await notary.getElectionStatus(ELECTION_ID);
      expect(status.finalized).to.be.false;
      expect(status.submissions).to.equal(2);
    });

    it("finalitza amb 2 iguals i 1 diferent (2-de-3)", async function () {
      await notary.connect(universities[0]).submitHash(ELECTION_ID, HASH_A);
      await notary.connect(universities[1]).submitHash(ELECTION_ID, HASH_B);

      // Tercera universitat envia HASH_A -> 2 coincidencies = K
      await expect(
        notary.connect(universities[2]).submitHash(ELECTION_ID, HASH_A)
      ).to.emit(notary, "ElectionFinalized");

      const status = await notary.getElectionStatus(ELECTION_ID);
      expect(status.finalized).to.be.true;
      expect(status.officialHash).to.equal(HASH_A);
      expect(status.submissions).to.equal(3);
    });

    it("rebutja enviaments despres de la finalitzacio", async function () {
      await notary.connect(universities[0]).submitHash(ELECTION_ID, HASH_A);
      await notary.connect(universities[1]).submitHash(ELECTION_ID, HASH_A);

      await expect(
        notary.connect(universities[2]).submitHash(ELECTION_ID, HASH_A)
      ).to.be.revertedWith("Eleccio ja finalitzada");
    });
  });

  describe("Eleccions independents", function () {
    it("gestiona multiples eleccions de forma independent", async function () {
      const ELECTION_2 = "Dega2026";
      const HASH_C = ethers.keccak256(ethers.toUtf8Bytes("resultC"));

      await notary.connect(universities[0]).submitHash(ELECTION_ID, HASH_A);
      await notary.connect(universities[0]).submitHash(ELECTION_2, HASH_C);

      const status1 = await notary.getElectionStatus(ELECTION_ID);
      const status2 = await notary.getElectionStatus(ELECTION_2);

      expect(status1.submissions).to.equal(1);
      expect(status2.submissions).to.equal(1);
      expect(status1.finalized).to.be.false;
      expect(status2.finalized).to.be.false;
    });
  });

  describe("Cas limit K=1", function () {
    it("finalitza immediatament amb un sol enviament", async function () {
      const NotaryContract = await ethers.getContractFactory("NotaryContract");
      const notaryK1 = await NotaryContract.deploy(
        universities.map((u) => u.address),
        1
      );
      await notaryK1.waitForDeployment();

      await expect(
        notaryK1.connect(universities[0]).submitHash(ELECTION_ID, HASH_A)
      ).to.emit(notaryK1, "ElectionFinalized");
    });
  });

  describe("Cas limit K=N", function () {
    it("requereix unanimitat per finalitzar", async function () {
      const NotaryContract = await ethers.getContractFactory("NotaryContract");
      const notaryKN = await NotaryContract.deploy(
        universities.map((u) => u.address),
        3
      );
      await notaryKN.waitForDeployment();

      await notaryKN
        .connect(universities[0])
        .submitHash(ELECTION_ID, HASH_A);
      await notaryKN
        .connect(universities[1])
        .submitHash(ELECTION_ID, HASH_A);

      let status = await notaryKN.getElectionStatus(ELECTION_ID);
      expect(status.finalized).to.be.false;

      await expect(
        notaryKN.connect(universities[2]).submitHash(ELECTION_ID, HASH_A)
      ).to.emit(notaryKN, "ElectionFinalized");

      status = await notaryKN.getElectionStatus(ELECTION_ID);
      expect(status.finalized).to.be.true;
    });
  });
});
