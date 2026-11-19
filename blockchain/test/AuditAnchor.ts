
import { expect } from "chai";
import { ethers } from "hardhat";

describe("AuditAnchor", function () {
  async function deployAuditAnchor() {
    const [owner, otherAccount] = await ethers.getSigners();

    const factory = await ethers.getContractFactory("AuditAnchor");
    const contract = await factory.deploy();
    await contract.waitForDeployment();

    return { contract, owner, otherAccount };
  }

  it("Should assign ownership to the deployer", async function () {
    const { contract, owner } = await deployAuditAnchor();

    expect(await contract.owner()).to.equal(owner.address);
  });

  it("Should initially have no anchors", async function () {
    const { contract } = await deployAuditAnchor();

    expect(await contract.anchorCount()).to.equal(0n);
    expect(await contract.getLatestRoot()).to.equal(ethers.ZeroHash);
    expect(await contract.frozen()).to.equal(false);
  });

  it("Should allow the owner to anchor a Merkle root", async function () {
    const { contract } = await deployAuditAnchor();

    const root = ethers.keccak256(
      ethers.toUtf8Bytes("LegalView audit batch 1")
    );

    await expect(contract.anchor(root)).to.emit(contract, "Anchored");

    expect(await contract.anchorCount()).to.equal(1n);
    expect(await contract.getAnchor(1)).to.equal(root);
    expect(await contract.getLatestRoot()).to.equal(root);
  });

  it("Should store multiple roots with sequential IDs", async function () {
    const { contract } = await deployAuditAnchor();

    const root1 = ethers.keccak256(
      ethers.toUtf8Bytes("Batch 1")
    );
    const root2 = ethers.keccak256(
      ethers.toUtf8Bytes("Batch 2")
    );

    await contract.anchor(root1);
    await contract.anchor(root2);

    expect(await contract.anchorCount()).to.equal(2n);
    expect(await contract.getAnchor(1)).to.equal(root1);
    expect(await contract.getAnchor(2)).to.equal(root2);
    expect(await contract.getLatestRoot()).to.equal(root2);
  });

  it("Should reject anchoring by a non-owner", async function () {
    const { contract, otherAccount } = await deployAuditAnchor();

    const root = ethers.keccak256(
      ethers.toUtf8Bytes("Unauthorized batch")
    );

    await expect(
      contract.connect(otherAccount).anchor(root)
    ).to.be.revertedWith("Not owner");
  });

  it("Should allow the owner to freeze anchoring", async function () {
    const { contract } = await deployAuditAnchor();

    await expect(contract.freeze()).to.emit(contract, "Frozen");

    expect(await contract.frozen()).to.equal(true);
  });

  it("Should reject freezing by a non-owner", async function () {
    const { contract, otherAccount } = await deployAuditAnchor();

    await expect(
      contract.connect(otherAccount).freeze()
    ).to.be.revertedWith("Not owner");
  });

  it("Should reject anchoring after freezing", async function () {
    const { contract } = await deployAuditAnchor();

    const root = ethers.keccak256(
      ethers.toUtf8Bytes("Batch after freeze")
    );

    await contract.freeze();

    await expect(
      contract.anchor(root)
    ).to.be.revertedWith("Anchoring frozen");

    expect(await contract.anchorCount()).to.equal(0n);
  });

  it("Should reject freezing a second time", async function () {
    const { contract } = await deployAuditAnchor();

    await contract.freeze();

    await expect(
      contract.freeze()
    ).to.be.revertedWith("Anchoring frozen");
  });
});
