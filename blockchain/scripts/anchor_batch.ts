import fs from "fs";
import path from "path";
import { MerkleTree } from "merkletreejs";
import keccak256 from "keccak256";
import { ethers } from "hardhat";

function strip0x(s: string) {
  return s.startsWith("0x") ? s.slice(2) : s;
}

function isHex64(s: string) {
  const x = strip0x(s);
  return /^[0-9a-fA-F]{64}$/.test(x);
}

async function main() {
  const batchJson = process.env.BATCH_JSON;
  const contractAddress = process.env.CONTRACT_ADDRESS;
  const outJson = process.env.OUT_JSON;

  if (!batchJson) throw new Error("Missing env var BATCH_JSON (path to batch_unanchored.json)");
  if (!contractAddress) throw new Error("Missing env var CONTRACT_ADDRESS (deployed AuditAnchor address)");

  const batchPathAbs = path.resolve(batchJson);
  const raw = fs.readFileSync(batchPathAbs, "utf-8");
  const batch = JSON.parse(raw);

  const blocks: Array<{ id: number; block_index: number; current_hash: string }> = batch.blocks || [];
  if (!Array.isArray(blocks) || blocks.length === 0) {
    console.log("No blocks found in batch JSON. Nothing to anchor.");
    return;
  }

  // Leaves = keccak256(bytes(current_hash_hex))
  const leaves = blocks.map((b) => {
    const h = b.current_hash;
    if (!isHex64(h)) {
      // fallback: hash UTF-8 bytes if the value isn't a clean 64-hex digest
      return keccak256(Buffer.from(String(h), "utf8"));
    }
    return keccak256(Buffer.from(strip0x(h), "hex"));
  });

  const tree = new MerkleTree(leaves, keccak256, { sortPairs: true });
  const root = tree.getHexRoot();

  console.log("Local Merkle Root:", root);

  // Anchor on-chain
  const anchor = await ethers.getContractAt("AuditAnchor", contractAddress);
  const tx = await anchor.anchor(root);
  const receipt = await tx.wait();

  console.log("Root anchored on-chain");
  console.log("tx_hash:", receipt?.hash ?? tx.hash);

  // Build proofs for each leaf
  const results = blocks.map((b, i) => ({
    id: b.id,
    block_index: b.block_index,
    leaf_index: i,
    merkle_proof: tree.getHexProof(leaves[i]),
  }));

  const output = {
    network: "localhost-hardhat",
    contract_address: contractAddress,
    tx_hash: receipt?.hash ?? tx.hash,
    merkle_root: root,
    block_start: blocks[0].block_index,
    block_end: blocks[blocks.length - 1].block_index,
    count: blocks.length,
    blocks: results,
  };

  const defaultOut = path.resolve(path.dirname(batchPathAbs), "anchor_result.json");
  const outPathAbs = outJson ? path.resolve(outJson) : defaultOut;

  fs.writeFileSync(outPathAbs, JSON.stringify(output, null, 2), "utf-8");
  console.log("Wrote anchor result ->", outPathAbs);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
