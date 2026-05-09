import jwt
from jwt import ExpiredSignatureError, InvalidTokenError
from fastapi import HTTPException
from app.config import settings


class AuthenticatedUser:
    """Простой объект пользователя для FastAPI"""

    def __init__(self, telegram_id: int):
        self.telegram_id = telegram_id
        self.is_authenticated = True

    def __repr__(self):
        return f"AuthenticatedUser(telegram_id={self.telegram_id})"


class JWTAuthenticator:
    """Класс для проверки JWT токена (аналог JWTAuthTgUser из Diary Service)"""

    @staticmethod
    def verify_token(token: str) -> AuthenticatedUser:
        """
        Проверяет JWT токен и возвращает пользователя

        Args:
            token: JWT токен из заголовка Authorization

        Returns:
            AuthenticatedUser с telegram_id

        Raises:
            HTTPException: При проблемах с токеном
        """
        try:
            # Декодируем токен с тем же ключом, что и Auth Service
            payload = jwt.decode(
                token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
            )

            # Извлекаем telegram_id
            telegram_id = payload.get("telegram_id")

            # Проверяем валидность telegram_id
            if not telegram_id:
                raise HTTPException(
                    status_code=401, detail="Telegram ID отсутствует в токене"
                )

            if not isinstance(telegram_id, int):
                raise HTTPException(
                    status_code=401, detail="Некорректный формат telegram_id в токене"
                )

            return AuthenticatedUser(telegram_id)

        except ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Срок действия токена истёк")
        except InvalidTokenError as e:
            raise HTTPException(status_code=401, detail=f"Некорректный токен: {str(e)}")
        except Exception as e:
            raise HTTPException(
                status_code=401, detail=f"Ошибка аутентификации: {str(e)}"
            )
