from datetime import date
from typing import Optional

from sqlalchemy import ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class Store(Base):
    __tablename__ = "stores"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)
    aisle_order: Mapped[dict] = mapped_column(JSON, default=dict)


class CanonicalIngredient(Base):
    __tablename__ = "canonical_ingredients"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)
    category: Mapped[Optional[str]]
    dirty_dozen: Mapped[bool] = mapped_column(default=False)
    organic_considerations: Mapped[list] = mapped_column(JSON, default=list)
    default_store_id: Mapped[Optional[int]] = mapped_column(ForeignKey("stores.id"))

    default_store: Mapped[Optional["Store"]] = relationship()


class Recipe(Base):
    __tablename__ = "recipes"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    source: Mapped[Optional[str]]
    steps: Mapped[Optional[str]]
    tags: Mapped[list] = mapped_column(JSON, default=list)
    times_cooked: Mapped[int] = mapped_column(default=0)
    last_cooked_date: Mapped[Optional[date]]
    favorite: Mapped[Optional[bool]]

    ingredients: Mapped[list["Ingredient"]] = relationship(back_populates="recipe")


class Ingredient(Base):
    __tablename__ = "ingredients"

    id: Mapped[int] = mapped_column(primary_key=True)
    recipe_id: Mapped[int] = mapped_column(ForeignKey("recipes.id"))
    canonical_ingredient_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("canonical_ingredients.id")
    )
    raw_name: Mapped[str]
    quantity: Mapped[Optional[float]]
    unit: Mapped[Optional[str]]

    recipe: Mapped["Recipe"] = relationship(back_populates="ingredients")
    canonical_ingredient: Mapped[Optional["CanonicalIngredient"]] = relationship()