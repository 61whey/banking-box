"""
Banks API - Список банков
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from models import Bank

router = APIRouter(prefix="/banks", tags=["Banks"])


@router.get("", summary="Получить список банков")
async def get_banks(
    db: AsyncSession = Depends(get_db)
):
    """
    Получить список всех банков
    
    Возвращает код и название банка
    """
    result = await db.execute(select(Bank))
    banks = result.scalars().all()
    
    return {
        "data": {
            "bank": [
                {
                    "code": bank.code,
                    "name": bank.name
                }
                for bank in banks
            ]
        }
    }

