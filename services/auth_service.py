"""
Сервис авторизации клиентов и банков
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pathlib import Path
import httpx
from sqlalchemy import select

from config import config
from models import Bank
from database import get_db

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Bearer token scheme
security = HTTPBearer()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None, use_rs256: bool = False):
    """Создание JWT токена (HS256 или RS256)"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
    # Для bank tokens используем RS256
    if use_rs256:
        try:
            # Загрузить приватный ключ
            keys_path = Path(__file__).parent.parent.parent.parent / "shared" / "keys"
            private_key_path = keys_path / f"{config.BANK_CODE}_private.pem"
            
            if not private_key_path.exists():
                # Fallback to HS256 if key not found
                encoded_jwt = jwt.encode(to_encode, config.SECRET_KEY, algorithm=config.ALGORITHM)
                return encoded_jwt
            
            with open(private_key_path, 'r') as f:
                private_key = f.read()
            
            # Добавить kid (key ID) в header
            headers = {"kid": f"{config.BANK_CODE}-2025"}
            encoded_jwt = jwt.encode(to_encode, private_key, algorithm="RS256", headers=headers)
            return encoded_jwt
        except Exception as e:
            print(f"Warning: Failed to load RSA key, falling back to HS256: {e}")
            # Fallback to HS256
            encoded_jwt = jwt.encode(to_encode, config.SECRET_KEY, algorithm=config.ALGORITHM)
            return encoded_jwt
    else:
        # Для client tokens используем HS256
        encoded_jwt = jwt.encode(to_encode, config.SECRET_KEY, algorithm=config.ALGORITHM)
        return encoded_jwt


async def verify_token(token: str, bank_code: Optional[str] = None) -> dict:
    """Проверка JWT токена (HS256 или RS256)"""
    try:
        # Сначала пробуем HS256
        try:
            payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
            return payload
        except JWTError:
            pass
        
        # Если не получилось и указан bank_code, пробуем RS256
        if bank_code:
            try:
                payload = await verify_rs256_token(token, bank_code)
                return payload
            except Exception:
                pass
        
        raise JWTError("Token validation failed")
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )


async def verify_rs256_token(token: str, bank_code: str) -> dict:
    """Проверка RS256 токена через JWKS"""
    try:
        # Попробовать загрузить JWKS из локального файла
        keys_path = Path(__file__).parent.parent.parent.parent / "shared" / "keys"
        public_key_path = keys_path / f"{bank_code}_public.pem"
        
        if public_key_path.exists():
            with open(public_key_path, 'r') as f:
                public_key = f.read()
            
            payload = jwt.decode(token, public_key, algorithms=["RS256"])
            return payload
        
        # Альтернативно: загрузить JWKS через HTTP
        async with httpx.AsyncClient() as client:
            # Определить base URL банка
            bank_ports = {"vbank": 8001, "abank": 8002, "sbank": 8003}
            port = bank_ports.get(bank_code, 8001)
            
            jwks_url = f"http://localhost:{port}/.well-known/jwks.json"
            response = await client.get(jwks_url, timeout=5.0)
            
            if response.status_code == 200:
                jwks = response.json()
                # Используем первый ключ из JWKS
                if jwks.get("keys"):
                    # Для упрощения используем первый ключ
                    # В production нужно искать по kid
                    key = jwks["keys"][0]
                    # jwt.decode автоматически обработает JWKS
                    payload = jwt.decode(token, key, algorithms=["RS256"])
                    return payload
        
        raise JWTError("Failed to verify RS256 token")
        
    except Exception as e:
        print(f"RS256 verification failed: {e}")
        raise JWTError("RS256 verification failed")


