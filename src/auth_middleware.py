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
        token = current_user_id.set(session.get("user_id"))
        try:
            await self.app(scope, receive, send)
        finally:
            current_user_id.reset(token)


class _AppWithMiddleware:
    """Proxies PyWire attributes (e.g. pages_dir) while routing ASGI calls
    through the middleware stack."""

    def __init__(self, pywire_app):
        self._pywire = pywire_app
        self._middleware = AuthMiddleware(
            SessionMiddleware(
                pywire_app,
                secret_key=os.environ.get("SECRET_KEY", "dev-secret-change-in-production"),
                https_only=False,
                max_age=60 * 60 * 24 * 30,
            )
        )

    def __getattr__(self, name):
        if name == "app":
            return self._middleware
        return getattr(self._pywire, name)

    async def __call__(self, scope, receive, send):
        await self._middleware(scope, receive, send)


def create_app_with_middleware(pywire_app):
    return _AppWithMiddleware(pywire_app)
