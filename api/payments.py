"""
Payments API - Инициирование переводов
OpenBanking Russia Payments API compatible
Спецификация: https://wiki.opendatarussia.ru/specifications (Payments API)
"""
from fastapi import APIRouter, Depends, HTTPException, Header, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from typing import Optional
from datetime import datetime
from decimal import Decimal
import uuid

from database import get_db
from models import Payment, PaymentConsent, Bank
from services.auth_service import get_current_client
from services.payment_service import PaymentService
from services.external_payment_service import execute_external_payment
from services.account_service import get_external_accounts_for_client
from services.cache_utils import client_page_key_builder, invalidate_client_cache
from config import config
from log import logger
from fastapi_cache.decorator import cache
from fastapi import Response
from redis import asyncio as aioredis


router = APIRouter(prefix="/payments", tags=["4 Переводы"])


# === Pydantic Models (OpenBanking Russia format) ===

class AmountModel(BaseModel):
    """Сумма платежа"""
    amount: str = Field(..., description="Сумма в формате строки")
    currency: str = "RUB"


class AccountIdentification(BaseModel):
    """Идентификация счета"""
    schemeName: str = "RU.CBR.PAN"
    identification: str = Field(..., description="Номер счета")
    name: Optional[str] = None


class PaymentInitiation(BaseModel):
    """Данные для инициации платежа"""
    instructionIdentification: str = Field(default_factory=lambda: f"instr-{uuid.uuid4().hex[:8]}")
    endToEndIdentification: str = Field(default_factory=lambda: f"e2e-{uuid.uuid4().hex[:8]}")
    instructedAmount: AmountModel
    debtorAccount: AccountIdentification
    creditorAccount: AccountIdentification
    remittanceInformation: Optional[dict] = None


class PaymentRequest(BaseModel):
    """Запрос создания платежа (OpenBanking Russia format)"""
    data: dict = Field(..., description="Содержит initiation")
    risk: Optional[dict] = {}


class PaymentData(BaseModel):
    """Данные платежа в ответе"""
    paymentId: str
    status: str
    creationDateTime: str
    statusUpdateDateTime: str


class PaymentResponse(BaseModel):
    """Ответ с платежом"""
    data: PaymentData
    links: dict
    meta: Optional[dict] = {}


# === Endpoints ===

