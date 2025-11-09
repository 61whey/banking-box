"""
Сервис для работы со счетами
Включает функции для получения счетов из внешних банков
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Dict, Optional
from datetime import datetime
import httpx
import logging

from models import Bank, Consent
from config import config

logger = logging.getLogger(__name__)


async def request_consent_from_external_bank(
    bank: Bank,
    client_person_id: str,
    token: str,
    db: AsyncSession,
    http_client: Optional[httpx.AsyncClient] = None
) -> Optional[str]:
    """
    Запросить согласие у внешнего банка и сохранить в базу данных
    
    Args:
        bank: Bank object
        client_person_id: ID клиента (person_id)
        token: Auth token для банка
        db: Database session
        http_client: Optional HTTP client (создается новый если None)
    
    Returns:
        Optional[str]: consent_id если успешно, None в противном случае
    """
    logger.info(f"Requesting consent for client {client_person_id} and bank {bank.code}")
    
    try:
        should_close_client = False
        if http_client is None:
            http_client = httpx.AsyncClient(timeout=10.0)
            should_close_client = True
        
        try:
            consent_data = {
                "client_id": client_person_id,
                "permissions": [
                    "ReadAccountsBasic",
                    "ReadAccountsDetail",
                    "ReadBalances",
                    "ReadTransactionsDetail"
                ],
                "expiration_date": "2025-12-31T23:59:59.000Z"
            }
            
            consent_response = await http_client.post(
                f"{bank.api_url}/account-consents/request",
                json=consent_data,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                    "x-requesting-bank": config.BANK_CODE
                }
            )
            
            if consent_response.status_code in [200, 201]:
                consent_response_data = consent_response.json()
                # Получить consent_id из ответа (может быть в разных форматах)
                consent_id = (
                    consent_response_data.get("Data", {}).get("ConsentId") or
                    consent_response_data.get("data", {}).get("consent_id") or
                    consent_response_data.get("consent_id") or
                    consent_response_data.get("ConsentId") or
                    consent_response_data.get("id")
                )
                
                if consent_id:
                    # Сохранить согласие в таблицу Consent
                    new_consent = Consent(
                        consent_id=consent_id,
                        client_id_external=client_person_id,
                        bank_id=bank.id,
                        granted_to=config.BANK_CODE,
                        permissions=["ReadAccountsBasic", "ReadAccountsDetail", "ReadBalances", "ReadTransactionsDetail"],
                        status="active",
                        expiration_date_time=datetime(2025, 12, 31, 23, 59, 59),
                        creation_date_time=datetime.utcnow(),
                        status_update_date_time=datetime.utcnow(),
                        signed_at=datetime.utcnow()
                    )
                    db.add(new_consent)
                    await db.commit()
                    logger.info(f"Saved new consent {consent_id} for client {client_person_id} and bank {bank.code}")
                    return consent_id
                else:
                    logger.warning(f"Could not extract consent_id from response: {consent_response_data}")
                    return None
            else:
                logger.error(f"Failed to request consent from {bank.code}: HTTP {consent_response.status_code}: {consent_response.text[:200]}")
                return None
        except Exception as e:
            logger.error(f"Error requesting consent from {bank.code}: {e}")
            return None
        finally:
            if should_close_client:
                await http_client.aclose()
    except Exception as e:
        logger.error(f"Unexpected error in request_consent_from_external_bank for {bank.code}: {e}")
        return None


async def get_accounts_from_external_bank(
    bank: Bank,
    client_person_id: str,
    token: str,
    consent_id: str,
    http_client: Optional[httpx.AsyncClient] = None
) -> List[Dict]:
    """
    Получить счета с балансами из внешнего банка
    
    Args:
        bank: Bank object
        client_person_id: ID клиента
        token: Auth token
        consent_id: Consent ID
        http_client: Optional HTTP client (создается новый если None)
    
    Returns:
        List[Dict]: Список счетов с форматом: {"bank_code": str, "bank_name": str, "account": dict, "balance": Optional[str], "error": Optional[str]}
    """
    accounts = []
    
    try:
        should_close_client = False
        if http_client is None:
            http_client = httpx.AsyncClient(timeout=10.0)
            should_close_client = True
        
        try:
            response = await http_client.get(
                f"{bank.api_url}/accounts",
                headers={
                    "Authorization": f"Bearer {token}",
                    "x-consent-id": consent_id,
                    "x-requesting-bank": config.BANK_CODE,
                    "accept": "application/json"
                },
                params={
                    "client_id": client_person_id
                }
            )
            
            if response.status_code == 200:
                # Успешный ответ
                data = response.json()
                account_list = data.get("data", {}).get("account", [])
                
                # Для каждого счета получить баланс
                for account in account_list:
                    account_id = account.get("accountId")
                    balance = None
                    
                    # Попытаться получить баланс
                    try:
                        balance_response = await http_client.get(
                            f"{bank.api_url}/accounts/{account_id}/balances",
                            headers={
                                "Authorization": f"Bearer {token}",
                                "x-consent-id": consent_id,
                                "x-requesting-bank": config.BANK_CODE,
                                "accept": "application/json"
                            }
                        )
                        
                        if balance_response.status_code == 200:
                            balance_data = balance_response.json()
                            balance_list = balance_data.get("data", {}).get("balance", [])
                            if balance_list:
                                balance = balance_list[0].get("amount", {}).get("amount")
                    except Exception as e:
                        logger.warning(f"Failed to get balance for account {account_id} from {bank.code}: {e}")
                    
                    accounts.append({
                        "bank_code": bank.code,
                        "bank_name": bank.name or bank.code,
                        "account": account,
                        "balance": balance,
                        "error": None
                    })
            elif response.status_code == 403:
                # Согласие недействительно
                error_text = response.text[:200] if response.text else "Consent invalid"
                logger.warning(f"Consent {consent_id} invalid for {bank.code}: {error_text}")
                accounts.append({
                    "bank_code": bank.code,
                    "bank_name": bank.name or bank.code,
                    "account": None,
                    "balance": None,
                    "error": "CONSENT_REQUIRED"
                })
            else:
                # Другая ошибка
                error_text = response.text[:200] if response.text else "Unknown error"
                logger.error(f"Failed to get accounts from {bank.code}: HTTP {response.status_code}: {error_text}")
                accounts.append({
                    "bank_code": bank.code,
                    "bank_name": bank.name or bank.code,
                    "account": None,
                    "balance": None,
                    "error": f"HTTP {response.status_code}"
                })
        finally:
            if should_close_client:
                await http_client.aclose()
    except httpx.TimeoutException:
        logger.error(f"Timeout when getting accounts from {bank.code}")
        accounts.append({
            "bank_code": bank.code,
            "bank_name": bank.name or bank.code,
            "account": None,
            "balance": None,
            "error": "Timeout"
        })
    except httpx.RequestError as e:
        logger.error(f"Request error when getting accounts from {bank.code}: {e}")
        accounts.append({
            "bank_code": bank.code,
            "bank_name": bank.name or bank.code,
            "account": None,
            "balance": None,
            "error": f"Connection error: {str(e)[:100]}"
        })
    except Exception as e:
        logger.error(f"Unexpected error when getting accounts from {bank.code}: {e}")
        accounts.append({
            "bank_code": bank.code,
            "bank_name": bank.name or bank.code,
            "account": None,
            "balance": None,
            "error": f"Error: {str(e)[:100]}"
        })
    
    return accounts


async def get_external_accounts_for_client(
    client_person_id: str,
    db: AsyncSession,
    app_state_tokens: dict
) -> List[Dict]:
    """
    Получить счета клиента из всех внешних банков
    
    Args:
        client_person_id: ID клиента (person_id)
        db: Database session
        app_state_tokens: Словарь с токенами внешних банков из app.state.tokens
                         Формат: {bank_code: {"token": str, "expires_in": int, "expiration_time": datetime}}
    
    Returns:
        List[Dict]: Список счетов с информацией о банке
                   Формат: [{"bank_code": "...", "bank_name": "...", "account": {...}, "balance": "...", "error": None}, ...]
    """
    accounts = []
    
    # Получить все внешние банки
    result = await db.execute(
        select(Bank).where(Bank.external.is_(True))
    )
    external_banks = result.scalars().all()
    
    if not external_banks:
        logger.info("No external banks found")
        return accounts
    
    # Для каждого внешнего банка получить счета
    for bank in external_banks:
        if not bank.code or not bank.api_url:
            logger.warning(f"Skipping bank {bank.code or 'unknown'}: missing code or api_url")
            continue
        
        # Получить токен для банка
        bank_token_info = app_state_tokens.get(bank.code, {})
        token = bank_token_info.get("token")
        
        if not token:
            logger.warning(f"No token available for bank {bank.code}")
            accounts.append({
                "bank_code": bank.code,
                "bank_name": bank.name or bank.code,
                "account": None,
                "balance": None,
                "error": "Token not available"
            })
            continue
        
        try:
            # Получить существующее согласие из таблицы Consent
            consent_result = await db.execute(
                select(Consent).where(
                    and_(
                        Consent.client_id_external == client_person_id,
                        Consent.bank_id == bank.id,
                        Consent.status == "active"
                    )
                )
            )
            consent = consent_result.scalar_one_or_none()
            consent_id = None
            
            if consent:
                consent_id = consent.consent_id
                logger.info(f"Found existing consent {consent_id} for client {client_person_id} and bank {bank.code}")
            else:
                # Запросить новое согласие у внешнего банка
                logger.info(f"No consent found for client {client_person_id} and bank {bank.code}, requesting new consent")
                consent_id = await request_consent_from_external_bank(bank, client_person_id, token, db)
            
            if not consent_id:
                accounts.append({
                    "bank_code": bank.code,
                    "bank_name": bank.name or bank.code,
                    "account": None,
                    "balance": None,
                    "error": "CONSENT_REQUIRED"
                })
                continue
            
            # Запрос счетов к внешнему банку с использованием consent
            bank_accounts = await get_accounts_from_external_bank(bank, client_person_id, token, consent_id)
            
            # Проверить, есть ли ошибка CONSENT_REQUIRED (403)
            if bank_accounts and len(bank_accounts) == 1 and bank_accounts[0].get("error") == "CONSENT_REQUIRED":
                # Согласие недействительно, обновить статус и запросить новое
                logger.warning(f"Consent {consent_id} failed for {bank.code}, updating status and requesting new consent")
                if consent:
                    consent.status = "expired"
                    consent.status_update_date_time = datetime.utcnow()
                    await db.commit()
                
                # Запросить новое согласие и повторить запрос счетов
                async with httpx.AsyncClient(timeout=10.0) as retry_client:
                    new_consent_id = await request_consent_from_external_bank(bank, client_person_id, token, db, retry_client)
                    
                    if new_consent_id:
                        # Повторить запрос счетов с новым согласием
                        bank_accounts = await get_accounts_from_external_bank(bank, client_person_id, token, new_consent_id, retry_client)
                        accounts.extend(bank_accounts)
                    else:
                        # Не удалось получить новое согласие
                        accounts.append({
                            "bank_code": bank.code,
                            "bank_name": bank.name or bank.code,
                            "account": None,
                            "balance": None,
                            "error": "CONSENT_REQUIRED"
                        })
            else:
                # Успешно получены счета или другая ошибка
                accounts.extend(bank_accounts)
        
        except httpx.TimeoutException:
            logger.error(f"Timeout when getting accounts from {bank.code}")
            accounts.append({
                "bank_code": bank.code,
                "bank_name": bank.name or bank.code,
                "account": None,
                "balance": None,
                "error": "Timeout"
            })
        except httpx.RequestError as e:
            logger.error(f"Request error when getting accounts from {bank.code}: {e}")
            accounts.append({
                "bank_code": bank.code,
                "bank_name": bank.name or bank.code,
                "account": None,
                "balance": None,
                "error": f"Connection error: {str(e)[:100]}"
            })
        except Exception as e:
            logger.error(f"Unexpected error when getting accounts from {bank.code}: {e}")
            accounts.append({
                "bank_code": bank.code,
                "bank_name": bank.name or bank.code,
                "account": None,
                "balance": None,
                "error": f"Error: {str(e)[:100]}"
            })
    
    return accounts

