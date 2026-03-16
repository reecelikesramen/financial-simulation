from pywire import PyWire
from auth_middleware import create_app_with_middleware

app = create_app_with_middleware(PyWire(enable_pjax=True, debug=True))
