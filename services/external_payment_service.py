"""
Сервис для работы с платежами во внешние банки
Включает функции для создания согласий на платежи и выполнения платежей
"""
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict
from decimal import Decimal
from datetime import datetime
import httpx
import uuid

from models import Bank, Payment
from config import config
from log import logger


async def execute_external_payment(
    bank: Bank,
    client_person_id: str,
    token: str,
    amount: Decimal,
    debtor_account: str,
    creditor_account: str,
    description: str,
    db: AsyncSession,
    http_client: Optional[httpx.AsyncClient] = None,
    creditor_bank_code: Optional[str] = None,
    source_bank_id: Optional[int] = None,
    destination_bank_id: Optional[int] = None
) -> Dict:
    """
    Выполнить платеж во внешний банк (с автоматическим созданием согласия)

    Двухэтапный процесс:
    1. Запросить согласие на платеж (POST /payment-consents/request)
    2. Выполнить платеж используя согласие (POST /payments)

    Args:
        bank: Bank object (SOURCE bank - где находится счет списания)
        client_person_id: ID клиента (person_id)
        token: Auth token для банка
        amount: Сумма платежа
        debtor_account: Счет списания
        creditor_account: Счет зачисления
        description: Описание платежа
        db: Database session
        http_client: Optional HTTP client (создается новый если None)
        creditor_bank_code: Код банка получателя (для межбанковских переводов)
        source_bank_id: ID банка-источника в БД (для сохранения Payment)
        destination_bank_id: ID банка-получателя в БД (для сохранения Payment)

    Returns:
        Dict: {
            "success": bool,
            "payment_id": Optional[str],  # local payment ID
            "external_payment_id": Optional[str],
            "status": Optional[str],
            "error": Optional[str]
        }
    """
    logger.info(
        f"Executing external payment: source_bank={bank.code} ({bank.name}), "
        f"amount={amount}, from_account={debtor_account} to_account={creditor_account}"
        f"{f', creditor_bank={creditor_bank_code}' if creditor_bank_code else ''}"
    )

    try:
        should_close_client = False
        if http_client is None:
            http_client = httpx.AsyncClient(timeout=10.0)
            should_close_client = True

        try:
            # Шаг 1: Запросить согласие на платеж
            consent_url = f"{bank.api_url}/payment-consents/request"
            logger.info(
                f"Step 1: Requesting payment consent from {bank.code} for amount {amount} "
                f"| API: POST {consent_url}"
            )

            consent_data = {
                "requesting_bank": config.BANK_CODE,
                "client_id": client_person_id,
                "consent_type": "single_use",
                "debtor_account": debtor_account,
                "creditor_account": creditor_account,
                "amount": str(amount),
                "currency": "RUB",
                "reference": description[:35] if description else "Payment"
            }

            consent_response = await http_client.post(
                consent_url,
                json=consent_data,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                    "X-Requesting-Bank": config.BANK_CODE
                }
            )

            if consent_response.status_code not in [200, 201]:
                error_text = consent_response.text[:200] if consent_response.text else "Unknown error"
                logger.error(
                    f"Failed to request payment consent from {bank.code}: "
                    f"HTTP {consent_response.status_code}: {error_text}"
                )
                return {
                    "success": False,
                    "payment_id": None,
                    "external_payment_id": None,
                    "status": None,
                    "error": f"Consent request failed: HTTP {consent_response.status_code}"
                }

            consent_response_data = consent_response.json()

            # Извлечь consent_id из ответа (может быть в разных форматах)
            consent_id = (
                consent_response_data.get("Data", {}).get("ConsentId") or
                consent_response_data.get("data", {}).get("consentId") or
                consent_response_data.get("data", {}).get("consent_id") or
                consent_response_data.get("consent_id") or
                consent_response_data.get("ConsentId") or
                consent_response_data.get("id")
            )

            if not consent_id:
                logger.error(f"Could not extract consent_id from response: {consent_response_data}")
                return {
                    "success": False,
                    "payment_id": None,
                    "external_payment_id": None,
                    "status": None,
                    "error": "Failed to extract consent_id from response"
                }

            logger.info(f"Received consent_id: {consent_id} from {bank.code}")

            # Шаг 2: Выполнить платеж используя согласие
            payment_url = f"{bank.api_url}/payments"
            logger.info(
                f"Step 2: Executing payment with consent {consent_id} | "
                f"source_bank={config.BANK_CODE} -> destination_bank={bank.code} | "
                f"API: POST {payment_url}?client_id={client_person_id}"
            )

            payment_data = {
                "data": {
                    "initiation": {
                        "instructedAmount": {
                            "amount": str(amount),
                            "currency": "RUB"
                        },
                        "debtorAccount": {
                            "schemeName": "RU.CBR.PAN",
                            "identification": debtor_account
                        },
                        "creditorAccount": {
                            "schemeName": "RU.CBR.PAN",
                            "identification": creditor_account,
                            "bank_code": creditor_bank_code if creditor_bank_code else bank.code
                        },
                        "comment": description[:140] if description else "Payment"
                    }
                }
            }

            payment_response = await http_client.post(
                payment_url,
                json=payment_data,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                    "X-Payment-Consent-Id": consent_id,
                    "X-Requesting-Bank": config.BANK_CODE
                },
                params={
                    "client_id": client_person_id
                }
            )

            if payment_response.status_code not in [200, 201]:
                error_text = payment_response.text[:200] if payment_response.text else "Unknown error"
                logger.error(
                    f"Failed to execute payment at {bank.code}: "
                    f"HTTP {payment_response.status_code}: {error_text}"
                )
                return {
                    "success": False,
                    "payment_id": None,
                    "external_payment_id": None,
                    "status": None,
                    "error": f"Payment execution failed: HTTP {payment_response.status_code}"
                }

            payment_response_data = payment_response.json()

            # Извлечь payment_id и status из ответа
            external_payment_id = (
                payment_response_data.get("Data", {}).get("PaymentId") or
                payment_response_data.get("data", {}).get("paymentId") or
                payment_response_data.get("data", {}).get("payment_id") or
                payment_response_data.get("payment_id") or
                payment_response_data.get("PaymentId") or
                payment_response_data.get("id")
            )

            payment_status = (
                payment_response_data.get("Data", {}).get("Status") or
                payment_response_data.get("data", {}).get("Status") or
                payment_response_data.get("data", {}).get("status") or
                payment_response_data.get("status")
            )

            if not external_payment_id:
                logger.error(f"Could not extract payment_id from response: {payment_response_data}")
                return {
                    "success": False,
                    "payment_id": None,
                    "external_payment_id": None,
                    "status": payment_status,
                    "error": "Failed to extract payment_id from response"
                }

            logger.info(
                f"External payment created successfully: external_payment_id={external_payment_id}, "
                f"status={payment_status}, source_bank={config.BANK_CODE}, destination_bank={bank.code} ({bank.name}), "
                f"amount={amount}"
            )

            # Сохранить платеж в базу данных
            payment_id = f"pay-ext-{uuid.uuid4().hex[:16]}"

            new_payment = Payment(
                payment_id=payment_id,
                account_id=None,  # Нет локального счета для внешних платежей
                amount=amount,
                currency="RUB",
                destination_account=creditor_account,
                destination_bank=creditor_bank_code or bank.code,
                description=description or "External payment",
                status=payment_status or "pending",
                payment_direction="outgoing",
                source_account=debtor_account,
                source_bank=bank.code,
                source_bank_id=source_bank_id,
                destination_bank_id=destination_bank_id,
                external_payment_id=external_payment_id,
                creation_date_time=datetime.utcnow(),
                status_update_date_time=datetime.utcnow()
            )

            db.add(new_payment)
            await db.commit()

            logger.info(
                f"Payment {payment_id} saved to database: "
                f"external_id={external_payment_id}, status={payment_status}"
            )

            return {
                "success": True,
                "payment_id": payment_id,
                "external_payment_id": external_payment_id,
                "status": payment_status or "pending",
                "error": None
            }

        except httpx.TimeoutException:
            logger.error(f"Timeout when executing payment to {bank.code}")
            return {
                "success": False,
                "payment_id": None,
                "external_payment_id": None,
                "status": None,
                "error": "Request timeout"
            }
        except httpx.RequestError as e:
            logger.error(f"Request error when executing payment to {bank.code}: {e}")
            return {
                "success": False,
                "payment_id": None,
                "external_payment_id": None,
                "status": None,
                "error": f"Connection error: {str(e)[:100]}"
            }
        except Exception as e:
            logger.error(f"Unexpected error when executing payment to {bank.code}: {e}", exc_info=True)
            return {
                "success": False,
                "payment_id": None,
                "external_payment_id": None,
                "status": None,
                "error": f"Error: {str(e)[:100]}"
            }
        finally:
            if should_close_client:
                await http_client.aclose()
    except Exception as e:
        logger.error(f"Critical error in execute_external_payment for {bank.code}: {e}", exc_info=True)
        return {
            "success": False,
            "payment_id": None,
            "external_payment_id": None,
            "status": None,
            "error": f"Critical error: {str(e)[:100]}"
        }


