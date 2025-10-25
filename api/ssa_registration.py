"""
SSA Registration - Регистрация клиентов по Software Statement
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
import httpx
import secrets

from ..database import get_db

router = APIRouter(tags=["ssa"])


class SSARegistrationRequest(BaseModel):
    """Запрос на регистрацию по SSA"""
    ssa_id: str


class SSARegistrationResponse(BaseModel):
    """Ответ при регистрации"""
    client_id: str
    client_secret: str
    message: str


@router.post("/register-client", response_model=SSARegistrationResponse)
async def register_client_by_ssa(
    request: SSARegistrationRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Регистрация клиента (TPP) по Software Statement Assertion
    
    Процесс:
    1. Получить SSA из Directory
    2. Проверить статус (active)
    3. Создать client credentials
    4. Сохранить в БД (опционально)
    5. Вернуть client_id и client_secret
    """
    # 1. Валидация SSA через Directory
    directory_url = "http://localhost:3000"  # TODO: из config
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"{directory_url}/ssa/{request.ssa_id}/validate"
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid SSA: {request.ssa_id}"
                )
            
            ssa_data = response.json()
            
    except httpx.RequestError:
        raise HTTPException(
            status_code=503,
            detail="Directory Service unavailable"
        )
    
    # 2. Проверить статус
    if ssa_data.get("status") != "active":
        raise HTTPException(
            status_code=400,
            detail=f"SSA status is {ssa_data.get('status')}, not active"
        )
    
    # 3. Сгенерировать client credentials
    client_id = f"tpp_{secrets.token_urlsafe(16)}"
    client_secret = f"secret_{secrets.token_urlsafe(32)}"
    
    # 4. TODO: Сохранить в БД банка (таблица registered_clients)
    # Пока просто возвращаем credentials
    
    return SSARegistrationResponse(
        client_id=client_id,
        client_secret=client_secret,
        message=f"Client registered successfully for {ssa_data['client_name']}"
    )

