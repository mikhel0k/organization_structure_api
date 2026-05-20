from app.routes.departments import router
from app.routes.handlers import register_exception_handlers

__all__ = ["register_exception_handlers", "router"]
