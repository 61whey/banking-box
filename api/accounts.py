"""
Accounts API - Получение информации о счетах клиента
OpenBanking Russia v2.1 compatible
"""
from fastapi import APIRouter, Depends, HTTPException, Header, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from datetime import datetime
from pydantic import BaseModel
from decimal import Decimal
import uuid

from database import get_db
from models import Account, Client, Transaction, BankCapital
from services.auth_service import get_current_client, get_optional_client
from services.consent_service import ConsentService
from services.account_service import get_external_accounts_for_client
from services.cache_utils import client_key_builder, invalidate_client_cache
from fastapi import Request
from log import logger
from fastapi_cache.decorator import cache
from config import config
from redis import asyncio as aioredis


router = APIRouter(prefix="/accounts", tags=["2 Счета и балансы"])


@router.get("", summary="Получить счета")
async def get_accounts(
    client_id: Optional[str] = None,
    x_consent_id: Optional[str] = Header(None, alias="x-consent-id"),
    x_requesting_bank: Optional[str] = Header(None, alias="x-requesting-bank"),
    current_client: Optional[dict] = Depends(get_optional_client),
    db: AsyncSession = Depends(get_db)
):
    """
    Получение списка счетов
    
    Для собственного клиента: используется JWT токен
    Для межбанковского запроса: требуется consent_id и bank token
    """
    
    # Определяем, чей это запрос
    if x_requesting_bank:
        # Межбанковский запрос - требуется согласие
        if not client_id:
            raise HTTPException(400, "client_id required for interbank requests")
        
        # Проверить согласие
        consent = await ConsentService.check_consent(
            db=db,
            client_person_id=client_id,
            requesting_bank=x_requesting_bank,
            permissions=["ReadAccountsDetail"]
        )
        
        if not consent:
            raise HTTPException(
                403,
                detail={
                    "error": "CONSENT_REQUIRED",
                    "message": "Требуется согласие клиента",
                    "consent_request_url": "/account-consents/request"
                }
            )
        
        target_client_id = client_id
        
    else:
        # Запрос собственного клиента
        if not current_client:
            raise HTTPException(401, "Unauthorized")
        target_client_id = current_client["client_id"]
    
    # Получаем клиента для имени
    client_result = await db.execute(
        select(Client).where(Client.person_id == target_client_id)
    )
    client = client_result.scalar_one_or_none()
    
    if not client:
        logger.warning(f"Client not found for person_id: {target_client_id}")
        return {
            "data": {
                "account": []
            },
            "links": {
                "self": "/accounts"
            },
            "meta": {
                "totalPages": 1
            }
        }
    
    client_name = client.full_name if client else ""
    logger.info(f"Found client: id={client.id}, person_id={client.person_id}, name={client_name}")
    
    # Получаем счета
    result = await db.execute(
        select(Account)
        .where(Account.client_id == client.id)
        .where(Account.status == "active")
    )
    accounts = result.scalars().all()
    logger.info(f"Found {len(accounts)} accounts for client_id={client.id} (person_id={target_client_id})")
    
    # Формируем ответ в формате OpenBanking Russia
    return {
        "data": {
            "account": [
                {
                    "accountId": f"acc-{acc.id}",
                    "status": "Enabled" if acc.status == "active" else "Disabled",
                    "currency": acc.currency,
                    "accountType": "Personal" if acc.account_type == "checking" else "Business",
                    "accountSubType": acc.account_type.title(),
                    "nickname": f"{acc.account_type.title()} счет",
                    "openingDate": acc.opened_at.date().isoformat(),
                    "account": [
                        {
                            "schemeName": "RU.CBR.PAN",
                            "identification": acc.account_number,
                            "name": client_name
                        }
                    ]
                }
                for acc in accounts
            ]
        },
        "links": {
            "self": "/accounts"
        },
        "meta": {
            "totalPages": 1
        }
    }


