# app/services/ai/__init__.py
from .router import ImageRouter
from .specialist import GroqSpecialist

_router = None
_specialist = None

def get_image_router():
    global _router
    if _router is None:
        _router = ImageRouter()
    return _router

def get_specialist_ai():
    global _specialist
    if _specialist is None:
        _specialist = GroqSpecialist()
    return _specialist