import os
from context import current_user_id
from starlette.middleware.sessions import SessionMiddleware


class AuthMiddleware:
    """Reads user_id from the session (populated by SessionMiddleware) and
    stores it in a ContextVar so any .wire file can read it via import."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        session = scope.get("session", {})
        token = current_user_id.set(session.get("user_id", "dev-user-hardcoded"))
        try:
            await self.app(scope, receive, send)
        finally:
            current_user_id.reset(token)


def auth_middleware_stack():
    """Return the middleware list to pass to PyWire(middleware=...).

    Order: outermost first. SessionMiddleware must wrap AuthMiddleware so
    scope['session'] is populated before AuthMiddleware reads it.
    """
    return [
        (
            SessionMiddleware,
            {
                "secret_key": os.environ.get(
                    "SECRET_KEY", "dev-secret-change-in-production"
                ),
                "https_only": False,
                "max_age": 60 * 60 * 24 * 30,
            },
        ),
        AuthMiddleware,
    ]