@router.post("", response_model=PaymentResponse, status_code=201, summary="Создать платеж")
async def create_payment(
    request: PaymentRequest,
    x_fapi_interaction_id: Optional[str] = Header(None, alias="x-fapi-interaction-id"),
    x_fapi_customer_ip_address: Optional[str] = Header(None, alias="x-fapi-customer-ip-address"),
    x_payment_consent_id: Optional[str] = Header(None, alias="x-payment-consent-id"),
    x_requesting_bank: Optional[str] = Header(None, alias="x-requesting-bank"),
    current_client: dict = Depends(get_current_client),
    db: AsyncSession = Depends(get_db)
):
    """
    ## 💸 Создание платежа (разовый перевод)

    **OpenBanking Russia Payments API**

    ### Два типа платежей:

    #### 1️⃣ Внутрибанковский перевод (тот же банк)
    ```json
    {
      "data": {
        "initiation": {
          "instructedAmount": {
            "amount": "1000.00",
            "currency": "RUB"
          },
          "debtorAccount": {
            "schemeName": "RU.CBR.PAN",
            "identification": "40817810099910004312"
          },
          "creditorAccount": {
            "schemeName": "RU.CBR.PAN",
            "identification": "40817810099910005423"
          }
        }
      }
    }
    ```

    #### 2️⃣ Межбанковский перевод
    Добавьте в `creditorAccount`:
    ```json
    {
      "creditorAccount": {
        "identification": "40817810099910001234",
        "bank_code": "abank"  // Код банка получателя
      }
    }
    ```
    
    ### Статусы платежа:
    - `pending` — ожидает обработки
    - `completed` — успешно выполнен
    - `failed` — ошибка (недостаточно средств, счет не найден)
    
    ### Проверка статуса:
    ```bash
    GET /payments/{payment_id}
    ```

    ### ⚠️ Важно:
    - Проверяйте баланс счета перед платежом: `GET /accounts/{account_id}/balances`
    - Счет списания (`debtorAccount`) должен принадлежать авторизованному клиенту
    - Для межбанковых переводов используйте правильный `bank_code`
    - Коды банков: `vbank`, `abank`, `sbank`

    ### Sandbox особенности:
    - Межбанковые переводы выполняются мгновенно
    - Комиссия не взимается
    - Все валюты конвертируются по курсу 1:1 для упрощения
    """
    if not current_client:
        raise HTTPException(401, "Unauthorized")
    
    # Проверка согласия для межбанковых запросов
    payment_consent_id_to_store = None
    if x_requesting_bank:
        # Межбанковый запрос - требуется согласие на платеж
        if not x_payment_consent_id:
            raise HTTPException(
                403,
                detail={
                    "error": "PAYMENT_CONSENT_REQUIRED",
                    "message": "Требуется согласие клиента на платеж",
                    "consent_request_url": "/payment-consents/request"
                }
            )

        # Проверить согласие
        consent_result = await db.execute(
            select(PaymentConsent).where(
                and_(
                    PaymentConsent.consent_id == x_payment_consent_id,
                    PaymentConsent.status == "active",
                    PaymentConsent.expiration_date_time > datetime.utcnow()
                )
            )
        )
        payment_consent = consent_result.scalar_one_or_none()

        if not payment_consent:
            raise HTTPException(
                403,
                detail={
                    "error": "INVALID_CONSENT",
                    "message": "Согласие недействительно, истекло или уже использовано"
                }
            )

        # Проверить что согласие выдано запрашивающему банку
        if payment_consent.granted_to != x_requesting_bank:
            raise HTTPException(
                403,
                detail={
                    "error": "CONSENT_MISMATCH",
                    "message": "Согласие выдано другому банку"
                }
            )

        payment_consent_id_to_store = x_payment_consent_id

    # Извлечь данные из request
    initiation = request.data.get("initiation")
    if not initiation:
        raise HTTPException(400, "Missing initiation data")
    
    amount_data = initiation.get("instructedAmount", {})
    debtor_account = initiation.get("debtorAccount", {})
    creditor_account = initiation.get("creditorAccount", {})
    
    # Описание платежа
    remittance = initiation.get("remittanceInformation", {})
    description = remittance.get("unstructured", "") if remittance else ""
    
    try:
        # Инициировать платеж
        payment, interbank = await PaymentService.initiate_payment(
            db=db,
            from_account_number=debtor_account.get("identification"),
            to_account_number=creditor_account.get("identification"),
            amount=Decimal(amount_data.get("amount", "0")),
            description=description,
            payment_consent_id=payment_consent_id_to_store
        )

        # Если использовалось согласие - пометить его как использованное
        if payment_consent_id_to_store:
            consent_result = await db.execute(
                select(PaymentConsent).where(PaymentConsent.consent_id == payment_consent_id_to_store)
            )
            consent = consent_result.scalar_one_or_none()
            if consent:
                consent.status = "used"
                consent.used_at = datetime.utcnow()
                consent.status_update_date_time = datetime.utcnow()
                await db.commit()

        # Формируем ответ OpenBanking Russia
        payment_data = PaymentData(
            paymentId=payment.payment_id,
            status=payment.status,
            creationDateTime=payment.creation_date_time.isoformat() + "Z",
            statusUpdateDateTime=payment.status_update_date_time.isoformat() + "Z"
        )
        
        return PaymentResponse(
            data=payment_data,
            links={
                "self": f"/payments/{payment.payment_id}"
            },
            meta={}
        )
        
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/{payment_id}", response_model=PaymentResponse, summary="Получить платеж")
async def get_payment(
    payment_id: str,
    x_fapi_interaction_id: Optional[str] = Header(None, alias="x-fapi-interaction-id"),
    current_client: dict = Depends(get_current_client),
    db: AsyncSession = Depends(get_db)
):
    """
    Получение статуса платежа
    
    OpenBanking Russia Payments API
    GET /payments/{paymentId}
    """
    if not current_client:
        raise HTTPException(401, "Unauthorized")
    
    payment = await PaymentService.get_payment(db, payment_id)
    
    if not payment:
        raise HTTPException(404, "Payment not found")
    
    # TODO: Проверить что клиент имеет право просматривать этот платеж
    
    payment_data = PaymentData(
        paymentId=payment.payment_id,
        status=payment.status,
        creationDateTime=payment.creation_date_time.isoformat() + "Z",
        statusUpdateDateTime=payment.status_update_date_time.isoformat() + "Z"
    )
    
    return PaymentResponse(
        data=payment_data,
        links={
            "self": f"/payments/{payment_id}"
        }
    )