async def check_external_payment_status(
    bank: Bank,
    token: str,
    payment_id: str,
    http_client: Optional[httpx.AsyncClient] = None
) -> Dict:
    """
    Проверить статус платежа во внешнем банке

    Args:
        bank: Bank object (внешний банк)
        token: Auth token для банка
        payment_id: ID платежа во внешнем банке
        http_client: Optional HTTP client (создается новый если None)

    Returns:
        Dict: {
            "success": bool,
            "status": Optional[str],  # "pending", "completed", "failed"
            "error": Optional[str]
        }
    """
    logger.info(f"Checking payment status: {payment_id} at bank {bank.code}")

    try:
        should_close_client = False
        if http_client is None:
            http_client = httpx.AsyncClient(timeout=10.0)
            should_close_client = True

        try:
            response = await http_client.get(
                f"{bank.api_url}/payments/{payment_id}",
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-Requesting-Bank": config.BANK_CODE,
                    "Accept": "application/json"
                }
            )

            if response.status_code == 200:
                data = response.json()

                # Извлечь status из ответа
                payment_status = (
                    data.get("Data", {}).get("Status") or
                    data.get("data", {}).get("Status") or
                    data.get("data", {}).get("status") or
                    data.get("status")
                )

                logger.info(f"Payment {payment_id} status: {payment_status}")

                return {
                    "success": True,
                    "status": payment_status,
                    "error": None
                }
            else:
                error_text = response.text[:200] if response.text else "Unknown error"
                logger.error(
                    f"Failed to check payment status from {bank.code}: "
                    f"HTTP {response.status_code}: {error_text}"
                )
                return {
                    "success": False,
                    "status": None,
                    "error": f"HTTP {response.status_code}"
                }
        except httpx.TimeoutException:
            logger.error(f"Timeout when checking payment status from {bank.code}")
            return {
                "success": False,
                "status": None,
                "error": "Request timeout"
            }
        except httpx.RequestError as e:
            logger.error(f"Request error when checking payment status from {bank.code}: {e}")
            return {
                "success": False,
                "status": None,
                "error": f"Connection error: {str(e)[:100]}"
            }
        except Exception as e:
            logger.error(f"Unexpected error when checking payment status from {bank.code}: {e}", exc_info=True)
            return {
                "success": False,
                "status": None,
                "error": f"Error: {str(e)[:100]}"
            }
        finally:
            if should_close_client:
                await http_client.aclose()
    except Exception as e:
        logger.error(f"Critical error in check_external_payment_status for {bank.code}: {e}", exc_info=True)
        return {
            "success": False,
            "status": None,
            "error": f"Critical error: {str(e)[:100]}"
        }
