from pywire import PyWire
from auth_middleware import auth_middleware_stack

app = PyWire(
    enable_pjax=True,
    debug=True,
    middleware=auth_middleware_stack(),
)