async def get_current_client(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Optional[dict]:
    """
    Dependency для получения текущего клиента из JWT токена
    """
    token = credentials.credentials
    payload = await verify_token(token)
    
    if payload.get("type") != "client":
        return None
    
    return {
        "client_id": payload.get("sub"),
        "type": "client"
    }


async def get_current_bank(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Optional[dict]:
    """
    Dependency для получения текущего банка из JWT токена (межбанковские запросы)
    
    Принимает:
    - type="bank" - межбанковый токен
    - type="team" - токен команды (bank-token, выданный банком)
    """
    token = credentials.credentials
    # Team токены используют HS256, bank_code не нужен
    payload = await verify_token(token)
    
    # Принимаем и "bank" и "team" токены (team = токен банка для команды)
    if payload.get("type") not in ["bank", "team"]:
        return None
    
    return {
        "bank_code": payload.get("sub"),  # для team это client_id (team200)
        "client_id": payload.get("client_id"),  # для team токенов
        "type": payload.get("type")
    }


async def get_optional_client(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[dict]:
    """
    Optional dependency - не выбрасывает ошибку если токена нет
    """
    if not credentials:
        return None
    
    try:
        payload = await verify_token(credentials.credentials)
        if payload.get("type") == "client":
            return {
                "client_id": payload.get("sub"),
                "type": "client"
            }
    except:
        return None
    
    return None


async def get_current_banker(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Optional[dict]:
    """
    Получить текущего банкира из токена
    Возвращает None если не авторизован или не банкир
    """
    if not credentials:
        return None
    
    try:
        payload = await verify_token(credentials.credentials)
        if payload.get("type") == "banker":
            return {
                "username": payload.get("sub"),
                "type": "banker"
            }
    except:
        return None
    
    return None


def hash_password(password: str) -> str:
    """Хеширование пароля"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверка пароля"""
    return pwd_context.verify(plain_password, hashed_password)


async def get_access_token(
    team_id: str, client_secret: str, bank_url: str
) -> dict:
    """
    Obtain bank access token for inter-bank operations.
    
    Args:
        team_id: Team identifier (e.g., "team200")
        client_secret: API key for secure requests
        bank_url: Base URL of the bank API
    
    Returns:
        dict: Token response containing access_token, token_type, client_id, expires_in
    """
    async with httpx.AsyncClient(base_url=bank_url, timeout=30.0) as client:
        response = await client.post(
            "/auth/bank-token",
            params={
                "client_id": team_id,
                "client_secret": client_secret
            }
        )
        response.raise_for_status()
        return response.json()


async def get_external_bank_tokens() -> dict:
    """
    Get access tokens for all external banks from the banks table.
    
    Uses get_db() generator for consistency with codebase patterns.
    
    Returns:
        dict: Dictionary with bank_code as keys and token info as values
              Format: {bank_code: {"token": str, "expires_in": int, "expiration_time": datetime}}
              On failure: {bank_code: {"token": None, "expires_in": None, "expiration_time": None}}
    """
    tokens = {}
    
    # Use get_db() generator for consistency with codebase (like in middleware.py)
    async for db in get_db():
        # Query all external banks
        result = await db.execute(
            select(Bank).where(Bank.external.is_(True))
        )
        external_banks = result.scalars().all()
        
        # Get token for each external bank
        for bank in external_banks:
            if not bank.code or not bank.api_url or not bank.api_user or not bank.api_secret:
                # Skip banks with missing required fields
                tokens[bank.code] = {
                    "token": None,
                    "expires_in": None,
                    "expiration_time": None
                }
                continue
            
            try:
                token_response = await get_access_token(
                    team_id=bank.api_user,
                    client_secret=bank.api_secret,
                    bank_url=bank.api_url
                )
                
                expires_in = token_response.get("expires_in", 86400)
                expiration_time = datetime.utcnow() + timedelta(seconds=expires_in)
                
                tokens[bank.code] = {
                    "token": token_response.get("access_token"),
                    "expires_in": expires_in,
                    "expiration_time": expiration_time
                }
            except Exception as e:
                print(f"Failed to get token for bank {bank.code}: {e}")
                tokens[bank.code] = {
                    "token": None,
                    "expires_in": None,
                    "expiration_time": None
                }
        break  # Only need one iteration since get_db() yields one session
    
    return tokens

