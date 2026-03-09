"""ROFL TEE-attested signing service — fetches weather data, signs it, submits on-chain."""

import json
import logging
import os
import time

import httpx
from eth_account import Account
from eth_account.messages import encode_defunct
from oasis_rofl_client import RoflClient
from web3 import Web3

from .abi import ATTESTED_SIGNER_ABI

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

WEATHER_URL = (
    "https://api.open-meteo.com/v1/forecast"
    "?latitude=40.71&longitude=-74.01&current=temperature_2m,wind_speed_10m"
)


def main() -> None:
    contract_address = os.environ["CONTRACT_ADDRESS"]
    fetch_interval = int(os.environ.get("FETCH_INTERVAL", "60"))
    key_id = os.environ.get("KEY_ID", "attested-signer-v1")

    client = RoflClient()
    w3 = Web3()
    checksum_addr = Web3.to_checksum_address(contract_address)
    contract = w3.eth.contract(address=checksum_addr, abi=ATTESTED_SIGNER_ABI)

    # 1. Generate a persistent secp256k1 key inside the TEE
    log.info("Generating key in TEE (key_id=%s)...", key_id)
    private_key_hex = client.generate_key(key_id)
    acct = Account.from_key(f"0x{private_key_hex}")
    log.info("TEE-generated signer address: %s", acct.address)

    # 2. Register the signer on-chain (ROFL-authenticated)
    log.info("Registering signer on contract %s...", checksum_addr)
    register_data = contract.encode_abi("registerSigner", args=[acct.address])
    client.sign_submit(
        {"to": checksum_addr, "gas": 200_000, "value": 0, "data": register_data}
    )
    log.info("Signer registered on-chain")

    # 3. Loop: fetch → sign → submit
    while True:
        try:
            resp = httpx.get(WEATHER_URL, timeout=15)
            resp.raise_for_status()
            current = resp.json()["current"]

            data_str = json.dumps(
                {
                    "temperature_c": current["temperature_2m"],
                    "wind_speed_kmh": current["wind_speed_10m"],
                    "location": "New York",
                    "timestamp": int(time.time()),
                },
                separators=(",", ":"),
            )

            # Sign the hash of the data (matches contract's keccak256 + toEthSignedMessageHash)
            data_hash = Web3.keccak(text=data_str)
            message = encode_defunct(primitive=data_hash)
            sig = Account.sign_message(message, private_key=f"0x{private_key_hex}")

            # Submit signed data on-chain (ROFL-authenticated)
            submit_data = contract.encode_abi(
                "submitData", args=[data_str, bytes(sig.signature)]
            )
            client.sign_submit(
                {"to": checksum_addr, "gas": 300_000, "value": 0, "data": submit_data}
            )
            log.info("Submitted: %s", data_str)

        except Exception:
            log.exception("Error in fetch/sign/submit cycle")

        time.sleep(fetch_interval)


if __name__ == "__main__":
    main()
