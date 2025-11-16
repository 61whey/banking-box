"""
Virtual Accounts API - Управление виртуальными счетами
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime
from decimal import Decimal

from database import get_db
from models import VirtualAccount, Client
from services.auth_service import get_current_client
from sqlalchemy import select
from services.virtual_account_service import (
    create_virtual_account,
    get_virtual_accounts_for_client,
    get_virtual_account_by_id,
    update_virtual_account,
    delete_virtual_account
)
from services.account_service import get_external_accounts_for_client
from log import logger


router = APIRouter(prefix="/virtual-accounts", tags=["Виртуальные счета"])


# === Pydantic Models ===

class VirtualAccountCreate(BaseModel):
    """Запрос на создание виртуального счета"""
    account_type: str = Field(..., description="Тип счета: checking, savings")
    calculation_type: str = Field(..., description="Тип расчета: automatic, fixed")
    balance: Optional[Decimal] = Field(None, description="Баланс (обязателен для fixed)")
    currency: str = Field(default="RUB", description="Валюта счета")

    class Config:
        json_schema_extra = {
            "example": {
                "account_type": "checking",
                "calculation_type": "automatic",
                "currency": "RUB"
            }
        }


class VirtualAccountUpdate(BaseModel):
    """Запрос на обновление виртуального счета"""
    account_type: Optional[str] = Field(None, description="Тип счета: checking, savings")
    calculation_type: Optional[str] = Field(None, description="Тип расчета: automatic, fixed")
    balance: Optional[Decimal] = Field(None, description="Баланс")
    currency: Optional[str] = Field(None, description="Валюта счета")
    status: Optional[str] = Field(None, description="Статус: active, inactive, closed")

    class Config:
        json_schema_extra = {
            "example": {
                "balance": "10000.00",
                "status": "active"
            }
        }


class VirtualAccountResponse(BaseModel):
    """Ответ с виртуальным счетом"""
    id: int
    client_id: int
    account_number: str
    account_type: str
    calculation_type: str
    balance: Decimal
    currency: str
    status: str
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class VirtualAccountListResponse(BaseModel):
    """Ответ со списком виртуальных счетов"""
    data: List[VirtualAccountResponse]
    count: int


class DeleteResponse(BaseModel):
    """Ответ при удалении"""
    message: str
    success: bool


# === Endpoints ===

@router.get("", response_model=VirtualAccountListResponse, summary="Получить виртуальные счета")
async def get_virtual_accounts(
    request: Request,
    current_client: dict = Depends(get_current_client),
    db: AsyncSession = Depends(get_db)
):
    """
    ## 📋 Получить все виртуальные счета клиента

    Возвращает список всех виртуальных счетов для аутентифицированного клиента.

    **Требуется авторизация:** JWT токен в заголовке Authorization
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

    logger.info(f"Fetching virtual accounts for client_id={client.id} (person_id={person_id})")

    try:
        accounts = await get_virtual_accounts_for_client(client.id, db)

        logger.info(f"Found {len(accounts)} virtual accounts for client_id={client.id}")

        # Fetch external accounts and calculate total balance for automatic accounts
        tokens = getattr(request.app.state, "tokens", {})
        external_accounts = await get_external_accounts_for_client(
            client_person_id=person_id,
            db=db,
            app_state_tokens=tokens
        )

        # Calculate total sum of all external account balances
        total_balance = Decimal("0")
        for acc_data in external_accounts:
            balance_str = acc_data.get("balance", "0")
            try:
                total_balance += Decimal(str(balance_str))
            except (ValueError, TypeError, Exception):
                logger.warning(f"Could not parse balance: {balance_str}")

        logger.info(f"Total external accounts balance: {total_balance}")

        # Calculate sum of balances from non-automatic virtual accounts
        other_accounts_balance = Decimal("0")
        for acc in accounts:
            if acc.calculation_type != "automatic":
                other_accounts_balance += acc.balance or Decimal("0")

        logger.info(f"Sum of other virtual accounts balances: {other_accounts_balance}")

        # Update balance for automatic calculation_type accounts
        # Balance = total external - sum of other virtual accounts
        automatic_balance = total_balance - other_accounts_balance
        for acc in accounts:
            if acc.calculation_type == "automatic":
                acc.balance = automatic_balance
                logger.debug(f"Updated automatic account {acc.account_number} balance to {automatic_balance}")

        return VirtualAccountListResponse(
            data=[VirtualAccountResponse.model_validate(acc) for acc in accounts],
            count=len(accounts)
        )

    except Exception as e:
        logger.error(f"Error fetching virtual accounts for client {client.id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{account_id}", response_model=VirtualAccountResponse, summary="Получить виртуальный счет")
