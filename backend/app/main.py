from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import get_settings
from .graphs import coach_graph, humanize_graph
from .schemas import (
    BillingStatusResponse,
    CheckoutRequest,
    CheckoutResponse,
    CoachRequest,
    CoachResponse,
    HumanizeRequest,
    HumanizeResponse,
)
from .services.billing import billing_service


settings = get_settings()
app = FastAPI(title=settings.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_user_id(x_user_id: str | None) -> str:
    return x_user_id or "demo-pro"


@app.post("/api/coach", response_model=CoachResponse)
def coach(
    payload: CoachRequest,
    request: Request,
    x_user_id: str | None = Header(default=None),
) -> CoachResponse:
    user_id = get_user_id(x_user_id)
    client_ip = request.client.host if request.client else "unknown"
    result = coach_graph.invoke({
        "user_id": user_id,
        "client_ip": client_ip,
        "text": payload.text,
        "assignment_type": payload.assignment_type,
        "writing_level": payload.writing_level,
        "depth": payload.depth,
    })
    return result["response"]


@app.post("/api/humanize", response_model=HumanizeResponse)
def humanize(
    payload: HumanizeRequest,
    x_user_id: str | None = Header(default=None),
) -> HumanizeResponse:
    user_id = get_user_id(x_user_id)
    result = humanize_graph.invoke({
        "user_id": user_id,
        "text": payload.text,
        "tone": payload.tone,
        "strength": payload.strength,
        "preserve_meaning": payload.preserve_meaning,
        "preserve_citations": payload.preserve_citations,
        "preserve_structure": payload.preserve_structure,
    })
    return result["response"]


@app.get("/api/billing/status", response_model=BillingStatusResponse)
def billing_status(x_user_id: str | None = Header(default=None)) -> BillingStatusResponse:
    return billing_service.get_status(get_user_id(x_user_id))


@app.post("/api/billing/checkout", response_model=CheckoutResponse)
def billing_checkout(payload: CheckoutRequest) -> CheckoutResponse:
    valid_codes = {
        "starter_monthly", "student_plus_monthly", "pro_monthly",
        "credit_pack_s", "credit_pack_m", "credit_pack_l",
    }
    if payload.product_code not in valid_codes:
        raise HTTPException(status_code=400, detail="Unsupported product code.")
    return CheckoutResponse(
        checkout_url=billing_service.create_checkout_url(payload.product_code),
        message="Redirect the user to complete checkout.",
    )


frontend_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/assets", StaticFiles(directory=frontend_dist / "assets"), name="assets")

    @app.get("/{full_path:path}")
    def serve_frontend(full_path: str) -> FileResponse:
        return FileResponse(frontend_dist / "index.html")
