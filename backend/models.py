from sqlalchemy import (
    Column, Integer, String, Boolean, Float, ForeignKey, JSON, Date
)
from sqlalchemy.orm import relationship

from backend.database import Base


class Store(Base):
    __tablename__ = "stores"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    # category -> position, e.g. {"produce": 1, "dairy": 2, "pantry": 3}
    aisle_order = Column(JSON, default=dict)


class CanonicalIngredient(Base):
    __tablename__ = "canonical_ingredients"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    category = Column(String)  # produce, dairy, meat, pantry, etc.
    dirty_dozen = Column(Boolean, default=False)
    organic_considerations = Column(JSON, default=list)  # e.g. ["hormone-free"]
    default_store_id = Column(Integer, ForeignKey("stores.id"), nullable=True)

    default_store = relationship("Store")


class Recipe(Base):
    __tablename__ = "recipes"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    source = Column(String)  # cookbook / page
    steps = Column(String)   # raw text for now
    tags = Column(JSON, default=list)
    times_cooked = Column(Integer, default=0)
    last_cooked_date = Column(Date, nullable=True)
    favorite = Column(Boolean, nullable=True)  # null = not rated yet

    ingredients = relationship("Ingredient", back_populates="recipe")


class Ingredient(Base):
    __tablename__ = "ingredients"

    id = Column(Integer, primary_key=True)
    recipe_id = Column(Integer, ForeignKey("recipes.id"), nullable=False)
    canonical_ingredient_id = Column(
        Integer, ForeignKey("canonical_ingredients.id"), nullable=True
    )
    raw_name = Column(String, nullable=False)  # exactly as parsed, e.g. "yellow onion"
    quantity = Column(Float)
    unit = Column(String, nullable=True)

    recipe = relationship("Recipe", back_populates="ingredients")
    canonical_ingredient = relationship("CanonicalIngredient")