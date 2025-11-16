"""
Balance Allocations API - Управление распределением средств по банкам
"""
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict
from datetime import datetime
from decimal import Decimal

from database import get_db
from models import VirtualBalanceBankAllocation, Client, Bank
from services.auth_service import get_current_client
from services.account_service import get_external_accounts_for_client
from services.cache_utils import client_key_builder, invalidate_client_cache
from sqlalchemy import select
from log import logger
from fastapi_cache.decorator import cache
from config import config
from redis import asyncio as aioredis


router = APIRouter(prefix="/balance-allocations", tags=["Распределение по банкам"])


# === Pydantic Models ===

class BalanceAllocationCreate(BaseModel):
    """Запрос на создание распределения"""
    bank_id: int = Field(..., description="ID банка")
    target_share: Decimal = Field(..., ge=0, le=100, description="Целевая доля в процентах (0-100)")
    account_type: str = Field(default="checking", description="Тип счета")

    class Config:
        json_schema_extra = {
            "example": {
                "bank_id": 1,
                "target_share": 25.50,
                "account_type": "checking"
            }
        }


class BalanceAllocationUpdate(BaseModel):
    """Запрос на обновление распределения"""
    target_share: Optional[Decimal] = Field(None, ge=0, le=100, description="Целевая доля в процентах (0-100)")
    account_type: Optional[str] = Field(None, description="Тип счета")

    class Config:
        json_schema_extra = {
            "example": {
                "target_share": 30.00
            }
        }


class BalanceAllocationResponse(BaseModel):
    """Ответ с информацией о распределении"""
    id: Optional[int] = None
    client_id: int
    bank_id: int
    bank_code: str
    bank_name: str
    target_share: Optional[Decimal] = None
    account_type: str
    actual_amount: Decimal
    actual_share: Decimal
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class BalanceAllocationListResponse(BaseModel):
    """Ответ со списком распределений"""
    data: List[BalanceAllocationResponse]
    count: int


class DeleteResponse(BaseModel):
    """Ответ при удалении"""
    message: str
    success: bool


# === Helper Functions ===

async def calculate_bank_balances(
    external_accounts: List[Dict],
    account_type: str = "checking"
) -> Dict[str, Decimal]:
    """
    Вычислить суммы по банкам из внешних счетов

    Args:
        external_accounts: Список счетов из внешних банков
        account_type: Тип счета для фильтрации

    Returns:
        Dict[bank_code, total_amount]
    """
    bank_balances = {}

    for acc_data in external_accounts:
        bank_code = acc_data.get("bank_code")
        account = acc_data.get("account")

        if not bank_code or not account:
            continue

        # Фильтр по типу счета если указан
        acc_type = account.get("accountSubType", "").lower()
        if account_type and acc_type != account_type.lower():
            continue

        # Получить баланс
        balance_str = acc_data.get("balance", "0")
        try:
            balance = Decimal(str(balance_str))
        except (ValueError, TypeError):
            logger.warning(f"Invalid balance for bank {bank_code}: {balance_str}")
            balance = Decimal("0")

        # Добавить к балансу банка
        if bank_code not in bank_balances:
            bank_balances[bank_code] = Decimal("0")
        bank_balances[bank_code] += balance

    return bank_balances


# === Endpoints ===

