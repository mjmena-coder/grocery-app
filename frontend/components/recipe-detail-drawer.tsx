"use client"

import { useEffect, useState } from "react"
import { X, Clock, Flame, Users, Star, Loader2, AlertCircle, ChefHat, Camera } from "lucide-react"
import {
  apiUrl,
  ingredientLabel,
  recipeImage,
  recipeIsFavorite,
  recipeTitle,
  recipeTotalMinutes,
  uploadRecipePhoto,
  type Recipe,
} from "@/lib/api"

interface RecipeDetailDrawerProps {
  recipe: Recipe | null
  open: boolean
  onClose: () => void
}

export function RecipeDetailDrawer({ recipe, open, onClose }: RecipeDetailDrawerProps) {
  const [full, setFull] = useState<Recipe | null>(recipe)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [uploadingImage, setUploadingImage] = useState(false)

  useEffect(() => {
    setFull(recipe)
    if (!recipe || !open) return

    let cancelled = false
    const load = async () => {
      setLoading(true)
      setError(null)
      try {
        const res = await fetch(apiUrl(`/recipes/${recipe.id}`))
        if (!res.ok) throw new Error(`Server returned status ${res.status}`)
        const data = (await res.json()) as Recipe
        if (!cancelled) setFull({ ...recipe, ...data })
      } catch {
        if (!cancelled) setError("Couldn't load the full recipe. Showing the summary instead.")
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
    return () => {
      cancelled = true
    }
  }, [recipe, open])

  // Close on Escape.
  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose()
    window.addEventListener("keydown", onKey)
    return () => window.removeEventListener("keydown", onKey)
  }, [open, onClose])

  const handlePhotoUpload = async (file: File | null) => {
    if (!file || !full) return
    setUploadingImage(true)
    try {
      const res = await uploadRecipePhoto(full.id, file)
      setFull((prev) => (prev ? { ...prev, image_url: res.image_url } : null))
    } catch {
      setError("Failed to upload photo.")
    } finally {
      setUploadingImage(false)
    }
  }

  if (!open || !full) return null

  const img = recipeImage(full)
  const minutes = recipeTotalMinutes(full)
  // Used to expect array when its a string. More robust normalization:
  const steps = Array.isArray(full.steps)
    ? full.steps
    : typeof full.steps === "string"
    ? full.steps.split("\n").filter(Boolean)
    : []
  const ingredients = Array.isArray(full.ingredients) ? full.ingredients : []

  return (
    <div className="fixed inset-0 z-50 flex justify-center sm:items-center">
      <button
        type="button"
        aria-label="Close recipe details"
        onClick={onClose}
        className="absolute inset-0 bg-foreground/40 backdrop-blur-sm"
      />

      <div
        role="dialog"
        aria-modal="true"
        aria-label={recipeTitle(full)}
        className="relative mt-auto flex max-h-[92dvh] w-full max-w-lg flex-col overflow-hidden rounded-t-3xl border border-border bg-card shadow-xl sm:mt-0 sm:rounded-3xl"
      >
        <div className="relative h-48 w-full shrink-0 overflow-hidden bg-secondary">
          {img ? (
            <img
              src={img}
              alt={recipeTitle(full)}
              className="h-full w-full object-cover"
              crossOrigin="anonymous"
            />
          ) : (
            <div className="flex h-full w-full items-center justify-center">
              <ChefHat className="h-10 w-10 text-muted-foreground" />
            </div>
          )}

          {/* Photo Upload Overlay Button */}
          <div className="absolute inset-0 flex items-center justify-center bg-black/30 opacity-90 transition sm:opacity-0 sm:hover:opacity-100">
            <label className="flex cursor-pointer items-center gap-1.5 rounded-full bg-background/90 px-3.5 py-1.5 text-xs font-semibold text-foreground shadow-md backdrop-blur active:scale-95">
              {uploadingImage ? (
                <Loader2 className="h-4 w-4 animate-spin text-primary" />
              ) : (
                <Camera className="h-4 w-4 text-primary" />
              )}
              <span>{img ? "Change Photo" : "Add Photo"}</span>
              <input
                type="file"
                accept="image/*"
                disabled={uploadingImage}
                onChange={(e) => {
                  e.stopPropagation()
                  handlePhotoUpload(e.target.files?.[0] || null)
                }}
                className="hidden"
              />
            </label>
          </div>

          <div className="pointer-events-none absolute inset-x-0 bottom-0 h-16 bg-gradient-to-t from-card to-transparent" />

          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            className="absolute right-3 top-3 z-10 flex h-9 w-9 items-center justify-center rounded-full bg-background/80 text-foreground shadow-sm backdrop-blur transition hover:bg-background"
          >
            <X className="h-4 w-4" />
          </button>

          {recipeIsFavorite(full) && (
            <span className="absolute left-3 top-3 z-10 flex items-center gap-1 rounded-full bg-background/80 px-2.5 py-1 text-xs font-medium text-accent-foreground shadow-sm backdrop-blur">
              <Star className="h-3.5 w-3.5 fill-accent text-accent" /> Favorite
            </span>
          )}
        </div>

        <div className="flex-1 overflow-y-auto px-6 py-5">
          <h2 className="font-display text-2xl font-semibold text-balance text-foreground">
            {recipeTitle(full)}
          </h2>

          <div className="mt-3 flex flex-wrap gap-2 text-xs">
            {minutes !== null && (
              <span className="flex items-center gap-1.5 rounded-full bg-secondary px-3 py-1.5 font-medium text-secondary-foreground">
                <Clock className="h-3.5 w-3.5" /> {minutes} min
              </span>
            )}
            {typeof full.servings === "number" && (
              <span className="flex items-center gap-1.5 rounded-full bg-secondary px-3 py-1.5 font-medium text-secondary-foreground">
                <Users className="h-3.5 w-3.5" /> Serves {full.servings}
              </span>
            )}
            {typeof full.times_cooked === "number" && (
              <span className="flex items-center gap-1.5 rounded-full bg-secondary px-3 py-1.5 font-medium text-secondary-foreground">
                <Flame className="h-3.5 w-3.5" /> Cooked {full.times_cooked}×
              </span>
            )}
          </div>

          {(full.description || full.notes) && (
            <p className="mt-4 text-sm leading-relaxed text-muted-foreground">
              {full.description || full.notes}
            </p>
          )}

          {loading && (
            <div className="mt-5 flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" /> Loading full recipe…
            </div>
          )}

          {error && (
            <div className="mt-5 flex items-start gap-2 rounded-xl border border-border bg-secondary/50 p-3 text-xs text-muted-foreground">
              <AlertCircle className="h-4 w-4 shrink-0 text-destructive" />
              <span>{error}</span>
            </div>
          )}

          {ingredients.length > 0 && (
            <section className="mt-6">
              <h3 className="mb-2 font-display text-sm font-semibold uppercase tracking-wider text-muted-foreground">
                Ingredients
              </h3>
              <ul className="space-y-1.5">
                {ingredients.map((ing, i) => (
                  <li
                    key={ing.id ?? i}
                    className="flex items-start gap-2.5 text-sm text-foreground"
                  >
                    <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-primary" />
                    {ingredientLabel(ing)}
                  </li>
                ))}
              </ul>
            </section>
          )}

          {steps.length > 0 && (
            <section className="mt-6">
              <h3 className="mb-2 font-display text-sm font-semibold uppercase tracking-wider text-muted-foreground">
                Steps
              </h3>
              <ol className="space-y-3">
                {steps.map((step, i) => (
                  <li key={i} className="flex gap-3 text-sm leading-relaxed text-foreground">
                    <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary text-xs font-semibold text-primary-foreground">
                      {i + 1}
                    </span>
                    <span className="pt-0.5">{step}</span>
                  </li>
                ))}
              </ol>
            </section>
          )}
        </div>
      </div>
    </div>
  )
}
