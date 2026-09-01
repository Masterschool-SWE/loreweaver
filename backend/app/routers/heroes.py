"""Hero CRUD routes (scoped to the logged-in user)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from ..auth import get_current_user
from ..database import get_session
from ..models import Hero, User
from ..schemas import HeroCreate, HeroRead

router = APIRouter(prefix="/heroes", tags=["heroes"])

# Starting HP per class (see assets/worldbook/rules.md).
STARTING_HP = {"Warrior": 10, "Mage": 6, "Rogue": 8, "Ranger": 8}


@router.post("", response_model=HeroRead, status_code=201)
def create_hero(
    data: HeroCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    hero = Hero(
        user_id=current_user.id,
        name=data.name,
        char_class=data.char_class,
        race=data.race,
        backstory=data.backstory,
        hp=STARTING_HP.get(data.char_class, 10),
    )
    session.add(hero)
    session.commit()
    session.refresh(hero)
    return hero


@router.get("", response_model=list[HeroRead])
def list_heroes(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return session.exec(select(Hero).where(Hero.user_id == current_user.id)).all()


@router.get("/{hero_id}", response_model=HeroRead)
def get_hero(
    hero_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    hero = session.get(Hero, hero_id)
    if not hero or hero.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Hero not found")
    return hero
