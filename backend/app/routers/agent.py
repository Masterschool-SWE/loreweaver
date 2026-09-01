"""Agent invocation routes.

- ``/agent/invoke``    — chat with the Keeper (free text).
- ``/agent/encounter`` — structured-output demo: returns a validated Encounter.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from ..agent import service
from ..agent.structured import Encounter
from ..auth import get_current_user
from ..database import get_session
from ..models import Hero, User
from ..schemas import AgentInvokeRequest, AgentInvokeResponse, EncounterRequest

router = APIRouter(prefix="/agent", tags=["agent"])


def _require_hero(session: Session, hero_id: int, user: User) -> Hero:
    hero = session.get(Hero, hero_id)
    if not hero or hero.user_id != user.id:
        raise HTTPException(status_code=404, detail="Hero not found")
    return hero


@router.post("/invoke", response_model=AgentInvokeResponse)
def invoke(
    req: AgentInvokeRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    hero = _require_hero(session, req.hero_id, current_user)
    try:
        reply = service.invoke_keeper(
            session,
            hero,
            req.message,
            model=req.model,
            temperature=req.temperature,
            reasoning_effort=req.reasoning_effort,
        )
    except Exception as exc:  # surface model/config errors to the UI instead of a blank 500
        raise HTTPException(status_code=502, detail=f"The Keeper faltered: {exc}") from exc

    return AgentInvokeResponse(reply=reply)


@router.post("/encounter", response_model=Encounter)
def encounter(
    req: EncounterRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    hero = _require_hero(session, req.hero_id, current_user)
    try:
        return service.forge_encounter(hero, req.scene, model=req.model)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"The Keeper faltered: {exc}") from exc
