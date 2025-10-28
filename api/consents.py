class ConsentDataRequest(BaseModel):
    """Data для создания согласия"""
    permissions: List[str] = Field(..., description="ReadAccountsDetail, ReadBalances, ReadTransactionsDetail")
    expirationDateTime: Optional[str] = None
    transactionFromDateTime: Optional[str] = None
    transactionToDateTime: Optional[str] = None


class ConsentCreateRequest(BaseModel):
    """Запрос создания согласия (OpenBanking Russia format)"""
    data: ConsentDataRequest
    risk: Optional[dict] = {}


class ConsentData(BaseModel):
    """Данные согласия в ответе"""
    consentId: str
    status: str
    creationDateTime: str
    statusUpdateDateTime: str
    permissions: List[str]
    expirationDateTime: Optional[str] = None


class ConsentResponse(BaseModel):
    """Ответ с согласием"""
    data: ConsentData
    links: dict
    meta: Optional[dict] = {}




# === Межбанковские endpoints (для других банков) ===

class ConsentRequestBody(BaseModel):
    """Body для запроса согласия"""
    client_id: str
    permissions: List[str]
    reason: str = ""
    requesting_bank: str = "test_bank"
    requesting_bank_name: str = "Test Bank"


@router.post("/request")
async def request_consent(
    body: ConsentRequestBody,
    x_requesting_bank: Optional[str] = Header(None, alias="x-requesting-bank"),
    db: AsyncSession = Depends(get_db)
):
    """
    Быстрое создание согласия (упрощённо для хакатона)
    
    **⚠️ ВНИМАНИЕ: Упрощённый endpoint для хакатона**
    
    Это **НЕ** стандартный OpenBanking Russia endpoint!
    Упрощение по сравнению со спецификациями ЦБ/АФТ:
    - Нет OAuth 2.0 Authorization Code Flow
    - Нет редиректов на authorization server
    - Согласие создаётся и авторизуется в один запрос
    
    ### Зачем это сделано?
    
    Для **быстрого старта на хакатоне**. Стандартный OpenBanking flow 
    требует сложную инфраструктуру (OAuth server, редиректы, PKCE).
    Этот endpoint позволяет сразу получить согласие через API.
    
    ### Пример использования:
    
    ```bash
    # 1. Получить токен банка, где лежат данные клиента
    POST http://abank.ru/auth/bank-token
    ?client_id=team200&client_secret=xxx
    → {"access_token": "..."}
    
    # 2. Запросить согласие
    POST http://abank.ru/account-consents/request
    Headers:
      Authorization: Bearer {access_token}
      X-Requesting-Bank: team200
    Body:
    {
      "client_id": "team200-1",
      "permissions": ["ReadAccountsDetail", "ReadBalances"],
      "reason": "Агрегация счетов для HackAPI",
      "requesting_bank": "team200",
      "requesting_bank_name": "Team 200 App"
    }
    
    → {"status": "approved", "consent_id": "...", "auto_approved": true}
    
    # 3. Запросить данные
    GET http://abank.ru/accounts?client_id=team200-1
    Headers:
      Authorization: Bearer {access_token}
      X-Requesting-Bank: team200
    
    → 200 OK {"accounts": [...]}
    ```
    
    ### Что происходит внутри:
    1. Создаётся запрос согласия для клиента
    2. Если `auto_approve_consents=true` (по умолчанию):
       - Согласие одобряется автоматически
       - Можно сразу запрашивать данные
    3. Если `auto_approve_consents=false`:
       - Клиент увидит запрос в своём UI
       - Должен подтвердить через кнопку "Подписать"
       - После этого ваше приложение может запрашивать данные
    
    ### В production:
    - Используйте стандартный OAuth 2.0 Authorization Code Flow
    - `POST /account-consents` → redirect → authorization → callback
    - Этот endpoint не соответствует спецификации АФТ
    """
    # В sandbox режиме: разрешаем запросы для тестирования
    requesting_bank = x_requesting_bank or body.requesting_bank
    requesting_bank_name = body.requesting_bank_name
    
    try:
        consent_request, consent = await ConsentService.create_consent_request(
            db=db,
            client_person_id=body.client_id,
            requesting_bank=requesting_bank,
            requesting_bank_name=requesting_bank_name,
            permissions=body.permissions,
            reason=body.reason
        )
        
        if consent:
            # Автоодобрено
            return {
                "request_id": consent_request.request_id,
                "consent_id": consent.consent_id,
                "status": "approved",
                "message": "Согласие одобрено автоматически",
                "created_at": consent_request.created_at.isoformat(),
                "auto_approved": True
            }
        else:
            # Требуется одобрение
            return {
                "request_id": consent_request.request_id,
                "status": "pending",
                "message": "Запрос отправлен на одобрение",
                "created_at": consent_request.created_at.isoformat(),
                "auto_approved": False
            }
        
    except ValueError as e:
        raise HTTPException(404, str(e))





