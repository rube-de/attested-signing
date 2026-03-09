// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Subcall} from "@oasisprotocol/sapphire-contracts/contracts/Subcall.sol";
import {ECDSA} from "@openzeppelin/contracts/utils/cryptography/ECDSA.sol";
import {MessageHashUtils} from "@openzeppelin/contracts/utils/cryptography/MessageHashUtils.sol";

/// @title AttestedSigner — ROFL TEE-attested signing demo
/// @notice Stores data signed by a key generated inside a TEE.
///         Only the registered ROFL app can write; anyone can verify.
contract AttestedSigner {
    using ECDSA for bytes32;
    using MessageHashUtils for bytes32;

    bytes21 public roflAppID;
    address public attestedSigner;

    struct SignedData {
        string data;
        bytes signature;
        uint256 timestamp;
    }

    SignedData public latestData;

    event SignerRegistered(address indexed signer);
    event DataSubmitted(string data, address indexed signer, uint256 timestamp);

    constructor(bytes21 _roflAppID) {
        roflAppID = _roflAppID;
    }

    modifier onlyROFL() {
        Subcall.roflEnsureAuthorizedOrigin(roflAppID);
        _;
    }

    /// @notice Register the TEE-generated signer address (callable only by ROFL app)
    function registerSigner(address _signer) external onlyROFL {
        attestedSigner = _signer;
        emit SignerRegistered(_signer);
    }

    /// @notice Submit signed data from the TEE (callable only by ROFL app)
    function submitData(
        string calldata _data,
        bytes calldata _signature
    ) external onlyROFL {
        latestData = SignedData({
            data: _data,
            signature: _signature,
            timestamp: block.timestamp
        });
        emit DataSubmitted(_data, attestedSigner, block.timestamp);
    }

    /// @notice Verify that data was signed by the TEE-attested key (callable by anyone)
    function verifyData(
        string calldata _data,
        bytes calldata _signature
    ) external view returns (bool) {
        require(attestedSigner != address(0), "No signer registered");
        bytes32 ethHash = keccak256(bytes(_data)).toEthSignedMessageHash();
        address recovered = ethHash.recover(_signature);
        return recovered == attestedSigner;
    }

    function getLatestData()
        external
        view
        returns (string memory data, bytes memory signature, uint256 timestamp)
    {
        return (latestData.data, latestData.signature, latestData.timestamp);
    }
}
