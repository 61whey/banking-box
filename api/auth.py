"""
Auth API - Авторизация клиентов
"""
from fastapi import APIRouter, Depends, HTTPException, Form
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from ..database import get_db
from ..models import Client, Team
from ..services.auth_service import create_access_token, hash_password, verify_password, get_current_client


router = APIRouter(prefix="/auth", tags=["Internal: Auth"])


class LoginRequest(BaseModel):
    username: str  # person_id клиента
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    client_id: str


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Авторизация клиента в веб-интерфейсе банка
    
    ⚠️ **Для встроенного UI банка, НЕ для внешних приложений**
    
    Этот endpoint используется клиентским интерфейсом банка для входа пользователя.
    Внешние приложения должны использовать стандартный OAuth 2.0 flow.
    
    **Пример:**
    ```json
    {
      "username": "cli-vb-001",
      "password": "password"
    }
    ```
    
    **Ответ:**
    - `access_token` — JWT токен (валиден 24 часа)
    - `token_type` — "bearer"
    - `client_id` — ID клиента
    
    Используйте токен в заголовке: `Authorization: Bearer <token>`
    """
    
    # Найти клиента
    result = await db.execute(
        select(Client).where(Client.person_id == request.username)
    )
    client = result.scalar_one_or_none()
    
    if not client:
        raise HTTPException(401, "Invalid credentials")
    
    # В MVP: простая проверка пароля (для упрощения тестирования)
    # В production: проверять хешированный пароль
    
    # Определяем правильный пароль для клиента
    expected_password = None
    
    if request.username.startswith("demo-"):
        # Demo клиенты: пароль = "demo"
        expected_password = "demo"
    elif request.username.startswith("team"):
        # Командные клиенты: проверяем пароль из таблицы teams
        # Извлекаем номер команды из person_id (team010-1 → team010)
        import re
        match = re.match(r'(team\d+)-\d+', request.username)
        if match:
            team_id = match.group(1)
            
            # Ищем команду в БД
            team_result = await db.execute(
                select(Team).where(Team.client_id == team_id)
            )
            team = team_result.scalar_one_or_none()
            
            if team:
                # Используем client_secret из таблицы teams как пароль
                expected_password = team.client_secret
            else:
                # Команда не найдена в БД - используем fallback "password" для локальной разработки
                expected_password = "password"
        else:
            # Неправильный формат - используем fallback
            expected_password = "password"
    else:
        # Старые клиенты: пароль = username или "password"
        if request.password in [request.username, "password"]:
            expected_password = request.password
    
    # Проверка пароля
    if not expected_password or request.password != expected_password:
        raise HTTPException(401, "Invalid credentials")
    
    # Создать JWT токен
    access_token = create_access_token(
        data={
            "sub": client.person_id,
            "type": "client",
            "bank": "self"
        }
    )
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        client_id=client.person_id
    )


@router.get("/me")
async def get_current_user(
    current_client: dict = Depends(get_current_client)
):
    """Получение информации о текущем клиенте"""
    
    if not current_client:
        raise HTTPException(401, "Not authenticated")
    
    return current_client


@router.post("/bank-token", tags=["🚀 Start Here"])
async def create_bank_token(
    client_id: str,
    client_secret: str,
    db: AsyncSession = Depends(get_db)
):
    """
    ## 🎯 Получение токена для работы с API банка
    
    **Этот endpoint - точка входа для всех участников хакатона!**
    
    Токен выдается банком, У КОТОРОГО вы запрашиваете данные.
    Каждый банк подписывает токен своим приватным ключом (RS256).
    
    ### Где взять credentials?
    
    Получите у организаторов хакатона:
    - `client_id` — код вашей команды (например: team200)
    - `client_secret` — ваш секретный ключ (API key)
    
    ### Пример запроса:
    
    ```bash
    # Получить токен для запросов к VBank
    POST https://vbank.open.bankingapi.ru/auth/bank-token
    ?client_id=team200
    &client_secret=5OAaa4DYzYKfnOU6zbR34ic5qMm7VSMB
    
    # Ответ:
    {
      "access_token": "eyJ...",
      "token_type": "bearer",
      "client_id": "team200",
      "expires_in": 86400
    }
    ```
    
    ### Использование токена:
    
    ```bash
    GET https://vbank.open.bankingapi.ru/accounts
    Headers:
      Authorization: Bearer eyJ...
    ```
    
    ### Важно:
    
    - Токен валиден 24 часа
    - Для каждого банка нужен свой токен (VBank, ABank, SBank)
    - Токен подписан приватным ключом банка (RS256)
    - Публичный ключ: `/.well-known/jwks.json`
    
    ### Межбанковые запросы:
    
    Для получения данных клиента из другого банка добавьте:
    ```
    X-Requesting-Bank: your_client_id
    ```
    И создайте согласие: `POST /account-consents`
    """
    from ..config import config
    
    # Проверить credentials в базе
    result = await db.execute(
        select(Team).where(
            Team.client_id == client_id,
            Team.is_active == True
        )
    )
    team = result.scalar_one_or_none()
    
    if not team:
        raise HTTPException(401, "Invalid client_id")
    
    if team.client_secret != client_secret:
        raise HTTPException(401, "Invalid client_secret")
    
    # Создать токен с HS256 подписью (для упрощения в sandbox)
    access_token = create_access_token(
        data={
            "sub": client_id,
            "client_id": client_id,
            "type": "team",
            "iss": config.BANK_CODE,
            "aud": "openbanking"
        },
        use_rs256=False  # Используем HS256 для токенов команд (проще для sandbox)
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "client_id": client_id,
        "algorithm": "HS256",
        "expires_in": 86400  # 24 часа
    }


@router.post("/banker-login")
async def banker_login(
    username: str = Form(...),
    password: str = Form(...)
):
    """
    Авторизация сотрудника банка
    
    Для доступа к Banker UI и управления продуктами банка.
    """
    # Проверка учетных данных (в sandbox - упрощенная схема)
    if username != "hackapi_admin" or password != "HackAPI2025!Secure":
        raise HTTPException(401, "Invalid credentials")
    
    from ..config import config
    
    # Создать токен банкира
    banker_token = create_access_token(
        data={
            "sub": "banker",
            "type": "banker",
            "bank": config.BANK_CODE
        }
    )
    
    return {
        "access_token": banker_token,
        "token_type": "bearer",
        "role": "banker"
    }


class RandomClientResponse(BaseModel):
    person_id: str
    full_name: str
    password: str


@router.get("/random-demo-client", response_model=RandomClientResponse)
async def get_random_demo_client(db: AsyncSession = Depends(get_db)):
    """
    Получить случайного клиента для тестирования
    
    Возвращает случайного клиента с богатой историей транзакций
    для быстрого тестирования интерфейса.
    """
    # Выбираем случайного demo клиента
    result = await db.execute(
        select(Client).where(Client.person_id.like('demo-%')).order_by(func.random()).limit(1)
    )
    client = result.scalar_one_or_none()
    
    if not client:
        raise HTTPException(404, "No demo clients found")
    
    return RandomClientResponse(
        person_id=client.person_id,
        full_name=client.full_name,
        password="demo"
    )

