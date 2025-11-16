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


class TargetBankAmount(BaseModel):
    """Целевая сумма для банка"""
    bank_id: int
    bank_code: str
    bank_name: str
    target_share: Decimal
    target_amount: Optional[Decimal] = None
    accounts_count: int


class TargetAccountBalance(BaseModel):
    """Целевой баланс для счета"""
    bank_code: str
    bank_name: str
    account_id: str
    current_balance: Decimal
    target_balance: Decimal


class PaymentItem(BaseModel):
    """Элемент списка платежей"""
    source_account_id: str
    destination_account_id: str
    amount: Decimal
    source_bank: str
    source_bank_id: int
    destination_bank: str
    destination_bank_id: int


class ApplyAllocationsResponse(BaseModel):
    """Ответ при применении распределений"""
    success: bool
    message: str
    data: Optional[Dict] = None


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


async def validate_target_share_sum(
    db: AsyncSession,
    client_id: int,
    new_target_share: Decimal,
    external_accounts: List[Dict],
    exclude_allocation_id: Optional[int] = None,
    exclude_bank_id: Optional[int] = None
) -> tuple[bool, str, Decimal]:
    """
    Проверить, что сумма целевых долей не превышает 100%

    Args:
        db: Database session
        client_id: ID клиента
        new_target_share: Новая целевая доля для проверки
        external_accounts: Список внешних счетов клиента
        exclude_allocation_id: ID распределения для исключения (при обновлении)
        exclude_bank_id: ID банка для исключения (при создании)

    Returns:
        Tuple (is_valid, error_message, max_allowed_share)
    """
    # Получить коды банков, которые РЕАЛЬНО есть во внешних счетах (без ошибок)
    bank_codes_with_accounts = set()
    for acc_data in external_accounts:
        bank_code = acc_data.get("bank_code")
        account = acc_data.get("account")
        error = acc_data.get("error")

        # Учитывать только банки с реальными счетами (без ошибок)
        if bank_code and account is not None and not error:
            bank_codes_with_accounts.add(bank_code)

    logger.info(f"[validate_target_share_sum] external_accounts count: {len(external_accounts)}")
    logger.info(f"[validate_target_share_sum] external_accounts data: {external_accounts}")
    logger.info(f"[validate_target_share_sum] bank_codes_with_accounts: {bank_codes_with_accounts}")

    if not bank_codes_with_accounts:
        # Если нет внешних счетов, разрешаем установку target_share
        return True, "", Decimal("100")

    # Получить банки из базы
    banks_result = await db.execute(
        select(Bank).where(Bank.code.in_(bank_codes_with_accounts))
    )
    banks_dict = {bank.id: bank.code for bank in banks_result.scalars().all()}
    bank_ids_with_accounts = set(banks_dict.keys())

    logger.info(f"[validate_target_share_sum] bank_ids_with_accounts: {bank_ids_with_accounts}")

    # Получить все существующие распределения для клиента
    allocations_result = await db.execute(
        select(VirtualBalanceBankAllocation).where(
            VirtualBalanceBankAllocation.client_id == client_id
        )
    )
    allocations = allocations_result.scalars().all()

    # Подсчитать сколько банков будет иметь target_share после операции
    banks_with_target_after_operation = set()
    existing_sum = Decimal("0")

    for allocation in allocations:
        # Пропустить если это распределение мы обновляем
        if exclude_allocation_id and allocation.id == exclude_allocation_id:
            continue

        # Пропустить если это банк для которого создаем новое распределение
        if exclude_bank_id and allocation.bank_id == exclude_bank_id:
            continue

        # Учитывать только если банк есть во внешних счетах
        if allocation.bank_id in bank_ids_with_accounts:
            if allocation.target_share is not None:
                existing_sum += Decimal(str(allocation.target_share))
                banks_with_target_after_operation.add(allocation.bank_id)

    # Добавить текущий банк к списку банков с target_share
    if exclude_allocation_id:
        # При обновлении - найти bank_id обновляемого распределения
        for allocation in allocations:
            if allocation.id == exclude_allocation_id and allocation.bank_id in bank_ids_with_accounts:
                banks_with_target_after_operation.add(allocation.bank_id)
                break
    elif exclude_bank_id:
        # При создании - добавить новый банк
        if exclude_bank_id in bank_ids_with_accounts:
            banks_with_target_after_operation.add(exclude_bank_id)

    # Вычислить максимально допустимую долю
    max_allowed_share = Decimal("100") - existing_sum

    # Проверить, не превышает ли новая доля максимум
    total_sum = existing_sum + Decimal(str(new_target_share))

    if total_sum > Decimal("100"):
        error_msg = (
            f"Сумма всех целевых долей не должна превышать 100%. "
            f"Текущая сумма других банков: {existing_sum}%, "
            f"максимально допустимая доля для этого банка: {max_allowed_share}%"
        )
        return False, error_msg, max_allowed_share

    # Проверить: если ВСЕ банки будут иметь target_share, то сумма должна быть ровно 100%
    total_banks_count = len(bank_ids_with_accounts)
    banks_with_target_count = len(banks_with_target_after_operation)

    logger.info(
        f"[validate_target_share_sum] total_banks_count: {total_banks_count}, "
        f"banks_with_target_count: {banks_with_target_count}, "
        f"banks_with_target_after_operation: {banks_with_target_after_operation}, "
        f"total_sum: {total_sum}"
    )

    if banks_with_target_count == total_banks_count:
        # Все банки имеют target_share - сумма должна быть ровно 100%
        logger.info("[validate_target_share_sum] All banks have target_share, checking if sum == 100")
        if total_sum != Decimal("100"):
            error_msg = (
                f"Все банки должны иметь целевую долю в сумме равную 100%. "
                f"Текущая сумма: {total_sum}%. "
                f"Требуется распределить оставшиеся {Decimal('100') - total_sum}% между банками."
            )
            logger.warning(f"[validate_target_share_sum] Validation failed: {error_msg}")
            return False, error_msg, max_allowed_share
    else:
        logger.info(
            f"[validate_target_share_sum] Not all banks have target_share "
            f"({banks_with_target_count}/{total_banks_count}), allowing sum < 100%"
        )

    return True, "", max_allowed_share


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

        # Получить внешние счета для валидации
        tokens = getattr(request.app.state, "tokens", {})
        external_accounts = await get_external_accounts_for_client(
            client_person_id=person_id,
            db=db,
            app_state_tokens=tokens
        )

        # Проверить, что сумма target_share не превышает 100%
        is_valid, error_msg, max_allowed = await validate_target_share_sum(
            db=db,
            client_id=client.id,
            new_target_share=request_body.target_share,
            external_accounts=external_accounts,
            exclude_bank_id=request_body.bank_id
        )

        if not is_valid:
            logger.warning(f"Target share validation failed for client {client.id}: {error_msg}")
            raise HTTPException(status_code=400, detail=error_msg)

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

        # Использовать уже полученные external_accounts для ответа
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

        # Получить внешние счета для валидации
        tokens = getattr(request.app.state, "tokens", {})
        external_accounts = await get_external_accounts_for_client(
            client_person_id=person_id,
            db=db,
            app_state_tokens=tokens
        )

        # Проверить target_share если он обновляется
        if request_body.target_share is not None:
            # Проверить, что сумма target_share не превышает 100%
            is_valid, error_msg, max_allowed = await validate_target_share_sum(
                db=db,
                client_id=client.id,
                new_target_share=request_body.target_share,
                external_accounts=external_accounts,
                exclude_allocation_id=allocation_id
            )

            if not is_valid:
                logger.warning(f"Target share validation failed for allocation {allocation_id}: {error_msg}")
                raise HTTPException(status_code=400, detail=error_msg)

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

        # Использовать уже полученные external_accounts для ответа
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