@router.get("", response_model=BalanceAllocationListResponse, summary="Получить распределения по банкам")
@cache(expire=config.CACHE_EXPIRE_SECONDS, key_builder=client_key_builder)
async def get_balance_allocations(
    request: Request,
    response: Response,
    current_client: dict = Depends(get_current_client),
    db: AsyncSession = Depends(get_db)
):
    """
    ## 📊 Получить распределение средств по банкам

    Возвращает список всех банков, в которых у клиента есть счета,
    с информацией о целевом и фактическом распределении средств.

    **Требуется авторизация:** JWT токен в заголовке Authorization

    **Возвращает:**
    - Список всех банков с счетами клиента
    - Для каждого банка: целевая доля (если установлена), фактическая доля и сумма
    - Даже если распределение не задано, банк отображается с target_share = null

    **Кэширование:**
    - Кэшируется на 5 минут (300 секунд) для каждого клиента
    - Заголовок X-FastAPI-Cache: HIT/MISS показывает, получен ли ответ из кэша
    - Кэш автоматически инвалидируется при создании, изменении или удалении распределений
    """
    person_id = current_client["client_id"]

    # Get client database ID from person_id
    result = await db.execute(
        select(Client).where(Client.person_id == person_id)
    )
    client = result.scalar_one_or_none()

    if not client:
        logger.warning(f"Client not found for person_id: {person_id}")
        raise HTTPException(status_code=404, detail="Client not found")

    logger.info(f"Fetching balance allocations for client_id={client.id} (person_id={person_id})")

    try:
        # Получить токены из app.state
        tokens = getattr(request.app.state, "tokens", {})

        # Получить счета из всех внешних банков (используем кэшированные данные)
        external_accounts = await get_external_accounts_for_client(
            client_person_id=person_id,
            db=db,
            app_state_tokens=tokens
        )

        logger.info(f"Fetched {len(external_accounts)} account responses from external banks")

        # Вычислить балансы по банкам
        bank_balances = await calculate_bank_balances(external_accounts, account_type="checking")

        # Вычислить общую сумму
        total_amount = sum(bank_balances.values())

        logger.info(f"Total balance across all banks: {total_amount}")

        # Получить все банки, в которых есть счета
        bank_codes_with_accounts = list(bank_balances.keys())

        if not bank_codes_with_accounts:
            logger.info(f"No banks with accounts found for client_id={client.id}")
            return BalanceAllocationListResponse(data=[], count=0)

        # Получить информацию о банках
        banks_result = await db.execute(
            select(Bank).where(Bank.code.in_(bank_codes_with_accounts))
        )
        banks = {bank.code: bank for bank in banks_result.scalars().all()}

        # Получить существующие распределения для клиента
        allocations_result = await db.execute(
            select(VirtualBalanceBankAllocation, Bank)
            .join(Bank, VirtualBalanceBankAllocation.bank_id == Bank.id)
            .where(VirtualBalanceBankAllocation.client_id == client.id)
        )

        # Создать словарь распределений по bank_id
        allocations_by_bank_code = {}
        for allocation, bank in allocations_result.all():
            allocations_by_bank_code[bank.code] = (allocation, bank)

        # Собрать результаты для всех банков
        result_data = []

        for bank_code in bank_codes_with_accounts:
            bank = banks.get(bank_code)
            if not bank:
                logger.warning(f"Bank not found for code: {bank_code}")
                continue

            actual_amount = bank_balances.get(bank_code, Decimal("0"))
            actual_share = (actual_amount / total_amount * 100) if total_amount > 0 else Decimal("0")

            # Проверить, есть ли распределение для этого банка
            allocation_data = allocations_by_bank_code.get(bank_code)

            if allocation_data:
                allocation, _ = allocation_data
                result_data.append(BalanceAllocationResponse(
                    id=allocation.id,
                    client_id=client.id,
                    bank_id=bank.id,
                    bank_code=bank.code,
                    bank_name=bank.name or bank.code,
                    target_share=allocation.target_share,
                    account_type=allocation.account_type or "checking",
                    actual_amount=actual_amount,
                    actual_share=round(actual_share, 2),
                    created_at=allocation.created_at,
                    updated_at=allocation.updated_at
                ))
            else:
                # Банк без целевого распределения
                result_data.append(BalanceAllocationResponse(
                    id=None,
                    client_id=client.id,
                    bank_id=bank.id,
                    bank_code=bank.code,
                    bank_name=bank.name or bank.code,
                    target_share=None,
                    account_type="checking",
                    actual_amount=actual_amount,
                    actual_share=round(actual_share, 2),
                    created_at=None,
                    updated_at=None
                ))

        logger.info(f"Returning {len(result_data)} balance allocations for client_id={client.id}")

        return BalanceAllocationListResponse(
            data=result_data,
            count=len(result_data)
        )

    except Exception as e:
        logger.error(f"Error fetching balance allocations for client {client.id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{allocation_id}", response_model=BalanceAllocationResponse, summary="Получить распределение")
