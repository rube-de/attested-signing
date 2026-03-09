import { ethers } from "hardhat";

async function main() {
  const contractAddress = process.env.CONTRACT_ADDRESS;
  if (!contractAddress) {
    throw new Error("Set CONTRACT_ADDRESS env var (0x...)");
  }

  const contract = await ethers.getContractAt("AttestedSigner", contractAddress);

  const attestedSigner = await contract.attestedSigner();
  console.log(`Attested signer: ${attestedSigner}`);

  if (attestedSigner === ethers.ZeroAddress) {
    console.log("\nNo signer registered yet — the ROFL app hasn't run.");
    return;
  }

  const [data, signature, timestamp] = await contract.getLatestData();

  if (!data) {
    console.log("\nNo data submitted yet.");
    return;
  }

  console.log(`\nLatest data:      ${data}`);
  console.log(`Timestamp:        ${new Date(Number(timestamp) * 1000).toISOString()}`);

  const isValid = await contract.verifyData(data, signature);
  console.log(`\nSignature valid:  ${isValid}`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