# === Стандартные OpenBanking endpoints удалены для упрощения ===
# В sandbox используются только упрощённые endpoints выше.
# Стандартный flow требует OAuth infrastructure (сложно для хакатона).
# 
# Упрощения по сравнению со спецификациями ЦБ/АФТ:
# - Нет OAuth 2.0 Authorization Code Flow
# - Нет редиректов и authorization server
# - Согласие создаётся и авторизуется в один запрос


# === Клиентские endpoints (для собственных клиентов) ===

@router.get("/requests", tags=["Internal: Consents"], include_in_schema=False)
async def get_consent_requests(
    current_client: dict = Depends(get_current_client),
    db: AsyncSession = Depends(get_db)
):
    """Получить все запросы на согласие для клиента"""
    if not current_client:
        raise HTTPException(401, "Unauthorized")
    
    # Получить client.id
    client_result = await db.execute(
        select(Client).where(Client.person_id == current_client["client_id"])
    )
    client = client_result.scalar_one_or_none()
    
    if not client:
        raise HTTPException(404, "Client not found")
    
    # Получить pending запросы
    result = await db.execute(
        select(ConsentRequest).where(
            and_(
                ConsentRequest.client_id == client.id,
                ConsentRequest.status == "pending"
            )
        ).order_by(ConsentRequest.created_at.desc())
    )
    requests = result.scalars().all()
    
    return {
        "requests": [
            {
                "request_id": req.request_id,
                "requesting_bank": req.requesting_bank,
                "requesting_bank_name": req.requesting_bank_name,
                "permissions": req.permissions,
                "reason": req.reason,
                "created_at": req.created_at.isoformat(),
                "status": req.status
            }
            for req in requests
        ]
    }


class SignConsentBody(BaseModel):
    """Body для подписания согласия"""
    request_id: str
    action: str  # approve / reject
    signature: str = "password"


@router.post("/sign", tags=["Internal: Consents"], include_in_schema=False)
async def sign_consent(
    body: SignConsentBody,
    current_client: dict = Depends(get_current_client),
    db: AsyncSession = Depends(get_db)
):
    """
    Подписание или отклонение согласия клиентом
    
    Не из стандарта, но необходимо для процесса подписания
    """
    if not current_client:
        raise HTTPException(401, "Unauthorized")
    
    try:
        status, consent = await ConsentService.sign_consent(
            db=db,
            request_id=body.request_id,
            client_person_id=current_client["client_id"],
            action=body.action,
            signature=body.signature
        )
        
        if body.action == "approve" and consent:
            return {
                "consent_id": consent.consent_id,
                "status": consent.status,
                "granted_to": consent.granted_to,
                "permissions": consent.permissions,
                "expires_at": consent.expiration_date_time.isoformat(),
                "signed_at": consent.signed_at.isoformat()
            }
        else:
            return {
                "request_id": body.request_id,
                "status": "rejected"
            }
            
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.get("/my-consents", tags=["Internal: Consents"], include_in_schema=False)
async def get_my_consents(
    current_client: dict = Depends(get_current_client),
    db: AsyncSession = Depends(get_db)
):
    """Получить все активные согласия клиента"""
    if not current_client:
        raise HTTPException(401, "Unauthorized")
    
    client_result = await db.execute(
        select(Client).where(Client.person_id == current_client["client_id"])
    )
    client = client_result.scalar_one_or_none()
    
    if not client:
        raise HTTPException(404, "Client not found")
    
    # Получить все согласия
    result = await db.execute(
        select(Consent).where(Consent.client_id == client.id)
        .order_by(Consent.creation_date_time.desc())
    )
    consents = result.scalars().all()
    
    return {
        "consents": [
            {
                "consent_id": c.consent_id,
                "granted_to": c.granted_to,
                "permissions": c.permissions,
                "status": c.status,
                "signed_at": c.signed_at.isoformat() if c.signed_at else None,
                "expires_at": c.expiration_date_time.isoformat() if c.expiration_date_time else None,
                "last_accessed": c.last_accessed_at.isoformat() if c.last_accessed_at else None
            }
            for c in consents
        ]
    }


@router.delete("/my-consents/{consent_id}", tags=["Internal: Consents"], include_in_schema=False)
async def revoke_consent(
    consent_id: str,
    current_client: dict = Depends(get_current_client),
    db: AsyncSession = Depends(get_db)
):
    """Отозвать согласие"""
    if not current_client:
        raise HTTPException(401, "Unauthorized")
    
    success = await ConsentService.revoke_consent(
        db=db,
        consent_id=consent_id,
        client_person_id=current_client["client_id"]
    )
    
    if not success:
        raise HTTPException(404, "Consent not found or already revoked")
    
    return {
        "consent_id": consent_id,
        "status": "Revoked",
        "revoked_at": datetime.utcnow().isoformat()
    }