async def get_virtual_account(
    account_id: int,
    current_client: dict = Depends(get_current_client),
    db: AsyncSession = Depends(get_db)
):
    """
    ## 🔍 Получить информацию о виртуальном счете

    Возвращает детальную информацию о виртуальном счете по ID.

    **Требуется авторизация:** JWT токен в заголовке Authorization

    **Параметры:**
    - `account_id`: ID виртуального счета
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

    logger.info(f"Fetching virtual account id={account_id} for client_id={client.id}")

    try:
        account = await get_virtual_account_by_id(account_id, client.id, db)

        if not account:
            logger.warning(f"Virtual account id={account_id} not found for client_id={client.id}")
            raise HTTPException(
                status_code=404,
                detail=f"Virtual account {account_id} not found"
            )

        logger.info(f"Retrieved virtual account {account.account_number} for client_id={client.id}")

        return VirtualAccountResponse.model_validate(account)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching virtual account {account_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("", response_model=VirtualAccountResponse, status_code=201, summary="Создать виртуальный счет")
async def create_virtual_account_endpoint(
    request: VirtualAccountCreate,
    current_client: dict = Depends(get_current_client),
    db: AsyncSession = Depends(get_db)
):
    """
    ## ✨ Создать новый виртуальный счет

    Создает новый виртуальный счет для клиента. Номер счета генерируется автоматически.

    **Требуется авторизация:** JWT токен в заголовке Authorization

    **Параметры:**
    - `account_type`: Тип счета (checking, savings)
    - `calculation_type`: Тип расчета баланса (automatic, fixed)
    - `balance`: Баланс счета (обязателен для calculation_type=fixed, игнорируется для automatic)
    - `currency`: Валюта счета (по умолчанию RUB)

    **Примеры:**

    1. Счет с автоматическим расчетом:
    ```json
    {
      "account_type": "checking",
      "calculation_type": "automatic",
      "currency": "RUB"
    }
    ```

    2. Счет с фиксированным балансом:
    ```json
    {
      "account_type": "savings",
      "calculation_type": "fixed",
      "balance": "10000.00",
      "currency": "RUB"
    }
    ```
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
        f"Creating virtual account for client {client.id} (person_id={person_id}): "
        f"type={request.account_type}, calc_type={request.calculation_type}, "
        f"balance={request.balance}, currency={request.currency}"
    )

    try:
        account = await create_virtual_account(
            client_id=client.id,
            account_type=request.account_type,
            calculation_type=request.calculation_type,
            balance=request.balance,
            currency=request.currency,
            db=db
        )

        logger.info(
            f"Virtual account {account.account_number} created successfully for client {client.id}"
        )

        return VirtualAccountResponse.model_validate(account)

    except ValueError as e:
        logger.warning(f"Validation error creating virtual account: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating virtual account for client {client.id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{account_id}", response_model=VirtualAccountResponse, summary="Обновить виртуальный счет")
async def update_virtual_account_endpoint(
    account_id: int,
    request: VirtualAccountUpdate,
    current_client: dict = Depends(get_current_client),
    db: AsyncSession = Depends(get_db)
):
    """
    ## ✏️ Обновить виртуальный счет

    Обновляет свойства существующего виртуального счета.

    **Требуется авторизация:** JWT токен в заголовке Authorization

    **Параметры:**
    - `account_id`: ID виртуального счета
    - `account_type`: Новый тип счета (optional)
    - `calculation_type`: Новый тип расчета (optional)
    - `balance`: Новый баланс (optional, только для fixed)
    - `currency`: Новая валюта (optional)
    - `status`: Новый статус (optional: active, inactive, closed)

    **Примечание:** При изменении calculation_type на 'automatic', баланс автоматически сбрасывается в 0.
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

    logger.info(f"Updating virtual account id={account_id} for client_id={client.id}")

    try:
        account = await update_virtual_account(
            account_id=account_id,
            client_id=client.id,
            account_type=request.account_type,
            calculation_type=request.calculation_type,
            balance=request.balance,
            currency=request.currency,
            status=request.status,
            db=db
        )

        if not account:
            logger.warning(f"Virtual account id={account_id} not found for client_id={client.id}")
            raise HTTPException(
                status_code=404,
                detail=f"Virtual account {account_id} not found"
            )

        logger.info(f"Virtual account {account.account_number} updated successfully")

        return VirtualAccountResponse.model_validate(account)

    except ValueError as e:
        logger.warning(f"Validation error updating virtual account {account_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating virtual account {account_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{account_id}", response_model=DeleteResponse, summary="Удалить виртуальный счет")
async def delete_virtual_account_endpoint(
    account_id: int,
    current_client: dict = Depends(get_current_client),
    db: AsyncSession = Depends(get_db)
):
    """
    ## 🗑️ Удалить виртуальный счет

    Удаляет виртуальный счет из базы данных.

    **Требуется авторизация:** JWT токен в заголовке Authorization

    **Параметры:**
    - `account_id`: ID виртуального счета
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

    logger.info(f"Deleting virtual account id={account_id} for client_id={client.id}")

    try:
        success = await delete_virtual_account(account_id, client.id, db)

        if not success:
            logger.warning(f"Virtual account id={account_id} not found for client_id={client.id}")
            raise HTTPException(
                status_code=404,
                detail=f"Virtual account {account_id} not found"
            )

        logger.info(f"Virtual account id={account_id} deleted successfully for client_id={client.id}")

        return DeleteResponse(
            message=f"Virtual account {account_id} deleted successfully",
            success=True
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting virtual account {account_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
