import hmac
import binascii
import json
import os
import subprocess
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models import Profile, Pending
from logging import getLogger

logger = getLogger("tpm_bootstrap")

def validate_tpm_quote(quote: str, nonce: str, aik_pub: str, expected_hash: str) -> bool:
    try:
        quote_bytes = bytes.fromhex(quote)
        aik_bytes = bytes.fromhex(aik_pub)
        logger.info(f"Validating TPM quote for nonce={nonce}...")
        return expected_hash in quote
    except binascii.Error:
        logger.error("Invalid hex encoding in TPM quote or AIK public key")
        return False

def validate_api_token(token: str, stored_token: str) -> bool:
    return hmac.compare_digest(token, stored_token)

async def get_profile_by_id(session: AsyncSession, identifier: str, profile_type: Optional[str] = None):
    query = select(Profile).where(Profile.id == identifier)
    if profile_type:
        query = query.where(Profile.type == profile_type)
    result = await session.execute(query)
    return result.scalars().first()

async def create_boot_iso(identifier: str, user_data: str, meta_data: str):
    os.makedirs(f"/tmp/seed/{identifier}", exist_ok=True)
    with open(f"/tmp/seed/{identifier}/user-data", "w") as f:
        f.write(user_data)
    with open(f"/tmp/seed/{identifier}/meta-data", "w") as f:
        f.write(meta_data)

    iso_path = f"/tmp/{identifier}-seed.iso"
    cmd = [
        "genisoimage",
        "-output", iso_path,
        "-volid", "cidata",
        "-joliet",
        "-rock",
        f"/tmp/seed/{identifier}/user-data",
        f"/tmp/seed/{identifier}/meta-data"
    ]

    try:
        subprocess.run(cmd, check=True)
        return iso_path
    except subprocess.CalledProcessError as e:
        logger.error(f"ISO creation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate ISO")

async def handle_bootstrap(bootstrap_data, mac, session: AsyncSession):
    if not mac:
        raise HTTPException(status_code=400, detail="Missing MAC address header")

    profile = None
    profile_type = ""

    # Handle TPM-based profiles
    if bootstrap_data.tpm:
        tpm_key = bootstrap_data.serial_number
        if not validate_tpm_quote(
            quote=bootstrap_data.tpm.quote,
            nonce=bootstrap_data.tpm.nonce,
            aik_pub=bootstrap_data.tpm.aik_pub,
            expected_hash=bootstrap_data.tpm.expected_hash
        ):
            raise HTTPException(status_code=403, detail="TPM attestation failed")

        profile = await get_profile_by_id(session, tpm_key, "tpm")
        profile_type = "tpm"
    else:
        # Handle MAC-based profiles
        profile = await get_profile_by_id(session, mac, "mac")
        profile_type = "mac"

    # If no profile is found, add to pending
    if not profile:
        pending_id = bootstrap_data.serial_number if bootstrap_data.tpm else mac
        pending = Pending(id=pending_id, data=json.dumps(bootstrap_data.dict()))
        session.add(pending)
        await session.commit()
        raise HTTPException(status_code=404, detail="Profile not registered, stored as pending.")

    # Validate API token if provided
    if profile.api_token and bootstrap_data.api_token:
        if not validate_api_token(bootstrap_data.api_token, profile.api_token):
            raise HTTPException(status_code=401, detail="Invalid API token")

    # Return the profile data
    return {"user-data": profile.user_data, "meta-data": profile.meta_data}