@router.get("/external", summary="Получить счета из внешних банков", include_in_schema=False)
@cache(expire=config.CACHE_EXPIRE_SECONDS, key_builder=client_key_builder)
async def get_external_accounts(
    request: Request,
    response: Response,
    force_refresh: bool = False,
    current_client: dict = Depends(get_current_client),
    db: AsyncSession = Depends(get_db)
):
    """
    Получить счета клиента из всех внешних банков

    Использует токены из app.state.tokens для запросов к внешним банкам

    Кэшируется на 5 минут (300 секунд) для каждого клиента.
    Заголовок X-FastAPI-Cache: HIT/MISS показывает, получен ли ответ из кэша.

    Args:
        force_refresh: Если True, обходит кэш и получает свежие данные
    """
    if not current_client:
        logger.warning("Unauthorized request to get_external_accounts")
        raise HTTPException(401, "Unauthorized")
    
    client_id = current_client["client_id"]
    logger.info(f"Fetching external accounts for client_id={client_id}")
    
    # Получить токены из app.state
    tokens = getattr(request.app.state, "tokens", {})
    logger.debug(f"Retrieved {len(tokens)} tokens from app.state")
    
    # Получить счета из всех внешних банков
    try:
        accounts = await get_external_accounts_for_client(
            client_person_id=client_id,
            db=db,
            app_state_tokens=tokens
        )
        logger.info(f"Fetched {len(accounts)} account responses from external banks")
    except Exception as e:
        logger.error(f"Error fetching external accounts for client_id={client_id}: {e}", exc_info=True)
        raise
    
    # Подсчитать статистику
    total_accounts = len([acc for acc in accounts if acc.get("account") is not None])
    banks_with_accounts = len(set(acc["bank_code"] for acc in accounts if acc.get("account") is not None))
    
    logger.info(
        f"External accounts summary for client_id={client_id}: "
        f"total_accounts={total_accounts}, banks_count={banks_with_accounts}"
    )

    # Add cache-busting headers if force_refresh is requested
    if force_refresh:
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        logger.info(f"Force refresh requested, added cache-busting headers for client_id={client_id}")

    return {
        "data": {
            "accounts": accounts
        },
        "meta": {
            "total": total_accounts,
            "banks_count": banks_with_accounts
        }
    }


