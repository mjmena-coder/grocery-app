// Resolves the FastAPI backend base URL.
// The backend runs on port 8000 on the same host that serves the frontend.
export function getApiBase(): string {
  if (typeof window === "undefined") return "http://localhost:8000"
  const host = window.location.hostname || "localhost"
  return `http://${host}:8000`
}

export function apiUrl(path: string): string {
  return `${getApiBase()}${path.startsWith("/") ? path : `/${path}`}`
}

// A single consolidated grocery-list item matching your backend model.
export interface ConsolidatedItem {
  id: number
  canonical_name: string
  quantity_display?: string | null
  category: string
  assigned_store: string
  recipes: string[]
  dirty_dozen?: boolean
  organic_considerations?: string[]
  is_active?: boolean
  is_checked?: boolean
}

export interface UnlinkedIngredient {
  id: number
  raw_name: string
  recipe_id: number
  recipe_title?: string
}

// Maps directly to backend fields
export function itemName(item: ConsolidatedItem): string {
  return item.canonical_name || "Unnamed item"
}

export function itemStore(item: ConsolidatedItem): string {
  return item.assigned_store || "Unassigned"
}

export function itemCategory(item: ConsolidatedItem): string {
  return item.category || "PANTRY"
}

export function itemChecked(item: ConsolidatedItem): boolean {
  return Boolean(item.is_checked)
}

export function itemQuantity(item: ConsolidatedItem): string {
  return item.quantity_display || ""
}

// A saved recipe as returned by GET /recipes and GET /recipes/{id}.
// Field names vary by backend, so most are optional and normalized in the UI.
export interface Recipe {
  id: number
  title?: string
  name?: string
  favorite?: boolean
  is_favorite?: boolean
  times_cooked?: number
  last_cooked_date?: string | null
  prep_time?: number | string
  prep_minutes?: number
  cook_time?: number | string
  cook_minutes?: number
  servings?: number
  image_url?: string | null
  photo_url?: string | null
  image?: string | null
  description?: string
  notes?: string
  tags?: string[]
  category?: string
  ingredients?: RecipeIngredient[]
  steps?: string[]
}

export interface RecipeIngredient {
  id?: number
  raw_name?: string
  name?: string
  quantity?: number | string
  unit?: string
}

export function recipeTitle(r: Recipe): string {
  return r.title || r.name || "Untitled recipe"
}

export function recipeIsFavorite(r: Recipe): boolean {
  return Boolean(r.favorite ?? r.is_favorite)
}

export function recipeImage(r: Recipe): string | null {
  return r.image_url || r.photo_url || r.image || null
}

// Total time in minutes, coercing loosely-typed backend values.
export function recipeTotalMinutes(r: Recipe): number | null {
  const prep = toMinutes(r.prep_time ?? r.prep_minutes)
  const cook = toMinutes(r.cook_time ?? r.cook_minutes)
  if (prep === null && cook === null) return null
  return (prep ?? 0) + (cook ?? 0)
}

function toMinutes(value: number | string | undefined): number | null {
  if (value === undefined || value === null || value === "") return null
  if (typeof value === "number") return value
  const parsed = Number.parseInt(value, 10)
  return Number.isNaN(parsed) ? null : parsed
}

export function ingredientLabel(ing: RecipeIngredient): string {
  const name = ing.name || ing.raw_name || "Ingredient"
  const qty = ing.quantity
  const prefix =
    qty === undefined || qty === null || qty === ""
      ? ""
      : `${qty}${ing.unit ? ` ${ing.unit}` : ""} `
  return `${prefix}${name}`.trim()
}

// Copies text to the clipboard with a legacy fallback for insecure contexts.
export async function copyToClipboard(text: string): Promise<boolean> {
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text)
      return true
    }
  } catch {
    // fall through to legacy path
  }
  try {
    const ta = document.createElement("textarea")
    ta.value = text
    ta.style.position = "fixed"
    ta.style.opacity = "0"
    document.body.appendChild(ta)
    ta.focus()
    ta.select()
    const ok = document.execCommand("copy")
    document.body.removeChild(ta)
    return ok
  } catch {
    return false
  }
}

// Sends selected recipe ids to POST /grocery-list/generate. The backend
// aggregates quantities, runs store routing, and saves the active weekly list.
export async function generateGroceryList(recipeIds: number[]): Promise<void> {
  const res = await fetch(apiUrl("/grocery-list/generate"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ recipe_ids: recipeIds }),
  })
  if (!res.ok) {
    throw new Error(`Server returned status ${res.status}`)
  }
}

// Formats grocery items as one-per-line plain text. Pasting this into a
// Google Keep note that is in checklist mode turns each line into a checkbox.
export function formatItemsForKeep(items: ConsolidatedItem[]): string {
  return items
    .map((item) => {
      const qty = itemQuantity(item)
      return qty ? `${qty} - ${itemName(item)}` : itemName(item)
    })
    .join("\n")
}
