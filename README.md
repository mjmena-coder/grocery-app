# Grocery Assistant API

A VLM-powered backend service designed to automate grocery list management, recipe extraction, and store routing.

## Features
- **Recipe Extraction**: Uses VLM (via Ollama) to parse images of physical recipes into structured data.
- **Canonical Mapping**: Automatically maps raw ingredients to a canonical database.
- **Grocery Management**: Tracks ingredient lists and generates optimized shopping routes.
- **Store Routing**: Manages store inventories and aisle mappings.

## Tech Stack
- **Backend**: FastAPI
- **Database**: SQLite with SQLAlchemy ORM
- **Inference**: Ollama (Qwen2.5-VL)

## API Endpoints

### Health
- `GET /health`: Returns service status.

### Recipes
- `POST /recipes/extract`: Processes an image upload, extracts recipe data, and saves to the database.

### Canonical Ingredients
- `GET /canonical`: List all canonical ingredients.
- `POST /canonical`: Add or update a canonical ingredient.

### Grocery List
- `GET /grocery_list`: Retrieve current shopping list.
- `POST /grocery_list`: Add items to the list.

### Stores
- `GET /stores`: List all configured grocery stores and their metadata.

## Getting Started

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Server**
   ```bash
   uvicorn backend.main:app --reload
   ```