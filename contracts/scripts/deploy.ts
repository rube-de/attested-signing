import { ethers } from "hardhat";
import { bech32 } from "bech32";

function decodeRoflAppId(roflAppId: string): Uint8Array {
  const decoded = bech32.decode(roflAppId);
  if (decoded.prefix !== "rofl") {
    throw new Error(`Expected 'rofl' prefix, got '${decoded.prefix}'`);
  }
  const raw = new Uint8Array(bech32.fromWords(decoded.words));
  if (raw.length !== 21) {
    throw new Error(`ROFL app ID must be 21 bytes, got ${raw.length}`);
  }
  return raw;
}

async function main() {
  const roflAppId = process.env.ROFL_APP_ID;
  if (!roflAppId) {
    throw new Error(
      "Set ROFL_APP_ID env var (bech32 format, e.g. rofl1qp5e5enxuf2ts...)\n" +
        "Get it from: oasis rofl show"
    );
  }

  const rawAppId = decodeRoflAppId(roflAppId);
  const bytes21Hex = "0x" + Buffer.from(rawAppId).toString("hex");
  console.log(`ROFL App ID (bech32):  ${roflAppId}`);
  console.log(`ROFL App ID (bytes21): ${bytes21Hex}`);

  const factory = await ethers.getContractFactory("AttestedSigner");
  const contract = await factory.deploy(rawAppId);
  await contract.waitForDeployment();

  const address = await contract.getAddress();
  console.log(`\nAttestedSigner deployed to: ${address}`);
  console.log(`\nSet this in your ROFL app environment:`);
  console.log(`  CONTRACT_ADDRESS=${address}`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
