from fastapi import APIRouter, Request, Query

from helper.hash.hash_helper import HashHelper

router = APIRouter()


@router.get("/hash", response_description="generate hash content")
async def generate_hash(content: str = Query(..., description="raw content")) -> str:
    return HashHelper.hash(content)


@router.get("/encrypt", response_description="generate encrypted content")
async def generate_encrypted(request: Request, content: str = Query(..., description="raw content")) -> str:
    crypto_helper = request.app.crypto_helper
    return crypto_helper.encrypt(content)


@router.get("/decrypt", response_description="generate decrypted content")
async def generate_decrypted(request: Request, content: str = Query(..., description="encrypted content")) -> str:
    crypto_helper = request.app.crypto_helper
    return crypto_helper.decrypt(content)
