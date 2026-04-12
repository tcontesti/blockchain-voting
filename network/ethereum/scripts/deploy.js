/**
 * Script de desplegament del NotaryContract.
 *
 * Ús:
 *   npx hardhat run scripts/deploy.js --network localhost
 *   npx hardhat run scripts/deploy.js --network sepolia
 *
 * Variables d'entorn opcionals:
 *   UNIVERSITY_ADDRESSES  - Adreces separades per coma (si no, usa 3 comptes de Hardhat)
 *   THRESHOLD_K           - Llindar K (per defecte: 2)
 */

const hre = require("hardhat");

async function main() {
  const signers = await hre.ethers.getSigners();

  // Determinar adreces de les universitats
  let universityAddresses;
  if (process.env.UNIVERSITY_ADDRESSES) {
    universityAddresses = process.env.UNIVERSITY_ADDRESSES.split(",").map(
      (a) => a.trim()
    );
  } else {
    // Per defecte: 3 primers comptes de Hardhat (per a testing)
    universityAddresses = signers.slice(0, 3).map((s) => s.address);
    console.log("Usant comptes de Hardhat per defecte com a universitats");
  }

  const thresholdK = parseInt(process.env.THRESHOLD_K || "2", 10);

  console.log(`Desplegant NotaryContract...`);
  console.log(`  Universitats (N=${universityAddresses.length}):`);
  universityAddresses.forEach((addr, i) =>
    console.log(`    [${i}] ${addr}`)
  );
  console.log(`  Llindar (K=${thresholdK})`);

  const NotaryContract = await hre.ethers.getContractFactory(
    "NotaryContract"
  );
  const notary = await NotaryContract.deploy(
    universityAddresses,
    thresholdK
  );
  await notary.waitForDeployment();

  const contractAddress = await notary.getAddress();
  console.log(`\nNotaryContract desplegat a: ${contractAddress}`);
  console.log(
    `Configura NOTARY_CONTRACT_ADDRESS=${contractAddress} al fitxer .env`
  );
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
