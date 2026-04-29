from __future__ import annotations

from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field


router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    page: str | None = Field(default=None, max_length=200)


class SuggestedAction(BaseModel):
    label: str
    href: str


class ChatResponse(BaseModel):
    reply: str
    intent: Literal[
        "forecast",
        "history",
        "alerts",
        "downloads",
        "confidence",
        "calculator",
        "about",
        "unknown",
        "refuse_admin",
    ]
    suggested_actions: list[SuggestedAction] = []


_ADMIN_BLOCKLIST = (
    "admin",
    "dashboard",
    "pipeline",
    "performance",
    "settings",
    "logout",
    "log out",
)


def _normalize(text: str) -> str:
    return " ".join(text.lower().strip().split())


def _contains_any(text: str, needles: tuple[str, ...]) -> bool:
    return any(n in text for n in needles)


@router.post("", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    """
    Guidance chatbot for the public website.

    Hard rule: never discuss admin topics. If asked, refuse and redirect to public help.
    """
    msg = _normalize(req.message)

    # Strictly refuse admin-related prompts (including "how do I login?" which is often admin-only here).
    if _contains_any(msg, _ADMIN_BLOCKLIST) or msg.startswith("login") or "log in" in msg:
        return ChatResponse(
            reply=(
                "I can help with the public website (forecast, history, downloads, and price alerts), "
                "but I can’t assist with admin or login topics. "
                "Tell me what you’re trying to do on the forecast or history pages."
            ),
            intent="refuse_admin",
            suggested_actions=[
                SuggestedAction(label="Forecast", href="/forecast"),
                SuggestedAction(label="History", href="/history"),
            ],
        )

    # Intent routing (keep it simple + deterministic).
    if _contains_any(msg, ("forecast", "predict", "prediction", "tomorrow", "3-day", "3 day")):
        return ChatResponse(
            reply=(
                "The Forecast page shows the AI 3‑day price prediction for Balaya at the Peliyagoda market. "
                "Open the detailed view to see the chart, table, and the confidence band (upper/lower bounds)."
            ),
            intent="forecast",
            suggested_actions=[
                SuggestedAction(label="Open Forecast", href="/forecast"),
                SuggestedAction(label="Go Home", href="/"),
            ],
        )

    if _contains_any(msg, ("history", "historical", "trend", "past", "date range")):
        return ChatResponse(
            reply=(
                "The History page lets you explore past price trends over a selectable date range. "
                "Use the date range selector to zoom in on a period and compare how prices changed over time."
            ),
            intent="history",
            suggested_actions=[SuggestedAction(label="Open History", href="/history")],
        )

    if _contains_any(msg, ("download", "csv", "export", "excel")):
        return ChatResponse(
            reply=(
                "You can export data from the site using the download/export controls. "
                "If you want raw history as CSV, use the download option from the pages that offer it."
            ),
            intent="downloads",
            suggested_actions=[
                SuggestedAction(label="Forecast", href="/forecast"),
                SuggestedAction(label="History", href="/history"),
            ],
        )

    if _contains_any(msg, ("alert", "notify", "notification", "price alert")):
        return ChatResponse(
            reply=(
                "Price alerts let you get notified when the price crosses a level you care about. "
                "Open the Forecast page and use the Price Alert form to set your target."
            ),
            intent="alerts",
            suggested_actions=[SuggestedAction(label="Set an alert", href="/forecast")],
        )

    if _contains_any(msg, ("confidence", "band", "upper", "lower", "uncertainty", "range")):
        return ChatResponse(
            reply=(
                "Confidence bands show an estimated upper/lower range around the prediction. "
                "A wider band means more uncertainty; a tighter band means the model is more confident."
            ),
            intent="confidence",
            suggested_actions=[SuggestedAction(label="See Forecast details", href="/forecast")],
        )

    if _contains_any(msg, ("calculator", "wholesale", "volume", "profit", "margin")):
        return ChatResponse(
            reply=(
                "The wholesale calculator helps you estimate totals using the forecasted price. "
                "Go to the Forecast page to adjust volumes and see quick planning numbers."
            ),
            intent="calculator",
            suggested_actions=[SuggestedAction(label="Open Forecast", href="/forecast")],
        )

    if _contains_any(msg, ("about", "what is this", "what is fishprice", "site", "website")):
        return ChatResponse(
            reply=(
                "FishPrice.LK provides AI-assisted fish price forecasts and historical trend views. "
                "Use Forecast for the next few days and History for past trends."
            ),
            intent="about",
            suggested_actions=[
                SuggestedAction(label="About", href="/about"),
                SuggestedAction(label="Forecast", href="/forecast"),
                SuggestedAction(label="History", href="/history"),
            ],
        )

    return ChatResponse(
        reply=(
            "I can help you navigate the public site. "
            "Do you want help with the Forecast (next 3 days), History (past trends), downloads, or price alerts?"
        ),
        intent="unknown",
        suggested_actions=[
            SuggestedAction(label="Forecast", href="/forecast"),
            SuggestedAction(label="History", href="/history"),
            SuggestedAction(label="About", href="/about"),
        ],
    )

