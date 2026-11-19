import { MerkleTree } from "merkletreejs";
import keccak256 from "keccak256";
import { ethers } from "hardhat";

function envOn(name: string) {
  return process.env[name] === "1";
}

async function main() {
  const auditRecords = [
    "contract_001: risk=HIGH",
    "contract_002: risk=LOW",
    "contract_003: risk=MEDIUM",
  ];

  const leaves = auditRecords.map((r) => keccak256(r));
  const merkleTree = new MerkleTree(leaves, keccak256, { sortPairs: true });
  const localRoot = merkleTree.getHexRoot();

  console.log("Local Merkle Root:", localRoot);

  const anchor = await ethers.getContractAt(
    "AuditAnchor",
    "0x5FbDB2315678afecb367f032d93F642f64180aa3"
  );

  //  1) Anchor
  if (envOn("ANCHOR")) {
    const tx = await anchor.anchor(localRoot);
    await tx.wait();
    console.log(" Root anchored on-chain");
  }

  //  2) Freeze
  if (envOn("FREEZE")) {
    const tx = await anchor.freeze();
    await tx.wait();
    console.log(" Contract frozen (no more anchoring allowed)");
  }

  //  3) Verify (valid + tampered)
  if (envOn("VERIFY")) {
    const latestRoot = await anchor.getLatestRoot();
    console.log("On-chain Root (latest):", latestRoot);

    const targetAudit = auditRecords[1]; // contract_002
    const leaf = keccak256(targetAudit);
    const proof = merkleTree.getHexProof(leaf);

    console.log("Merkle Proof:", proof);

    const ok = merkleTree.verify(proof, leaf, latestRoot);
    if (ok) console.log(" Audit verified successfully");
    else console.log(" Audit verification FAILED (unexpected)");

    // Tamper test: modify content
    const tampered = "contract_002: risk=LOW_MEDIUM";
    const tamperedLeaf = keccak256(tampered);
    const ok2 = merkleTree.verify(proof, tamperedLeaf, latestRoot);

    if (!ok2) console.log(" Tampered audit FAILED verification (expected)");
    else console.log(" Tampered audit verified (BUG)");
  }

  //  4) Try anchoring AFTER freeze (must fail)
  if (envOn("POSTFREEZE_ANCHOR")) {
    try {
      const tx = await anchor.anchor(localRoot);
      await tx.wait();
      console.log(" Anchored after freeze (BUG) — should have failed");
    } catch (e: any) {
      console.log(" Anchoring blocked after freeze (expected)");
      // optional: console.log(e.message);
    }
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