# === External Payment Models ===

class ExternalPaymentRequest(BaseModel):
    """Запрос создания платежа во внешний банк"""
    from_account: str = Field(..., description="Счет списания (формат: bank_code:account_id)")
    to_account: str = Field(..., description="Счет зачисления (формат: bank_code:account_id)")
    amount: Decimal = Field(..., description="Сумма платежа", gt=0)
    description: Optional[str] = Field(None, description="Описание платежа")


class ExternalPaymentResponse(BaseModel):
    """Ответ создания платежа во внешний банк"""
    success: bool
    payment_id: Optional[str] = None
    external_payment_id: Optional[str] = None
    status: Optional[str] = None
    error: Optional[str] = None


# === External Payment Endpoints ===

@router.post("/external", response_model=ExternalPaymentResponse, summary="Создать платеж во внешний банк")
async def create_external_payment(
    request_data: ExternalPaymentRequest,
    request: Request,
    current_client: dict = Depends(get_current_client),
    db: AsyncSession = Depends(get_db)
):
    """
    ## 🌐 Создание платежа во внешний банк (Мультибанк)

    Создает платеж через внешний банк используя OpenBanking API.

    ### Процесс:
    1. Запрашивает согласие на платеж у внешнего банка
    2. Выполняет платеж используя полученное согласие
    3. Сохраняет информацию о платеже в локальной базе

    ### Формат запроса:
    ```json
    {
      "from_account": "vbank:40817810099910004312",
      "to_account": "abank:40817810099910001234",
      "amount": 5000.00,
      "description": "Оплата услуг"
    }
    ```

    ### Формат счета:
    - `bank_code:account_id` - код банка и номер счета, разделенные двоеточием
    - Пример: `abank:40817810099910001234`

    ### Статусы платежа:
    - `pending` — ожидает обработки
    - `completed` — успешно выполнен
    - `failed` — ошибка

    ### Примечания:
    - Счет списания должен принадлежать текущему банку
    - Счет зачисления должен принадлежать внешнему банку
    - Требуется активный токен для внешнего банка
    """
    if not current_client:
        raise HTTPException(401, "Unauthorized")

    client_id = current_client["client_id"]

    logger.info(
        f"External payment request from client {client_id}: "
        f"from={request_data.from_account} to={request_data.to_account} amount={request_data.amount}"
    )

    # Парсинг счетов (формат: bank_code:account_id)
    try:
        from_parts = request_data.from_account.split(":", 1)
        to_parts = request_data.to_account.split(":", 1)

        if len(from_parts) != 2 or len(to_parts) != 2:
            raise ValueError("Invalid account format. Expected 'bank_code:account_id'")

        from_bank_code, from_account_id = from_parts
        to_bank_code, to_account_id = to_parts
    except Exception as e:
        logger.warning(f"Invalid account format in external payment request: {e}")
        raise HTTPException(400, f"Invalid account format: {str(e)}")

    # Получить исходный банк (source bank) - тот, с которого переводим
    source_bank_result = await db.execute(
        select(Bank).where(Bank.code == from_bank_code)
    )
    source_bank = source_bank_result.scalar_one_or_none()

    if not source_bank:
        logger.warning(f"Source bank not found: {from_bank_code}")
        raise HTTPException(404, f"Source bank not found: {from_bank_code}")

    if not source_bank.external:
        logger.warning(f"Source bank {from_bank_code} is not an external bank")
        raise HTTPException(400, f"Source bank {from_bank_code} is not an external bank")

    # Получить целевой банк (destination bank) для сохранения в базе
    dest_bank_result = await db.execute(
        select(Bank).where(Bank.code == to_bank_code)
    )
    dest_bank = dest_bank_result.scalar_one_or_none()

    if not dest_bank:
        logger.warning(f"Destination bank not found: {to_bank_code}")
        raise HTTPException(404, f"Destination bank not found: {to_bank_code}")

    # Получить токен для исходного банка (source bank)
    tokens = getattr(request.app.state, "tokens", {})
    bank_token_info = tokens.get(from_bank_code, {})
    token = bank_token_info.get("token")

    if not token:
        logger.error(f"No token available for source bank {from_bank_code}")
        raise HTTPException(503, f"Service unavailable: No token for source bank {from_bank_code}")

    # Выполнить платеж через исходный банк (source bank)
    try:
        result = await execute_external_payment(
            bank=source_bank,
            client_person_id=client_id,
            token=token,
            amount=request_data.amount,
            debtor_account=from_account_id,
            creditor_account=to_account_id,
            description=request_data.description or "Payment",
            db=db,
            creditor_bank_code=dest_bank.code
        )

        if not result["success"]:
            logger.error(f"External payment failed: {result['error']}")
            return ExternalPaymentResponse(
                success=False,
                error=result["error"]
            )

        # Создать локальную запись о платеже
        payment_id = f"pay-ext-{uuid.uuid4().hex[:16]}"

        new_payment = Payment(
            payment_id=payment_id,
            account_id=None,  # Нет локального счета для внешних платежей
            amount=request_data.amount,
            currency="RUB",
            destination_account=to_account_id,
            destination_bank=to_bank_code,
            description=request_data.description or "External payment",
            status=result["status"] or "pending",
            payment_direction="outgoing",
            source_account=from_account_id,
            source_bank=from_bank_code,
            source_bank_id=source_bank.id,
            destination_bank_id=dest_bank.id,
            external_payment_id=result["external_payment_id"],
            creation_date_time=datetime.utcnow(),
            status_update_date_time=datetime.utcnow()
        )

        db.add(new_payment)
        await db.commit()

        logger.info(
            f"External payment {payment_id} created successfully: "
            f"external_id={result['external_payment_id']}, status={result['status']}"
        )

        return ExternalPaymentResponse(
            success=True,
            payment_id=payment_id,
            external_payment_id=result["external_payment_id"],
            status=result["status"]
        )

    except Exception as e:
        logger.error(f"Error creating external payment: {e}", exc_info=True)
        raise HTTPException(500, f"Internal server error: {str(e)[:100]}")


