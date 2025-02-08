#server\app\api\v1\endpoints\web\__init__.py
from fastapi import APIRouter

router = APIRouter()

# Exportar el router
__all__ = ["router"]