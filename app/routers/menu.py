from fastapi import APIRouter

from app import store
from app.models import MenuItem

router = APIRouter(prefix="/api/menu", tags=["menu"])


@router.get("", response_model=list[MenuItem])
def list_menu() -> list[MenuItem]:
    return store.get_menu_items()


@router.get("/categories", response_model=list[str])
def list_categories() -> list[str]:
    return store.get_categories()