@router.post("/external/refresh", summary="Обновить кэш счетов из внешних банков", include_in_schema=False)
async def refresh_external_accounts(
    current_client: dict = Depends(get_current_client),
):
    """
    Инвалидировать кэш счетов из внешних банков для текущего клиента
    
    После вызова этого endpoint следующий запрос к /accounts/external
    получит свежие данные из внешних банков.
    """
    if not current_client:
        logger.warning("Unauthorized request to refresh_external_accounts")
        raise HTTPException(401, "Unauthorized")
    
    client_id = current_client["client_id"]
    logger.info(f"Invalidating cache for external accounts, client_id={client_id}")
    
    redis_client = None
    try:
        # Create Redis connection
        redis_client = await aioredis.from_url(
            config.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
        
        # Invalidate cache for this client
        deleted_keys = await invalidate_client_cache(redis_client, client_id)
        
        logger.info(f"Cache invalidated for client_id={client_id}, deleted {deleted_keys} keys")
        
        return {
            "data": {
                "message": "Cache invalidated successfully",
                "client_id": client_id,
                "deleted_keys": deleted_keys
            },
            "meta": {
                "message": "Кэш успешно обновлен"
            }
        }
    except Exception as e:
        logger.error(f"Error invalidating cache for client_id={client_id}: {e}", exc_info=True)
        raise HTTPException(500, f"Error invalidating cache: {str(e)}")
    finally:
        # Close Redis connection if it was created
        if redis_client:
            try:
                await redis_client.close()
            except Exception as close_error:
                logger.warning(f"Error closing Redis connection: {close_error}")


@router.get("/{account_id}", summary="Получить счет")
async def get_account(
    account_id: str,
    x_consent_id: Optional[str] = Header(None, alias="x-consent-id"),
    current_client: Optional[dict] = Depends(get_current_client),
    db: AsyncSession = Depends(get_db)
):
    """Получение детальной информации о счете"""
    
    # Извлекаем ID из строки "acc-123"
    acc_id = int(account_id.replace("acc-", ""))
    
    result = await db.execute(
        select(Account).where(Account.id == acc_id)
    )
    account = result.scalar_one_or_none()
    
    if not account:
        raise HTTPException(404, "Account not found")
    
    # TODO: Проверить права доступа
    
    return {
        "data": {
            "account": [
                {
                    "accountId": f"acc-{account.id}",
                    "status": "Enabled",
                    "currency": account.currency,
                    "accountType": "Personal",
                    "accountSubType": account.account_type.title(),
                    "description": f"{account.account_type} account",
                    "nickname": f"{account.account_type.title()} счет",
                    "openingDate": account.opened_at.date().isoformat()
                }
            ]
        }
    }


@router.get("/{account_id}/balances", summary="Получить балансы")
async def get_balances(
    account_id: str,
    x_consent_id: Optional[str] = Header(None, alias="x-consent-id"),
    current_client: Optional[dict] = Depends(get_current_client),
    db: AsyncSession = Depends(get_db)
):
    """Получение баланса счета"""
    
    acc_id = int(account_id.replace("acc-", ""))
    
    result = await db.execute(
        select(Account).where(Account.id == acc_id)
    )
    account = result.scalar_one_or_none()
    
    if not account:
        raise HTTPException(404, "Account not found")
    
    return {
        "data": {
            "balance": [
                {
                    "accountId": f"acc-{account.id}",
                    "type": "InterimAvailable",
                    "dateTime": datetime.utcnow().isoformat() + "Z",
                    "amount": {
                        "amount": str(account.balance),
                        "currency": account.currency
                    },
                    "creditDebitIndicator": "Credit"
                },
                {
                    "accountId": f"acc-{account.id}",
                    "type": "InterimBooked",
                    "dateTime": datetime.utcnow().isoformat() + "Z",
                    "amount": {
                        "amount": str(account.balance),
                        "currency": account.currency
                    },
                    "creditDebitIndicator": "Credit"
                }
            ]
        }
    }


@router.get("/{account_id}/transactions", summary="Получить транзакции")
async def get_transactions(
    account_id: str,
    from_booking_date_time: Optional[str] = None,
    to_booking_date_time: Optional[str] = None,
    x_consent_id: Optional[str] = Header(None, alias="x-consent-id"),
    current_client: Optional[dict] = Depends(get_current_client),
    db: AsyncSession = Depends(get_db)
):
    """Получение списка транзакций по счету"""
    
    acc_id = int(account_id.replace("acc-", ""))
    
    query = select(Transaction).where(Transaction.account_id == acc_id)
    
    # Фильтры по датам (опционально)
    if from_booking_date_time:
        # TODO: parse date
        pass
    
    result = await db.execute(query.order_by(Transaction.transaction_date.desc()).limit(50))
    transactions = result.scalars().all()
    
    return {
        "data": {
            "transaction": [
                {
                    "accountId": f"acc-{acc_id}",
                    "transactionId": tx.transaction_id,
                    "amount": {
                        "amount": str(abs(tx.amount)),
                        "currency": "RUB"
                    },
                    "creditDebitIndicator": "Credit" if tx.direction == "credit" else "Debit",
                    "status": "Booked",
                    "bookingDateTime": tx.transaction_date.isoformat() + "Z",
                    "valueDateTime": tx.transaction_date.isoformat() + "Z",
                    "transactionInformation": tx.description or "",
                    "bankTransactionCode": {
                        "code": "ReceivedCreditTransfer" if tx.direction == "credit" else "IssuedDebitTransfer"
                    }
                }
                for tx in transactions
            ]
        },
        "links": {
            "self": f"/accounts/{account_id}/transactions"
        }
    }


class CreateAccountRequest(BaseModel):
    """Запрос на создание нового счета"""
    account_type: str
    initial_balance: float = 0


class AccountStatusUpdate(BaseModel):
    """Обновление статуса счета"""
    status: str


class AccountCloseRequest(BaseModel):
    """Запрос на закрытие счета с переводом остатка"""
    action: str  # "transfer" или "donate"
    destination_account_id: Optional[str] = None  # Для action=transfer


@router.post("", summary="Создать счет", include_in_schema=False)
async def create_account(
    request: CreateAccountRequest,
    current_client: dict = Depends(get_current_client),
    db: AsyncSession = Depends(get_db)
):
    """
    Создание нового счета
    
    Поддерживаемые типы: checking, savings
    """
    # Найти клиента
    result = await db.execute(
        select(Client).where(Client.person_id == current_client["client_id"])
    )
    client = result.scalar_one_or_none()
    
    if not client:
        raise HTTPException(404, "Client not found")
    
    # Валидация типа счета
    valid_types = ["checking", "savings"]
    if request.account_type not in valid_types:
        raise HTTPException(400, f"Invalid account type. Must be one of: {', '.join(valid_types)}")
    
    # Генерация номера счета
    # 408 - текущий счет, 42301 - сберегательный
    if request.account_type == "checking":
        account_prefix = "408"
    elif request.account_type == "savings":
        account_prefix = "42301"
    else:
        account_prefix = "408"
    
    account_number = f"{account_prefix}{uuid.uuid4().hex[:15]}"
    
    # Создать счет
    new_account = Account(
        client_id=client.id,
        account_number=account_number,
        account_type=request.account_type,
        balance=Decimal(str(request.initial_balance)),
        currency="RUB",
        status="active"
    )
    
    db.add(new_account)
    await db.commit()
    await db.refresh(new_account)
    
    # Если начальный баланс > 0, создать транзакцию
    if request.initial_balance > 0:
        initial_tx = Transaction(
            account_id=new_account.id,
            transaction_id=f"tx-{uuid.uuid4().hex[:12]}",
            amount=Decimal(str(request.initial_balance)),
            direction="credit",
            counterparty="Начальное пополнение",
            description="Начальный баланс при открытии счета"
        )
        db.add(initial_tx)
        await db.commit()
    
    return {
        "data": {
            "accountId": f"acc-{new_account.id}",
            "account_number": new_account.account_number,
            "account_type": new_account.account_type,
            "balance": float(new_account.balance),
            "status": new_account.status
        },
        "meta": {
            "message": "Account created successfully"
        }
    }


@router.put("/{account_id}/status", summary="Изменить статус счета", include_in_schema=False)
async def update_account_status(
    account_id: str,
    request: AccountStatusUpdate,
    current_client: dict = Depends(get_current_client),
    db: AsyncSession = Depends(get_db)
):
    """
    Изменение статуса счета (закрытие)
    
    Допустимые статусы: active, closed
    """
    # Извлечь ID
    acc_id = int(account_id.replace("acc-", ""))
    
    # Найти счет
    result = await db.execute(
        select(Account, Client)
        .join(Client, Account.client_id == Client.id)
        .where(Account.id == acc_id)
    )
    account_data = result.first()
    
    if not account_data:
        raise HTTPException(404, "Account not found")
    
    account, client = account_data
    
    # Проверить что это счет текущего клиента
    if client.person_id != current_client["client_id"]:
        raise HTTPException(403, "Access denied")
    
    # Проверить валидность статуса
    valid_statuses = ["active", "closed"]
    if request.status not in valid_statuses:
        raise HTTPException(400, f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
    
    # Обновить статус
    account.status = request.status
    await db.commit()
    
    return {
        "data": {
            "accountId": f"acc-{account.id}",
            "account_number": account.account_number,
            "status": account.status
        },
        "meta": {
            "message": f"Account status updated to {request.status}"
        }
    }


@router.put("/{account_id}/close", summary="Закрыть счет", include_in_schema=False)
async def close_account_with_balance(
    account_id: str,
    request: AccountCloseRequest,
    current_client: dict = Depends(get_current_client),
    db: AsyncSession = Depends(get_db)
):
    """
    Закрытие счета с переводом остатка или дарением банку
    
    Actions:
    - transfer: перевести остаток на другой счет
    - donate: подарить остаток банку (увеличить capital)
    """
    # Извлечь ID
    acc_id = int(account_id.replace("acc-", ""))
    
    # Найти счет
    result = await db.execute(
        select(Account, Client)
        .join(Client, Account.client_id == Client.id)
        .where(Account.id == acc_id)
    )
    account_data = result.first()
    
    if not account_data:
        raise HTTPException(404, "Account not found")
    
    account, client = account_data
    
    # Проверить что это счет текущего клиента
    if client.person_id != current_client["client_id"]:
        raise HTTPException(403, "Access denied")
    
    balance = account.balance
    
    if request.action == "transfer":
        # Перевести остаток на другой счет
        if not request.destination_account_id:
            raise HTTPException(400, "destination_account_id required for transfer action")
        
        dest_acc_id = int(request.destination_account_id.replace("acc-", ""))
        dest_result = await db.execute(
            select(Account).where(Account.id == dest_acc_id, Account.client_id == client.id)
        )
        dest_account = dest_result.scalar_one_or_none()
        
        if not dest_account:
            raise HTTPException(404, "Destination account not found")
        
        # Перевести средства
        dest_account.balance += balance
        account.balance = Decimal("0")
        
        # Создать транзакции
        debit_tx = Transaction(
            account_id=account.id,
            transaction_id=f"tx-{uuid.uuid4().hex[:12]}",
            amount=balance,
            direction="debit",
            counterparty="Закрытие счета",
            description=f"Перевод на {dest_account.account_number} при закрытии"
        )
        db.add(debit_tx)
        
        credit_tx = Transaction(
            account_id=dest_account.id,
            transaction_id=f"tx-{uuid.uuid4().hex[:12]}",
            amount=balance,
            direction="credit",
            counterparty="Пополнение",
            description=f"Перевод с {account.account_number} (закрытие счета)"
        )
        db.add(credit_tx)
        
    elif request.action == "donate":
        # Подарить банку (увеличить capital)
        capital_result = await db.execute(
            select(BankCapital).where(BankCapital.bank_code == config.BANK_CODE)
        )
        capital = capital_result.scalar_one_or_none()
        
        if capital:
            capital.capital += balance
        
        # Создать транзакцию списания
        donate_tx = Transaction(
            account_id=account.id,
            transaction_id=f"tx-{uuid.uuid4().hex[:12]}",
            amount=balance,
            direction="debit",
            counterparty="Дар банку",
            description="Дарение средств банку при закрытии счета"
        )
        db.add(donate_tx)
        
        account.balance = Decimal("0")
    
    else:
        raise HTTPException(400, f"Invalid action: {request.action}")
    
    # Закрыть счет
    account.status = "closed"
    await db.commit()
    
    return {
        "data": {
            "accountId": f"acc-{account.id}",
            "account_number": account.account_number,
            "status": "closed",
            "action": request.action,
            "amount_transferred": float(balance)
        },
        "meta": {
            "message": f"Account closed with {request.action} action"
        }
    }

