from fastapi import Depends, HTTPException, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from .services.auth import JWTAuthenticator, AuthenticatedUser

# Схема безопасности для Swagger UI
security_scheme = HTTPBearer(
    scheme_name="JWT",
    description="Введите JWT токен от Auth Service. Формат: Bearer <токен>",
    bearerFormat="JWT",
)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
) -> AuthenticatedUser:
    """
    Зависимость для получения текущего пользователя из JWT токена.

    Использование в эндпоинтах:
        @router.post("/analysis")
        async def create_analysis(
            current_user: AuthenticatedUser = Depends(get_current_user)
        ):
            # current_user.telegram_id содержит ID пользователя
            ...
    """
    token = credentials.credentials
    return JWTAuthenticator.verify_token(token)


async def get_token_from_header(authorization: Optional[str] = Header(None)) -> str:
    """
    Получает JWT токен из заголовка Authorization для проброса в другие сервисы.

    Возвращает чистый токен без префикса 'Bearer'.
    Используется, когда нужно передать токен дальше (в Diary Service).
    """
    if not authorization:
        raise HTTPException(
            status_code=401, detail="Отсутствует заголовок Authorization"
        )

    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=401, detail="Неверный формат токена. Ожидается Bearer"
            )
        return token
    except ValueError:
        raise HTTPException(
            status_code=401, detail="Некорректный формат заголовка Authorization"
        )
