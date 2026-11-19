// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract AuditAnchor {
    event Anchored(
        uint256 indexed anchorId,
        bytes32 indexed merkleRoot,
        address indexed anchoredBy,
        uint256 timestamp
    );

    event Frozen(address indexed frozenBy, uint256 timestamp);

    address public owner;
    bool public frozen;

    uint256 public anchorCount;
    mapping(uint256 => bytes32) public anchors;

    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }

    modifier notFrozen() {
        require(!frozen, "Anchoring frozen");
        _;
    }

    constructor() {
        owner = msg.sender;
    }

    function anchor(bytes32 merkleRoot) external onlyOwner notFrozen {
        anchorCount += 1;
        anchors[anchorCount] = merkleRoot;

        emit Anchored(anchorCount, merkleRoot, msg.sender, block.timestamp);
    }

    function freeze() external onlyOwner notFrozen {
        frozen = true;
        emit Frozen(msg.sender, block.timestamp);
    }

    function getLatestRoot() external view returns (bytes32) {
        if (anchorCount == 0) return bytes32(0);
        return anchors[anchorCount];
    }

    function getAnchor(uint256 anchorId) external view returns (bytes32) {
        return anchors[anchorId];
    }
}
