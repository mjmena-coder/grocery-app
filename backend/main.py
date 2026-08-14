from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import backend.models
from backend.database import engine, Base
from backend.api.routes import recipes, canonical, grocery_list, stores

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Recipe & Grocery Store Router API",
    version="1.0.0",
    description="VLM-powered recipe extractor and automated store routing system."
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register route modules
app.include_router(recipes.router)
app.include_router(canonical.router)
app.include_router(grocery_list.router)
app.include_router(stores.router)


@app.get("/health")
def health_check():
    """Simple API health check endpoint."""
    return {"status": "healthy"}