@router.get("/external/history", summary="Получить историю платежей из внешних банков")
@cache(expire=config.CACHE_EXPIRE_SECONDS, key_builder=client_page_key_builder)
async def get_external_payment_history(
    request: Request,
    response: Response,
    page: int = 1,
    current_client: dict = Depends(get_current_client),
    db: AsyncSession = Depends(get_db)
):
    """
    Получить историю платежей из внешних банков для текущего клиента
    
    Возвращает все платежи, которые были созданы из внешних банков,
    где source_account соответствует счетам клиента во внешних банках.
    
    Query params:
    - page: номер страницы (начинается с 1, по умолчанию 1)
    """
    if not current_client:
        raise HTTPException(401, "Unauthorized")
    
    if page < 1:
        page = 1
    
    client_id = current_client["client_id"]
    page_size = config.EXTERNAL_PAYMENT_HISTORY_PAGE_SIZE
    logger.info(f"Fetching external payment history for client {client_id}, page {page}")
    
    try:
        # Получить токены из app.state
        tokens = getattr(request.app.state, "tokens", {})
        
        # Получить внешние счета клиента
        external_accounts = await get_external_accounts_for_client(
            client_person_id=client_id,
            db=db,
            app_state_tokens=tokens
        )
        
        # Извлечь номера счетов из внешних счетов
        client_account_numbers = []
        for acc in external_accounts:
            if acc.get("account") and acc.get("error") is None:
                account_data = acc["account"]
                if isinstance(account_data, dict) and "account" in account_data:
                    account_list = account_data["account"]
                    if isinstance(account_list, list) and len(account_list) > 0:
                        account_identification = account_list[0].get("identification")
                        if account_identification:
                            client_account_numbers.append(account_identification)

        if not client_account_numbers:
            logger.info(f"No external accounts found for client {client_id}")
            return {
                "data": {
                    "payments": []
                },
                "meta": {
                    "total": 0,
                    "page": page,
                    "page_size": page_size,
                    "total_pages": 0
                }
            }
        
        logger.debug(f"Found {len(client_account_numbers)} external account numbers for client {client_id}")
        
        # Базовый запрос для подсчета общего количества
        base_query = select(Payment).where(
            and_(
                Payment.source_bank.isnot(None),
                Payment.source_account.in_(client_account_numbers)
            )
        )
        
        # Получить общее количество платежей
        count_result = await db.execute(
            select(func.count(Payment.id)).where(
                and_(
                    Payment.source_bank.isnot(None),
                    Payment.source_account.in_(client_account_numbers)
                )
            )
        )
        total_count = count_result.scalar() or 0
        
        # Вычислить offset и limit для пагинации
        offset = (page - 1) * page_size
        total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 0
        
        # Запросить платежи с пагинацией
        result = await db.execute(
            base_query
            .order_by(Payment.creation_date_time.desc())
            .offset(offset)
            .limit(page_size)
        )
        payments = result.scalars().all()
        
        logger.info(f"Found {len(payments)} external payments for client {client_id} (page {page}/{total_pages})")
        
        # Формировать ответ
        payments_data = []
        for payment in payments:
            payments_data.append({
                "payment_id": payment.payment_id,
                "amount": float(payment.amount),
                "currency": payment.currency or "RUB",
                "source_bank": payment.source_bank or "",
                "source_account": payment.source_account or "",
                "destination_bank": payment.destination_bank or "",
                "destination_account": payment.destination_account or "",
                "description": payment.description or "",
                "status": payment.status or "",
                "creation_date_time": payment.creation_date_time.isoformat() + "Z" if payment.creation_date_time else "",
                "external_payment_id": payment.external_payment_id or ""
            })
        
        return {
            "data": {
                "payments": payments_data
            },
            "meta": {
                "total": total_count,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching external payment history for client {client_id}: {e}", exc_info=True)
        raise HTTPException(500, f"Internal server error: {str(e)[:100]}")


@router.post("/external/history/refresh", summary="Обновить кэш истории платежей из внешних банков", include_in_schema=False)
async def refresh_external_payment_history(
    current_client: dict = Depends(get_current_client),
):
    """
    Инвалидировать кэш истории платежей из внешних банков для текущего клиента

    После вызова этого endpoint следующий запрос к /payments/external/history
    получит свежие данные из внешних банков.
    """
    if not current_client:
        logger.warning("Unauthorized request to refresh_external_payment_history")
        raise HTTPException(401, "Unauthorized")

    client_id = current_client["client_id"]
    logger.info(f"Invalidating cache for external payment history, client_id={client_id}")

    redis_client = None
    try:
        # Create Redis connection
        redis_client = await aioredis.from_url(
            config.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )

        # Invalidate cache for this client (all pages)
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
            except Exception as e:
                logger.error(f"Error closing Redis connection: {e}")

