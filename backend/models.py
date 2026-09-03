from datetime import date, datetime
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
    yield_info: Mapped[Optional[str]]
    prep_time: Mapped[Optional[str]]
    cook_time: Mapped[Optional[str]]
    notes: Mapped[list] = mapped_column(JSON, default=list)
    extraction_confidence: Mapped[Optional[float]]
    confidence_reasons: Mapped[list] = mapped_column(JSON, default=list)

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
    size_descriptor: Mapped[Optional[str]]
    # needs_canonical: Mapped[bool]
    comment: Mapped[Optional[str]]
    needs_manual_review: Mapped[bool] = mapped_column(default=False)
    review_reason: Mapped[Optional[str]]
    
    ambiguous_quantity: Mapped[bool] = mapped_column(default=False)

    recipe: Mapped["Recipe"] = relationship(back_populates="ingredients")
    canonical_ingredient: Mapped[Optional["CanonicalIngredient"]] = relationship()


class GroceryItem(Base):
    __tablename__ = "grocery_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    canonical_name: Mapped[str] # TODO: change the name, not always canonical now that kitchen staples live here.
    quantity_display: Mapped[Optional[str]]
    original_quantity_display: Mapped[Optional[str]] = mapped_column(nullable=True)
    category: Mapped[Optional[str]]
    assigned_store: Mapped[str]
    assigned_store_override: Mapped[Optional[str]] = mapped_column(nullable=True)
    recipes: Mapped[list] = mapped_column(JSON, default=list)
    is_kitchen_staple: Mapped[bool] = mapped_column(default=False)
    is_active: Mapped[bool] = mapped_column(default=True)
    is_checked: Mapped[bool] = mapped_column(default=False)
    is_deleted: Mapped[bool] = mapped_column(default=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
