from fastapi import APIRouter, Request

from smartdrive.application.services.dashboard_service import get_dashboard_system_stats
from smartdrive.application.services.portfolio_service import get_portfolio_writeups
from smartdrive.infrastructure.templates import templates


router = APIRouter()


def render_portfolio_page(request: Request):
    return templates.TemplateResponse(
        "portfolio.html",
        {
            "request": request,
            "writeups_data": get_portfolio_writeups(),
        },
    )


@router.get("/")
def portfolio_home(request: Request):
    return render_portfolio_page(request)


@router.get("/portfolio")
def portfolio_alias(request: Request):
    return render_portfolio_page(request)


@router.get("/dashboard")
def dashboard_home(request: Request):
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
        },
    )


@router.get("/dashboard/system-stats")
def dashboard_system_stats():
    return get_dashboard_system_stats()
