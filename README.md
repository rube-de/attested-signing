# Attested Signing — ROFL Workshop Demo

A TEE-attested signing service built with [Oasis ROFL](https://docs.oasis.io/build/rofl/).

The ROFL app generates a key inside a TEE, fetches external data, signs it with that key,
and submits the signed data to a Sapphire smart contract. Anyone can verify the signature
came from a TEE-attested key — without trusting any individual or server.

## Architecture

```
┌─────────────────────────────────────┐
│  ROFL App (runs inside TEE)         │
│                                     │
│  ┌──────────────┐  ┌──────────────┐ │
│  │ Python app   │──│ appd sidecar │ │
│  │ (signer)     │  │ (keys, txs)  │ │
│  └──────┬───────┘  └──────┬───────┘ │
│         │ fetch            │ sign &  │
│         │ weather          │ submit  │
└─────────┼──────────────────┼────────┘
          │                  │
          ▼                  ▼
   open-meteo.com    ┌──────────────────┐
   (external API)    │ Sapphire Contract │
                     │ AttestedSigner    │
                     │                   │
                     │ • registerSigner()│ ← only ROFL app
                     │ • submitData()    │ ← only ROFL app
                     │ • verifyData()    │ ← anyone
                     └──────────────────┘
```

## What ROFL adds (vs pure Sapphire)

- **External HTTP calls** — fetches data from APIs (Sapphire contracts can't do this)
- **Continuous operation** — runs as a daemon, not just on-chain transactions
- **appd key management** — generates and holds keys in the TEE via a simple REST API
- **Docker Compose** — write your logic in Python/Node/Go, not Solidity

## Prerequisites

- [Oasis CLI](https://docs.oasis.io/general/manage-tokens/cli/setup)
- [Docker](https://docs.docker.com/get-docker/) (for ROFL builds)
- [Bun](https://bun.sh/) (for Hardhat)
- [Python](https://python.org/) 3.11+ and [uv](https://docs.astral.sh/uv/) (for local dev)
- Sapphire Testnet tokens from https://faucet.testnet.oasis.io

## Quick Start

### 1. Set up wallet and create the ROFL app

```bash
# 1. Create a new wallet in MetaMask and copy the private key
# 2. Fund it with Sapphire Testnet tokens from https://faucet.testnet.oasis.io
# 3. Import the private key into the Oasis CLI
oasis wallet import my_wallet --algorithm secp256k1-raw --secret <0xYOUR_PRIVATE_KEY>

# Create the ROFL app on-chain
oasis rofl create --network testnet --account my_wallet
# Note the ROFL App ID (rofl1q...)

# Get the hex representation for the contract
oasis rofl show --network testnet
```

### 2. Deploy the contract

```bash
cd contracts
cp .env.example .env
# Edit .env: add your PRIVATE_KEY and ROFL_APP_ID (bech32 format, rofl1q...)
bun install
bun run deploy:testnet
# Note the contract address
cd ..
```

### 3. Build and push the container image

```bash
cd ../app

# Build
docker build -t YOUR_DOCKERHUB_USER/attested-signing:0.1.0 --platform linux/amd64 .

# Push
docker push YOUR_DOCKERHUB_USER/attested-signing:0.1.0
```

Update `compose.yaml` with your image name.

### 4. Set secrets and deploy

```bash
# Set the contract address as an environment variable
echo -n "0xYOUR_CONTRACT_ADDRESS" | oasis rofl secret set CONTRACT_ADDRESS -

# Build and deploy the ROFL app
oasis rofl build
oasis rofl deploy
```

### 5. Verify it works

```bash
# Check ROFL app status
oasis rofl machine show

# Check logs
oasis rofl machine logs
```

On-chain, anyone can call `verifyData()` to confirm the signature came from the
TEE-attested key.

## Local development

```bash
cd app
uv sync
# The app expects the appd socket at /run/rofl-appd.sock
# For local testing, use sapphire-localnet:
# docker run -it -p8544-8548:8544-8548 -v .:/rofls ghcr.io/oasisprotocol/sapphire-localnet
```

## Project structure

```
attested-signing/
├── compose.yaml                    # ROFL container orchestration
├── app/                            # Python ROFL container
│   ├── pyproject.toml
│   ├── Dockerfile
│   └── src/attested_signing/
│       ├── main.py                 # App logic: keygen → fetch → sign → submit
│       └── abi.py                  # Minimal contract ABI
└── contracts/                      # Hardhat / Sapphire
    ├── contracts/AttestedSigner.sol
    ├── scripts/deploy.ts
    ├── hardhat.config.ts
    └── package.json
```

## Hackathon ideas

This demo is a starting point. Swap the weather API for:

- **ML inference** — run a model in the TEE, post attested predictions on-chain (Props)
- **Credential delegation** — hold API keys in the TEE, grant time-bounded access (Conditional Recall)
- **Order flow protection** — monitor mempool, sign protected orders (PROF)
- **Cross-chain signing** — generate keys for other chains, sign portable EIP-712 messages

## Resources

- [ROFL docs](https://docs.oasis.io/build/rofl/)
- [rofl-client Python SDK](https://github.com/oasisprotocol/oasis-sdk/tree/main/rofl-client/py)
- [Sapphire docs](https://docs.oasis.io/build/sapphire/)
- [Oasis Testnet faucet](https://faucet.testnet.oasis.io)
- [Liquefaction paper](https://arxiv.org/abs/2412.02634) — encumbered wallets on Sapphire