@router.post("/apply", response_model=ApplyAllocationsResponse, summary="Применить распределение по банкам")
async def apply_balance_allocations(
    request: Request,
    current_client: dict = Depends(get_current_client),
    db: AsyncSession = Depends(get_db)
):
    """
    ## 🎯 Применить распределение средств по банкам

    Рассчитывает целевые балансы для счетов и формирует список платежей
    для достижения целевого распределения.

    **Требуется авторизация:** JWT токен в заголовке Authorization

    **Логика:**
    1. Получить актуальные данные внешних счетов
    2. Валидировать сумму target_share (не более 100%)
    3. Если все target_share заданы, проверить что сумма = 100%
    4. Рассчитать целевые суммы для каждого банка
    5. Рассчитать целевые балансы для каждого счета
    6. Сформировать список платежей для выравнивания
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

    logger.info(f"Applying balance allocations for client_id={client.id} (person_id={person_id})")

    try:
        # Step 1: Refresh external accounts data
        tokens = getattr(request.app.state, "tokens", {})
        external_accounts = await get_external_accounts_for_client(
            client_person_id=person_id,
            db=db,
            app_state_tokens=tokens
        )
        logger.info(f"[apply] Fetched {len(external_accounts)} external accounts")

        # Filter out accounts with errors
        valid_accounts = [
            acc for acc in external_accounts
            if acc.get("account") is not None and not acc.get("error")
        ]
        logger.info(f"[apply] Valid accounts (without errors): {len(valid_accounts)}")

        if not valid_accounts:
            return ApplyAllocationsResponse(
                success=True,
                message="Нет доступных внешних счетов для распределения",
                data=None
            )

        # Get unique bank_codes from valid accounts
        bank_codes = list(set(acc.get("bank_code") for acc in valid_accounts))
        logger.info(f"[apply] Unique bank codes: {bank_codes}")

        # Step 2: Check if there's only single unique bank_id
        if len(bank_codes) == 1:
            logger.info(f"[apply] Only one bank found ({bank_codes[0]}), nothing to do")
            return ApplyAllocationsResponse(
                success=True,
                message=f"Только один банк ({bank_codes[0]}). Распределение не требуется.",
                data=None
            )

        # Get banks from database
        banks_result = await db.execute(
            select(Bank).where(Bank.code.in_(bank_codes))
        )
        banks_dict = {bank.code: bank for bank in banks_result.scalars().all()}

        # Get existing allocations for client
        allocations_result = await db.execute(
            select(VirtualBalanceBankAllocation, Bank)
            .join(Bank, VirtualBalanceBankAllocation.bank_id == Bank.id)
            .where(VirtualBalanceBankAllocation.client_id == client.id)
        )
        allocations_by_bank_code = {}
        for allocation, bank in allocations_result.all():
            if bank.code in bank_codes:  # Only consider banks with accounts
                allocations_by_bank_code[bank.code] = allocation

        # Step 3: Collect target_shares for validation
        target_shares = {}
        empty_target_share_banks = []

        for bank_code in bank_codes:
            allocation = allocations_by_bank_code.get(bank_code)
            if allocation and allocation.target_share is not None:
                target_shares[bank_code] = Decimal(str(allocation.target_share))
            else:
                empty_target_share_banks.append(bank_code)

        logger.info(f"[apply] Target shares: {target_shares}")
        logger.info(f"[apply] Banks without target_share: {empty_target_share_banks}")

        # Step 4: Validate target_share sum
        total_target_share = sum(target_shares.values())
        logger.info(f"[apply] Total target_share sum: {total_target_share}")

        if total_target_share > Decimal("100"):
            error_msg = f"Сумма целевых долей ({total_target_share}%) превышает 100%"
            logger.error(f"[apply] {error_msg}")
            raise HTTPException(status_code=400, detail=error_msg)

        # Step 5: If all target_share values are non-empty, validate sum = 100
        if len(empty_target_share_banks) == 0:
            if total_target_share != Decimal("100"):
                error_msg = f"Все целевые доли заданы, но их сумма ({total_target_share}%) не равна 100%"
                logger.error(f"[apply] {error_msg}")
                raise HTTPException(status_code=400, detail=error_msg)

        # Step 6: Check that at most one target_share is empty
        if len(empty_target_share_banks) > 1:
            error_msg = f"Более одного банка без целевой доли: {', '.join(empty_target_share_banks)}. Задайте целевые доли для всех банков, кроме одного."
            logger.error(f"[apply] {error_msg}")
            raise HTTPException(status_code=400, detail=error_msg)

        # Step 7: Calculate total balance sum
        total_balance = Decimal("0")
        for acc in valid_accounts:
            balance_str = acc.get("balance", "0")
            try:
                balance = Decimal(str(balance_str)) if balance_str else Decimal("0")
            except (ValueError, TypeError):
                balance = Decimal("0")
            total_balance += balance
        logger.info(f"[apply] Total balance sum: {total_balance}")

        # Step 8: Build target_bank_amounts list
        target_bank_amounts = []

        # Count accounts per bank
        accounts_per_bank = {}
        for acc in valid_accounts:
            bank_code = acc.get("bank_code")
            if bank_code not in accounts_per_bank:
                accounts_per_bank[bank_code] = 0
            accounts_per_bank[bank_code] += 1

        # Fill in empty target_share with remainder
        if len(empty_target_share_banks) == 1:
            remaining_share = Decimal("100") - total_target_share
            target_shares[empty_target_share_banks[0]] = remaining_share
            logger.info(f"[apply] Auto-filled target_share for {empty_target_share_banks[0]}: {remaining_share}%")

        # Calculate target amounts
        calculated_sum = Decimal("0")
        bank_codes_sorted = sorted(bank_codes)  # Sort for consistency

        for i, bank_code in enumerate(bank_codes_sorted):
            bank = banks_dict.get(bank_code)
            if not bank:
                continue

            share = target_shares.get(bank_code, Decimal("0"))
            accounts_count = accounts_per_bank.get(bank_code, 0)

            if i < len(bank_codes_sorted) - 1:
                # Not the last bank - calculate normally
                target_amount = (total_balance * share / Decimal("100")).quantize(Decimal("0.01"))
                calculated_sum += target_amount
            else:
                # Last bank - use difference to avoid rounding errors
                target_amount = total_balance - calculated_sum

            target_bank_amounts.append({
                "bank_id": bank.id,
                "bank_code": bank_code,
                "bank_name": bank.name or bank_code,
                "target_share": float(share),
                "target_amount": float(target_amount),
                "accounts_count": accounts_count
            })

        logger.info(f"[apply] Target bank amounts: {target_bank_amounts}")

        # Step 9: Build target_account_balances list
        target_account_balances = []
        bank_target_amounts = {item["bank_code"]: Decimal(str(item["target_amount"])) for item in target_bank_amounts}
        bank_accounts_counts = {item["bank_code"]: item["accounts_count"] for item in target_bank_amounts}

        for acc in valid_accounts:
            bank_code = acc.get("bank_code")
            account = acc.get("account", {})
            account_id = account.get("accountId", "")
            balance_str = acc.get("balance", "0")

            try:
                current_balance = Decimal(str(balance_str)) if balance_str else Decimal("0")
            except (ValueError, TypeError):
                current_balance = Decimal("0")

            # Calculate target_balance = target_amount / accounts_count
            target_amount = bank_target_amounts.get(bank_code, Decimal("0"))
            accounts_count = bank_accounts_counts.get(bank_code, 1)
            target_balance = (target_amount / accounts_count).quantize(Decimal("0.01"))

            target_account_balances.append({
                "bank_code": bank_code,
                "bank_name": acc.get("bank_name", bank_code),
                "account_id": account_id,
                "current_balance": float(current_balance),
                "target_balance": float(target_balance)
            })

        logger.info(f"[apply] Target account balances: {target_account_balances}")

        # Step 10: Prepare payments_list
        payments_list = []

        # Create mapping from account_id to bank information
        account_to_bank = {}
        for acc_balance in target_account_balances:
            account_id = acc_balance["account_id"]
            bank_code = acc_balance["bank_code"]
            bank = banks_dict.get(bank_code)
            if bank:
                account_to_bank[account_id] = {
                    "bank_name": bank.name or bank_code,
                    "bank_id": bank.id
                }

        # Separate accounts into surplus (need to send) and deficit (need to receive)
        surplus_accounts = []
        deficit_accounts = []

        for acc_balance in target_account_balances:
            current = Decimal(str(acc_balance["current_balance"]))
            target = Decimal(str(acc_balance["target_balance"]))
            diff = current - target

            if diff > Decimal("0.01"):  # Has surplus
                surplus_accounts.append({
                    "account_id": acc_balance["account_id"],
                    "amount": diff
                })
            elif diff < Decimal("-0.01"):  # Has deficit
                deficit_accounts.append({
                    "account_id": acc_balance["account_id"],
                    "amount": -diff  # Convert to positive
                })

        # Match surplus with deficit accounts
        surplus_idx = 0
        deficit_idx = 0

        while surplus_idx < len(surplus_accounts) and deficit_idx < len(deficit_accounts):
            surplus = surplus_accounts[surplus_idx]
            deficit = deficit_accounts[deficit_idx]

            transfer_amount = min(surplus["amount"], deficit["amount"])

            if transfer_amount > Decimal("0.01"):
                source_bank_info = account_to_bank.get(surplus["account_id"], {"bank_name": "Unknown", "bank_id": 0})
                dest_bank_info = account_to_bank.get(deficit["account_id"], {"bank_name": "Unknown", "bank_id": 0})

                payments_list.append({
                    "source_account_id": surplus["account_id"],
                    "destination_account_id": deficit["account_id"],
                    "amount": float(transfer_amount.quantize(Decimal("0.01"))),
                    "source_bank": source_bank_info["bank_name"],
                    "source_bank_id": source_bank_info["bank_id"],
                    "destination_bank": dest_bank_info["bank_name"],
                    "destination_bank_id": dest_bank_info["bank_id"]
                })

            surplus["amount"] -= transfer_amount
            deficit["amount"] -= transfer_amount

            if surplus["amount"] <= Decimal("0.01"):
                surplus_idx += 1
            if deficit["amount"] <= Decimal("0.01"):
                deficit_idx += 1

        logger.info(f"[apply] Payments list (before filtering): {payments_list}")

        # Remove payments where source and destination are the same bank and account
        payments_list = [
            payment for payment in payments_list
            if not (
                payment["source_bank_id"] == payment["destination_bank_id"] and
                payment["source_account_id"] == payment["destination_account_id"]
            )
        ]

        logger.info(f"[apply] Payments list (after filtering): {payments_list}")

        return ApplyAllocationsResponse(
            success=True,
            message="Распределение рассчитано успешно",
            data={
                "external_accounts_count": len(valid_accounts),
                "total_balance": float(total_balance),
                "target_bank_amounts": target_bank_amounts,
                "target_account_balances": target_account_balances,
                "payments_list": payments_list
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error applying balance allocations for client {client.id}: {e}", exc_info=True)
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