async def get_balance_allocation(
    allocation_id: int,
    request: Request,
    current_client: dict = Depends(get_current_client),
    db: AsyncSession = Depends(get_db)
):
    """
    ## 🔍 Получить информацию о распределении

    Возвращает детальную информацию о распределении по ID.

    **Требуется авторизация:** JWT токен в заголовке Authorization

    **Параметры:**
    - `allocation_id`: ID распределения
    """
    person_id = current_client["client_id"]

    # Get client database ID from person_id
    result = await db.execute(
        select(Client).where(Client.person_id == person_id)
    )
    client = result.scalar_one_or_none()

    if not client:
        logger.warning(f"Client not found for person_id: {person_id}")
        raise HTTPException(status_code=404, detail="Client not found")

    logger.info(f"Fetching balance allocation id={allocation_id} for client_id={client.id}")

    try:
        # Получить распределение
        allocation_result = await db.execute(
            select(VirtualBalanceBankAllocation, Bank)
            .join(Bank, VirtualBalanceBankAllocation.bank_id == Bank.id)
            .where(
                VirtualBalanceBankAllocation.id == allocation_id,
                VirtualBalanceBankAllocation.client_id == client.id
            )
        )
        allocation_data = allocation_result.first()

        if not allocation_data:
            logger.warning(f"Balance allocation id={allocation_id} not found for client_id={client.id}")
            raise HTTPException(
                status_code=404,
                detail=f"Balance allocation {allocation_id} not found"
            )

        allocation, bank = allocation_data

        # Получить актуальные данные по счетам
        tokens = getattr(request.app.state, "tokens", {})
        external_accounts = await get_external_accounts_for_client(
            client_person_id=person_id,
            db=db,
            app_state_tokens=tokens
        )

        # Вычислить балансы
        bank_balances = await calculate_bank_balances(external_accounts, account_type=allocation.account_type or "checking")
        total_amount = sum(bank_balances.values())
        actual_amount = bank_balances.get(bank.code, Decimal("0"))
        actual_share = (actual_amount / total_amount * 100) if total_amount > 0 else Decimal("0")

        return BalanceAllocationResponse(
            id=allocation.id,
            client_id=client.id,
            bank_id=bank.id,
            bank_code=bank.code,
            bank_name=bank.name or bank.code,
            target_share=allocation.target_share,
            account_type=allocation.account_type or "checking",
            actual_amount=actual_amount,
            actual_share=round(actual_share, 2),
            created_at=allocation.created_at,
            updated_at=allocation.updated_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching balance allocation {allocation_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("", response_model=BalanceAllocationResponse, status_code=201, summary="Создать распределение")
async def create_balance_allocation(
    request_body: BalanceAllocationCreate,
    request: Request,
    current_client: dict = Depends(get_current_client),
    db: AsyncSession = Depends(get_db)
):
    """
    ## ✨ Создать новое распределение

    Создает целевое распределение средств для банка.

    **Требуется авторизация:** JWT токен в заголовке Authorization

    **Параметры:**
    - `bank_id`: ID банка
    - `target_share`: Целевая доля в процентах (0-100)
    - `account_type`: Тип счета (по умолчанию "checking")

    **Примечание:** Комбинация (client_id, bank_id, account_type) должна быть уникальной
    """
    person_id = current_client["client_id"]

    # Get client database ID from person_id
    result = await db.execute(
        select(Client).where(Client.person_id == person_id)
    )
    client = result.scalar_one_or_none()

    if not client:
        logger.warning(f"Client not found for person_id: {person_id}")
        raise HTTPException(status_code=404, detail="Client not found")

    logger.info(
        f"Creating balance allocation for client {client.id}: "
        f"bank_id={request_body.bank_id}, target_share={request_body.target_share}, "
        f"account_type={request_body.account_type}"
    )

    try:
        # Проверить, что банк существует
        bank_result = await db.execute(
            select(Bank).where(Bank.id == request_body.bank_id)
        )
        bank = bank_result.scalar_one_or_none()

        if not bank:
            raise HTTPException(status_code=404, detail=f"Bank {request_body.bank_id} not found")

        # Проверить, что такое распределение еще не существует
        existing_result = await db.execute(
            select(VirtualBalanceBankAllocation).where(
                VirtualBalanceBankAllocation.client_id == client.id,
                VirtualBalanceBankAllocation.bank_id == request_body.bank_id,
                VirtualBalanceBankAllocation.account_type == request_body.account_type
            )
        )
        existing = existing_result.scalar_one_or_none()

        if existing:
            raise HTTPException(
                status_code=400,
                detail="Balance allocation for this bank and account type already exists"
            )

        # Создать распределение
        allocation = VirtualBalanceBankAllocation(
            client_id=client.id,
            bank_id=request_body.bank_id,
            target_share=request_body.target_share,
            account_type=request_body.account_type
        )

        db.add(allocation)
        await db.commit()
        await db.refresh(allocation)

        logger.info(f"Balance allocation created successfully: id={allocation.id}")

        # Invalidate cache for this client
        redis_client = None
        try:
            redis_client = await aioredis.from_url(
                config.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            deleted_keys = await invalidate_client_cache(redis_client, person_id)
            logger.info(f"Cache invalidated for client_id={person_id}, deleted {deleted_keys} keys")
        except Exception as cache_error:
            logger.warning(f"Failed to invalidate cache: {cache_error}")
        finally:
            if redis_client:
                await redis_client.close()

        # Получить актуальные данные для ответа
        tokens = getattr(request.app.state, "tokens", {})
        external_accounts = await get_external_accounts_for_client(
            client_person_id=person_id,
            db=db,
            app_state_tokens=tokens
        )

        bank_balances = await calculate_bank_balances(external_accounts, account_type=request_body.account_type)
        total_amount = sum(bank_balances.values())
        actual_amount = bank_balances.get(bank.code, Decimal("0"))
        actual_share = (actual_amount / total_amount * 100) if total_amount > 0 else Decimal("0")

        return BalanceAllocationResponse(
            id=allocation.id,
            client_id=client.id,
            bank_id=bank.id,
            bank_code=bank.code,
            bank_name=bank.name or bank.code,
            target_share=allocation.target_share,
            account_type=allocation.account_type,
            actual_amount=actual_amount,
            actual_share=round(actual_share, 2),
            created_at=allocation.created_at,
            updated_at=allocation.updated_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating balance allocation: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{allocation_id}", response_model=BalanceAllocationResponse, summary="Обновить распределение")
async def update_balance_allocation(
    allocation_id: int,
    request_body: BalanceAllocationUpdate,
    request: Request,
    current_client: dict = Depends(get_current_client),
    db: AsyncSession = Depends(get_db)
):
    """
    ## ✏️ Обновить распределение

    Обновляет целевое распределение средств.

    **Требуется авторизация:** JWT токен в заголовке Authorization

    **Параметры:**
    - `allocation_id`: ID распределения
    - `target_share`: Новая целевая доля (optional)
    - `account_type`: Новый тип счета (optional)
    """
    person_id = current_client["client_id"]

    # Get client database ID from person_id
    result = await db.execute(
        select(Client).where(Client.person_id == person_id)
    )
    client = result.scalar_one_or_none()

    if not client:
        logger.warning(f"Client not found for person_id: {person_id}")
        raise HTTPException(status_code=404, detail="Client not found")

    logger.info(f"Updating balance allocation id={allocation_id} for client_id={client.id}")

    try:
        # Получить распределение
        allocation_result = await db.execute(
            select(VirtualBalanceBankAllocation, Bank)
            .join(Bank, VirtualBalanceBankAllocation.bank_id == Bank.id)
            .where(
                VirtualBalanceBankAllocation.id == allocation_id,
                VirtualBalanceBankAllocation.client_id == client.id
            )
        )
        allocation_data = allocation_result.first()

        if not allocation_data:
            logger.warning(f"Balance allocation id={allocation_id} not found for client_id={client.id}")
            raise HTTPException(
                status_code=404,
                detail=f"Balance allocation {allocation_id} not found"
            )

        allocation, bank = allocation_data

        # Обновить поля
        if request_body.target_share is not None:
            allocation.target_share = request_body.target_share

        if request_body.account_type is not None:
            allocation.account_type = request_body.account_type

        allocation.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(allocation)

        logger.info(f"Balance allocation {allocation.id} updated successfully")

        # Invalidate cache for this client
        redis_client = None
        try:
            redis_client = await aioredis.from_url(
                config.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            deleted_keys = await invalidate_client_cache(redis_client, person_id)
            logger.info(f"Cache invalidated for client_id={person_id}, deleted {deleted_keys} keys")
        except Exception as cache_error:
            logger.warning(f"Failed to invalidate cache: {cache_error}")
        finally:
            if redis_client:
                await redis_client.close()

        # Получить актуальные данные для ответа
        tokens = getattr(request.app.state, "tokens", {})
        external_accounts = await get_external_accounts_for_client(
            client_person_id=person_id,
            db=db,
            app_state_tokens=tokens
        )

        bank_balances = await calculate_bank_balances(external_accounts, account_type=allocation.account_type or "checking")
        total_amount = sum(bank_balances.values())
        actual_amount = bank_balances.get(bank.code, Decimal("0"))
        actual_share = (actual_amount / total_amount * 100) if total_amount > 0 else Decimal("0")

        return BalanceAllocationResponse(
            id=allocation.id,
            client_id=client.id,
            bank_id=bank.id,
            bank_code=bank.code,
            bank_name=bank.name or bank.code,
            target_share=allocation.target_share,
            account_type=allocation.account_type,
            actual_amount=actual_amount,
            actual_share=round(actual_share, 2),
            created_at=allocation.created_at,
            updated_at=allocation.updated_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating balance allocation {allocation_id}: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/refresh", summary="Обновить кэш распределений по банкам", include_in_schema=False)
async def refresh_balance_allocations(
    current_client: dict = Depends(get_current_client),
):
    """
    Инвалидировать кэш распределений по банкам для текущего клиента

    После вызова этого endpoint следующий запрос к /balance-allocations
    получит свежие данные.
    """
    if not current_client:
        logger.warning("Unauthorized request to refresh_balance_allocations")
        raise HTTPException(401, "Unauthorized")

    person_id = current_client["client_id"]
    logger.info(f"Invalidating cache for balance allocations, client_id={person_id}")

    redis_client = None
    try:
        # Create Redis connection
        redis_client = await aioredis.from_url(
            config.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )

        # Invalidate cache for this client
        deleted_keys = await invalidate_client_cache(redis_client, person_id)

        logger.info(f"Cache invalidated for client_id={person_id}, deleted {deleted_keys} keys")

        return {
            "data": {
                "message": "Cache invalidated successfully",
                "client_id": person_id,
                "deleted_keys": deleted_keys
            },
            "meta": {
                "message": "Кэш успешно обновлен"
            }
        }
    except Exception as e:
        logger.error(f"Error invalidating cache for client_id={person_id}: {e}", exc_info=True)
        raise HTTPException(500, f"Error invalidating cache: {str(e)}")
    finally:
        # Close Redis connection if it was created
        if redis_client:
            try:
                await redis_client.close()
            except Exception as close_error:
                logger.warning(f"Error closing Redis connection: {close_error}")


@router.delete("/{allocation_id}", response_model=DeleteResponse, summary="Удалить распределение")
async def delete_balance_allocation(
    allocation_id: int,
    current_client: dict = Depends(get_current_client),
    db: AsyncSession = Depends(get_db)
):
    """
    ## 🗑️ Удалить распределение

    Удаляет целевое распределение из базы данных.

    **Требуется авторизация:** JWT токен в заголовке Authorization

    **Параметры:**
    - `allocation_id`: ID распределения
    """
    person_id = current_client["client_id"]

    # Get client database ID from person_id
    result = await db.execute(
        select(Client).where(Client.person_id == person_id)
    )
    client = result.scalar_one_or_none()

    if not client:
        logger.warning(f"Client not found for person_id: {person_id}")
        raise HTTPException(status_code=404, detail="Client not found")

    logger.info(f"Deleting balance allocation id={allocation_id} for client_id={client.id}")

    try:
        # Получить распределение
        allocation_result = await db.execute(
            select(VirtualBalanceBankAllocation).where(
                VirtualBalanceBankAllocation.id == allocation_id,
                VirtualBalanceBankAllocation.client_id == client.id
            )
        )
        allocation = allocation_result.scalar_one_or_none()

        if not allocation:
            logger.warning(f"Balance allocation id={allocation_id} not found for client_id={client.id}")
            raise HTTPException(
                status_code=404,
                detail=f"Balance allocation {allocation_id} not found"
            )

        await db.delete(allocation)
        await db.commit()

        logger.info(f"Balance allocation id={allocation_id} deleted successfully for client_id={client.id}")

        # Invalidate cache for this client
        redis_client = None
        try:
            redis_client = await aioredis.from_url(
                config.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            deleted_keys = await invalidate_client_cache(redis_client, person_id)
            logger.info(f"Cache invalidated for client_id={person_id}, deleted {deleted_keys} keys")
        except Exception as cache_error:
            logger.warning(f"Failed to invalidate cache: {cache_error}")
        finally:
            if redis_client:
                await redis_client.close()

        return DeleteResponse(
            message=f"Balance allocation {allocation_id} deleted successfully",
            success=True
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting balance allocation {allocation_id}: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")
