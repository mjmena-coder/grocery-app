# Grocery Assistant

An AI-powered recipe management and grocery consolidation platform. Scan physical recipe cards or cookbook photos using local Vision-Language Models (VLMs), consolidate ingredients across recipes with unit intelligence, route items to your preferred stores, and export optimized shopping lists.

---

## 🌟 Key Features

- **VLM Recipe Digitization**: Upload photos of physical recipe cards or cookbook pages to extract structured ingredients, cooking times, yields, and step-by-step instructions via local Ollama inference (`qwen2.5-vl:7b`).
- **Ingredient Consolidation Engine**: Merges like ingredients across multiple planned recipes, normalizes fractions and units (e.g., cups, tablespoons, grams, ounces), and adjusts unit pluralities.
- **Smart Store Routing**:
  - Automatically routes ingredients to designated stores (e.g., King Soopers, Trader Joe's) based on category rules and user defaults.
  - Organic routing support for "Dirty Dozen" produce items.
- **Kitchen Staples Segregation**: Identifies pantry/staple items (salt, oil, spices) and isolates them in a dedicated drawer so shopping lists stay focused.
- **Interactive Web App**: Next.js React frontend featuring recipe flipping / deck browsing, batch recipe selection for weekly planning, soft deletion with restoration, in-line quantity editing, and one-click copy to clipboard formatted for Google Keep.

---

## 🛠 Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.10+)
- **ORM & Database**: SQLAlchemy 2.0 with SQLite
- **AI / VLM**: Ollama (`qwen2.5-vl:7b` / custom models)
- **Validation**: Pydantic v2
- **Testing**: Pytest

### Frontend
- **Framework**: Next.js 14 / React 18
- **Styling**: Tailwind CSS, Lucide Icons, Radix UI primitives

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+ and `npm` / `pnpm` / `yarn`
- [Ollama](https://ollama.com/) running locally with the vision model pulled:
  ```bash
  ollama pull qwen2.5-vl:7b
  ```

---

### Backend Setup

1. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Start the FastAPI backend server:
   ```bash
   uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
   ```
   The backend API will be available at `http://localhost:8000`. Interactive docs are at `http://localhost:8000/docs`.

---

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install Node dependencies:
   ```bash
   npm install
   ```

3. Run the development server:
   ```bash
   npm run dev
   ```
   Open `http://localhost:3000` in your browser.

---

## 🧪 Running Tests

Run backend tests using `pytest`:

