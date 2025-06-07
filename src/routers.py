from fastapi import APIRouter, Depends, HTTPException, Request, Header
from fastapi.responses import JSONResponse, PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession
from controllers import handle_bootstrap, create_boot_iso, get_profile_by_id
from models import BootstrapRequest
from dependencies import get_session

router = APIRouter()

@router.post("/bootstrap")
async def bootstrap(
    request: Request,
    bootstrap_data: BootstrapRequest,
    x_mac_address: str = Header(None),
    session: AsyncSession = Depends(get_session)
):
    profile_data = await handle_bootstrap(bootstrap_data, x_mac_address, session)
    return JSONResponse(content={"message": "Provisioning profile accepted.", "profile": profile_data})

@router.get("/seed/{identifier}/meta-data")
async def seed_meta_data(identifier: str, session: AsyncSession = Depends(get_session)):
    profile = await get_profile_by_id(session, identifier)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return PlainTextResponse(profile.meta_data)

@router.get("/cloud-config/{identifier}")
async def cloud_config(identifier: str, session: AsyncSession = Depends(get_session)):
    profile = await get_profile_by_id(session, identifier)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return PlainTextResponse(profile.user_data)

@router.post("/create-boot-iso")
async def create_iso(identifier: str, session: AsyncSession = Depends(get_session)):
    profile = await get_profile_by_id(session, identifier)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    iso_path = await create_boot_iso(identifier, profile.user_data, profile.meta_data)
    return {"status": "ISO created", "path": iso_path}