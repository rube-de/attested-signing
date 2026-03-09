"""Minimal ABI for AttestedSigner contract — only functions called by the ROFL app."""

ATTESTED_SIGNER_ABI = [
    {
        "inputs": [{"internalType": "address", "name": "_signer", "type": "address"}],
        "name": "registerSigner",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "string", "name": "_data", "type": "string"},
            {"internalType": "bytes", "name": "_signature", "type": "bytes"},
        ],
        "name": "submitData",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
]
