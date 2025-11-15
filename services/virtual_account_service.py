"""
Сервис для работы с виртуальными счетами
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional, Dict
from datetime import datetime
from decimal import Decimal
import random
import string

from models import VirtualAccount
from log import logger


def generate_account_number() -> str:
    """
    Генерация уникального номера виртуального счета
    Формат: VA + timestamp(10 digits) + random(6 digits)

    Returns:
        str: Уникальный номер счета (длина: 18 символов)
    """
    timestamp_part = str(int(datetime.utcnow().timestamp()))[-10:]  # Last 10 digits of timestamp
    random_part = ''.join(random.choices(string.digits, k=6))
    account_number = f"VA{timestamp_part}{random_part}"

    logger.info(f"Generated virtual account number: {account_number}")
    return account_number


async def create_virtual_account(
    client_id: int,
    account_type: str,
    calculation_type: str,
    balance: Optional[Decimal],
    currency: str,
    db: AsyncSession
) -> VirtualAccount:
    """
    Создать новый виртуальный счет

    Args:
        client_id: ID клиента
        account_type: Тип счета (checking, savings)
        calculation_type: Тип расчета (automatic, fixed)
        balance: Баланс (обязателен для fixed, игнорируется для automatic)
        currency: Валюта счета
        db: Database session

    Returns:
        VirtualAccount: Созданный виртуальный счет

    Raises:
        ValueError: Если параметры невалидны
    """
    # Validation
    valid_account_types = ["checking", "savings"]
    valid_calculation_types = ["automatic", "fixed"]
    valid_currencies = ["RUB"]

    if account_type not in valid_account_types:
        logger.warning(f"Invalid account_type: {account_type}, expected one of {valid_account_types}")
        raise ValueError(f"account_type must be one of: {', '.join(valid_account_types)}")

    if calculation_type not in valid_calculation_types:
        logger.warning(f"Invalid calculation_type: {calculation_type}, expected one of {valid_calculation_types}")
        raise ValueError(f"calculation_type must be one of: {', '.join(valid_calculation_types)}")

    if currency not in valid_currencies:
        logger.warning(f"Invalid currency: {currency}, expected one of {valid_currencies}")
        raise ValueError(f"currency must be one of: {', '.join(valid_currencies)}")

    # For fixed calculation type, balance is required
    if calculation_type == "fixed" and balance is None:
        logger.warning(f"Balance is required for fixed calculation_type")
        raise ValueError("balance is required when calculation_type is 'fixed'")

    # For automatic calculation type, balance should be 0 or None
    if calculation_type == "automatic":
        balance = Decimal("0.00")

    logger.info(
        f"Creating virtual account for client {client_id}: "
        f"type={account_type}, calc_type={calculation_type}, balance={balance}, currency={currency}"
    )

    try:
        # Generate unique account number
        account_number = generate_account_number()

        # Ensure uniqueness (very unlikely to collide, but check anyway)
        max_retries = 5
        for attempt in range(max_retries):
            existing = await db.execute(
                select(VirtualAccount).where(VirtualAccount.account_number == account_number)
            )
            if existing.scalar_one_or_none() is None:
                break
            logger.warning(f"Account number {account_number} already exists, generating new one (attempt {attempt + 1}/{max_retries})")
            account_number = generate_account_number()

        # Create virtual account
        virtual_account = VirtualAccount(
            client_id=client_id,
            account_number=account_number,
            account_type=account_type,
            calculation_type=calculation_type,
            balance=balance,
            currency=currency,
            status="active",
            created_at=datetime.utcnow()
        )

        db.add(virtual_account)
        await db.commit()
        await db.refresh(virtual_account)

        logger.info(
            f"Virtual account {account_number} created successfully: "
            f"id={virtual_account.id}, client_id={client_id}, type={account_type}"
        )

        return virtual_account

    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating virtual account for client {client_id}: {e}", exc_info=True)
        raise


async def get_virtual_accounts_for_client(
    client_id: int,
    db: AsyncSession
) -> List[VirtualAccount]:
    """
    Получить все виртуальные счета для клиента

    Args:
        client_id: ID клиента
        db: Database session

    Returns:
        List[VirtualAccount]: Список виртуальных счетов
    """
    logger.info(f"Fetching virtual accounts for client_id={client_id}")

    try:
        result = await db.execute(
            select(VirtualAccount)
            .where(VirtualAccount.client_id == client_id)
            .order_by(VirtualAccount.created_at.desc())
        )
        accounts = result.scalars().all()

        logger.info(f"Found {len(accounts)} virtual accounts for client_id={client_id}")
        return list(accounts)

    except Exception as e:
        logger.error(f"Error fetching virtual accounts for client {client_id}: {e}", exc_info=True)
        raise


async def get_virtual_account_by_id(
    account_id: int,
    client_id: int,
    db: AsyncSession
) -> Optional[VirtualAccount]:
    """
    Получить виртуальный счет по ID

    Args:
        account_id: ID виртуального счета
        client_id: ID клиента (для проверки авторизации)
        db: Database session

    Returns:
        Optional[VirtualAccount]: Виртуальный счет или None
    """
    logger.info(f"Fetching virtual account id={account_id} for client_id={client_id}")

    try:
        result = await db.execute(
            select(VirtualAccount).where(
                and_(
                    VirtualAccount.id == account_id,
                    VirtualAccount.client_id == client_id
                )
            )
        )
        account = result.scalar_one_or_none()

        if account:
            logger.info(f"Found virtual account: id={account_id}, account_number={account.account_number}")
        else:
            logger.warning(f"Virtual account id={account_id} not found for client_id={client_id}")

        return account

    except Exception as e:
        logger.error(f"Error fetching virtual account {account_id}: {e}", exc_info=True)
        raise


async def update_virtual_account(
    account_id: int,
    client_id: int,
    account_type: Optional[str],
    calculation_type: Optional[str],
    balance: Optional[Decimal],
    currency: Optional[str],
    status: Optional[str],
    db: AsyncSession
) -> Optional[VirtualAccount]:
    """
    Обновить виртуальный счет

    Args:
        account_id: ID виртуального счета
        client_id: ID клиента (для проверки авторизации)
        account_type: Новый тип счета (optional)
        calculation_type: Новый тип расчета (optional)
        balance: Новый баланс (optional)
        currency: Новая валюта (optional)
        status: Новый статус (optional)
        db: Database session

    Returns:
        Optional[VirtualAccount]: Обновленный виртуальный счет или None

    Raises:
        ValueError: Если параметры невалидны
    """
    logger.info(f"Updating virtual account id={account_id} for client_id={client_id}")

    try:
        # Fetch existing account
        account = await get_virtual_account_by_id(account_id, client_id, db)
        if not account:
            logger.warning(f"Cannot update: virtual account id={account_id} not found for client_id={client_id}")
            return None

        # Track changes for logging
        changes = []

        # Update account_type if provided
        if account_type is not None:
            valid_account_types = ["checking", "savings"]
            if account_type not in valid_account_types:
                logger.warning(f"Invalid account_type: {account_type}")
                raise ValueError(f"account_type must be one of: {', '.join(valid_account_types)}")
            if account.account_type != account_type:
                changes.append(f"account_type: {account.account_type} -> {account_type}")
                account.account_type = account_type

        # Update calculation_type if provided
        if calculation_type is not None:
            valid_calculation_types = ["automatic", "fixed"]
            if calculation_type not in valid_calculation_types:
                logger.warning(f"Invalid calculation_type: {calculation_type}")
                raise ValueError(f"calculation_type must be one of: {', '.join(valid_calculation_types)}")
            if account.calculation_type != calculation_type:
                changes.append(f"calculation_type: {account.calculation_type} -> {calculation_type}")
                account.calculation_type = calculation_type

                # If changing to automatic, reset balance to 0
                if calculation_type == "automatic":
                    if account.balance != Decimal("0.00"):
                        changes.append(f"balance: {account.balance} -> 0.00 (automatic)")
                        account.balance = Decimal("0.00")

        # Update balance if provided
        if balance is not None:
            if account.calculation_type == "fixed" or (calculation_type == "fixed"):
                if account.balance != balance:
                    changes.append(f"balance: {account.balance} -> {balance}")
                    account.balance = balance
            else:
                logger.warning(f"Cannot set balance for automatic calculation_type")

        # Update currency if provided
        if currency is not None:
            valid_currencies = ["RUB"]
            if currency not in valid_currencies:
                logger.warning(f"Invalid currency: {currency}")
                raise ValueError(f"currency must be one of: {', '.join(valid_currencies)}")
            if account.currency != currency:
                changes.append(f"currency: {account.currency} -> {currency}")
                account.currency = currency

        # Update status if provided
        if status is not None:
            valid_statuses = ["active", "inactive", "closed"]
            if status not in valid_statuses:
                logger.warning(f"Invalid status: {status}")
                raise ValueError(f"status must be one of: {', '.join(valid_statuses)}")
            if account.status != status:
                changes.append(f"status: {account.status} -> {status}")
                account.status = status

        # Update timestamp
        account.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(account)

        if changes:
            logger.info(f"Updated virtual account {account.account_number}: {', '.join(changes)}")
        else:
            logger.info(f"No changes made to virtual account {account.account_number}")

        return account

    except ValueError:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating virtual account {account_id}: {e}", exc_info=True)
        raise


async def delete_virtual_account(
    account_id: int,
    client_id: int,
    db: AsyncSession
) -> bool:
    """
    Удалить виртуальный счет

    Args:
        account_id: ID виртуального счета
        client_id: ID клиента (для проверки авторизации)
        db: Database session

    Returns:
        bool: True если удален, False если не найден
    """
    logger.info(f"Deleting virtual account id={account_id} for client_id={client_id}")

    try:
        # Fetch existing account
        account = await get_virtual_account_by_id(account_id, client_id, db)
        if not account:
            logger.warning(f"Cannot delete: virtual account id={account_id} not found for client_id={client_id}")
            return False

        account_number = account.account_number

        await db.delete(account)
        await db.commit()

        logger.info(f"Deleted virtual account {account_number} (id={account_id}) for client_id={client_id}")
        return True

    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting virtual account {account_id}: {e}", exc_info=True)
        raise
