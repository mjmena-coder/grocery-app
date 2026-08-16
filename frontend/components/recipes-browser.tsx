"use client"

import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import {
  Loader2,
  AlertCircle,
  RefreshCw,
  Search,
  Star,
  Clock,
  Flame,
  ChefHat,
  LayoutGrid,
  Rows3,
  ChevronLeft,
  ChevronRight,
  CalendarPlus,
  Check,
  ShoppingBasket,
  X,
} from "lucide-react"
import {
  apiUrl,
  generateGroceryList,
  recipeImage,
  recipeIsFavorite,
  recipeTitle,
  recipeTotalMinutes,
  type Recipe,
} from "@/lib/api"
import { RecipeDetailDrawer } from "@/components/recipe-detail-drawer"

type ViewMode = "changer" | "list"

interface RecipesBrowserProps {
  // Called after a weekly list is generated, so the parent can switch to the
  // Store Lists tab.
  onListGenerated?: () => void
}

export function RecipesBrowser({ onListGenerated }: RecipesBrowserProps) {
  const [recipes, setRecipes] = useState<Recipe[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState("")
  const [favoritesOnly, setFavoritesOnly] = useState(false)
  const [view, setView] = useState<ViewMode>("changer")
  const [favOverrides, setFavOverrides] = useState<Record<number, boolean>>({})
  const [selected, setSelected] = useState<Recipe | null>(null)

  // "Plan the week" multi-select state.
  const [planning, setPlanning] = useState(false)
  const [chosenIds, setChosenIds] = useState<Set<number>>(new Set())
  const [generating, setGenerating] = useState(false)
  const [genError, setGenError] = useState<string | null>(null)

  const toggleChosen = useCallback((r: Recipe) => {
    setChosenIds((prev) => {
      const next = new Set(prev)
      if (next.has(r.id)) next.delete(r.id)
      else next.add(r.id)
      return next
    })
  }, [])

  const exitPlanning = useCallback(() => {
    setPlanning(false)
    setChosenIds(new Set())
    setGenError(null)
  }, [])

  const handleGenerate = useCallback(async () => {
    if (chosenIds.size === 0) return
    setGenerating(true)
    setGenError(null)
    try {
      await generateGroceryList(Array.from(chosenIds))
      exitPlanning()
      onListGenerated?.()
    } catch {
      setGenError("Could not generate the list. Is the FastAPI server running on port 8000?")
    } finally {
      setGenerating(false)
    }
  }, [chosenIds, exitPlanning, onListGenerated])

  const fetchRecipes = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(apiUrl("/recipes/"))
      if (!res.ok) throw new Error(`Server returned status ${res.status}`)
      const data = await res.json()
      setRecipes(Array.isArray(data) ? data : data.recipes || data.items || [])
    } catch {
      setError("Could not load recipes. Is the FastAPI server running on port 8000?")
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchRecipes()
  }, [fetchRecipes])

  const isFav = useCallback(
    (r: Recipe) => favOverrides[r.id] ?? recipeIsFavorite(r),
    [favOverrides],
  )

  const toggleFavorite = useCallback(
    async (r: Recipe) => {
      const next = !isFav(r)
      setFavOverrides((prev) => ({ ...prev, [r.id]: next }))
      try {
        await fetch(apiUrl(`/recipes/${r.id}`), {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ favorite: next }),
        })
      } catch {
        setFavOverrides((prev) => ({ ...prev, [r.id]: !next }))
      }
    },
    [isFav],
  )

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase()
    return recipes.filter((r) => {
      if (favoritesOnly && !isFav(r)) return false
      if (q && !recipeTitle(r).toLowerCase().includes(q)) return false
      return true
    })
  }, [recipes, search, favoritesOnly, isFav])

  return (
    <div>
      <div className="mb-5 flex flex-col gap-4">
        <div className="flex items-end justify-between gap-3">
          <div>
            <h2 className="font-display text-xl font-semibold text-foreground">Recipe Box</h2>
            <p className="text-sm text-muted-foreground">
              Flip through what looks good this week.
            </p>
          </div>
          <div className="flex items-center gap-1 rounded-xl border border-border bg-card p-1">
            <button
              type="button"
              onClick={() => setView("changer")}
              aria-pressed={view === "changer"}
              aria-label="Cover-flow view"
              className={`flex h-8 w-8 items-center justify-center rounded-lg transition ${
                view === "changer"
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-secondary"
              }`}
            >
              <LayoutGrid className="h-4 w-4" />
            </button>
            <button
              type="button"
              onClick={() => setView("list")}
              aria-pressed={view === "list"}
              aria-label="List view"
              className={`flex h-8 w-8 items-center justify-center rounded-lg transition ${
                view === "list"
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-secondary"
              }`}
            >
              <Rows3 className="h-4 w-4" />
            </button>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <div className="relative min-w-0 flex-1">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <input
              type="search"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search recipes…"
              className="h-10 w-full rounded-xl border border-border bg-card pl-9 pr-3 text-sm text-foreground outline-none transition placeholder:text-muted-foreground focus:border-primary focus:ring-2 focus:ring-ring/30"
            />
          </div>
          <button
            type="button"
            onClick={() => setFavoritesOnly((v) => !v)}
            aria-pressed={favoritesOnly}
            className={`flex h-10 items-center gap-2 rounded-xl border px-3 text-sm font-medium transition ${
              favoritesOnly
                ? "border-accent bg-accent/20 text-accent-foreground"
                : "border-border bg-card text-muted-foreground hover:bg-secondary"
            }`}
          >
            <Star className={`h-4 w-4 ${favoritesOnly ? "fill-accent text-accent" : ""}`} />
            <span className="hidden sm:inline">Favorites</span>
          </button>
          <button
            type="button"
            onClick={() => (planning ? exitPlanning() : setPlanning(true))}
            aria-pressed={planning}
            className={`flex h-10 items-center gap-2 rounded-xl border px-3 text-sm font-medium transition ${
              planning
                ? "border-primary bg-primary text-primary-foreground"
                : "border-border bg-card text-foreground hover:bg-secondary"
            }`}
          >
            {planning ? <X className="h-4 w-4" /> : <CalendarPlus className="h-4 w-4" />}
            <span className="hidden sm:inline">{planning ? "Cancel" : "Plan week"}</span>
          </button>
          <button
            type="button"
            onClick={fetchRecipes}
            disabled={loading}
            aria-label="Refresh recipes"
            className="flex h-10 items-center gap-2 rounded-xl border border-border bg-card px-3 text-sm font-medium text-foreground transition hover:bg-secondary disabled:opacity-50"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          </button>
        </div>

        {planning && (
          <div className="flex items-center gap-2 rounded-xl border border-primary/30 bg-primary/5 px-3 py-2 text-sm text-foreground">
            <ShoppingBasket className="h-4 w-4 shrink-0 text-primary" />
            <span>
              Select the recipes you want to cook this week, then generate a consolidated shopping
              list.
            </span>
          </div>
        )}
      </div>

      {loading && (
        <div className="flex items-center justify-center gap-2 py-20 text-muted-foreground">
          <Loader2 className="h-6 w-6 animate-spin" /> Fetching recipes…
        </div>
      )}

      {error && !loading && (
        <div className="flex items-start gap-3 rounded-xl border border-destructive/30 bg-destructive/5 p-4 text-sm text-foreground">
          <AlertCircle className="h-5 w-5 shrink-0 text-destructive" />
          <span>{error}</span>
        </div>
      )}

      {!loading && !error && filtered.length === 0 && (
        <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-border bg-card py-20 text-center">
          <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-secondary">
            <ChefHat className="h-6 w-6 text-muted-foreground" />
          </div>
          <p className="font-display text-lg font-semibold text-foreground">No recipes yet</p>
          <p className="mt-1 max-w-sm text-sm text-muted-foreground">
            {recipes.length === 0
              ? "Scan a cookbook photo on the Upload tab to build your recipe box."
              : "No recipes match your current filters."}
          </p>
        </div>
      )}

      {!loading && !error && filtered.length > 0 && (
        <div className={planning ? "pb-28" : undefined}>
          {view === "changer" ? (
            <CoverFlow
              recipes={filtered}
              isFav={isFav}
              onToggleFav={toggleFavorite}
              onOpen={setSelected}
              planning={planning}
              chosenIds={chosenIds}
              onToggleChosen={toggleChosen}
            />
          ) : (
            <RecipeList
              recipes={filtered}
              isFav={isFav}
              onToggleFav={toggleFavorite}
              onOpen={setSelected}
              planning={planning}
              chosenIds={chosenIds}
              onToggleChosen={toggleChosen}
            />
          )}
        </div>
      )}

      {planning && (
        <div className="fixed inset-x-0 bottom-0 z-30 border-t border-border bg-card/95 backdrop-blur">
          <div className="mx-auto flex max-w-5xl flex-col gap-2 px-4 py-3">
            {genError && (
              <div className="flex items-start gap-2 rounded-lg border border-destructive/30 bg-destructive/5 px-3 py-2 text-xs text-foreground">
                <AlertCircle className="h-4 w-4 shrink-0 text-destructive" />
                <span>{genError}</span>
              </div>
            )}
            <div className="flex items-center justify-between gap-3">
              <div className="min-w-0">
                <p className="font-display font-semibold text-foreground">
                  {chosenIds.size} {chosenIds.size === 1 ? "recipe" : "recipes"} selected
                </p>
                <p className="truncate text-xs text-muted-foreground">
                  {chosenIds.size === 0
                    ? "Tap recipes to add them to this week."
                    : "Quantities will be consolidated and routed by store."}
                </p>
              </div>
              <button
                type="button"
                onClick={handleGenerate}
                disabled={chosenIds.size === 0 || generating}
                className="flex h-11 shrink-0 items-center gap-2 rounded-xl bg-primary px-5 text-sm font-semibold text-primary-foreground transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {generating ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" /> Generating…
                  </>
                ) : (
                  <>
                    <ShoppingBasket className="h-4 w-4" /> Generate list
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      <RecipeDetailDrawer
        recipe={selected}
        open={selected !== null}
        onClose={() => setSelected(null)}
      />
    </div>
  )
}

interface CardActionProps {
  recipes: Recipe[]
  isFav: (r: Recipe) => boolean
  onToggleFav: (r: Recipe) => void
  onOpen: (r: Recipe) => void
  planning: boolean
  chosenIds: Set<number>
  onToggleChosen: (r: Recipe) => void
}

// The "CD changer": a horizontal snap carousel where the centered card pops
// forward and its neighbors recede — like flipping through discs in a changer.
function CoverFlow({
  recipes,
  isFav,
  onToggleFav,
  onOpen,
  planning,
  chosenIds,
  onToggleChosen,
}: CardActionProps) {
  const scrollerRef = useRef<HTMLDivElement>(null)
  const [active, setActive] = useState(0)

  const updateActive = useCallback(() => {
    const el = scrollerRef.current
    if (!el) return
    const center = el.scrollLeft + el.clientWidth / 2
    let closest = 0
    let closestDist = Number.POSITIVE_INFINITY
    const cards = Array.from(el.querySelectorAll<HTMLElement>("[data-card]"))
    cards.forEach((card, i) => {
      const cardCenter = card.offsetLeft + card.offsetWidth / 2
      const dist = Math.abs(cardCenter - center)
      if (dist < closestDist) {
        closestDist = dist
        closest = i
      }
    })
    setActive(closest)
  }, [])

  useEffect(() => {
    const el = scrollerRef.current
    if (!el) return
    let frame = 0
    const onScroll = () => {
      cancelAnimationFrame(frame)
      frame = requestAnimationFrame(updateActive)
    }
    el.addEventListener("scroll", onScroll, { passive: true })
    updateActive()
    return () => {
      el.removeEventListener("scroll", onScroll)
      cancelAnimationFrame(frame)
    }
  }, [updateActive, recipes.length])

  const scrollTo = (index: number) => {
    const el = scrollerRef.current
    if (!el) return
    const clamped = Math.max(0, Math.min(index, recipes.length - 1))
    const card = el.querySelectorAll<HTMLElement>("[data-card]")[clamped]
    if (card) {
      el.scrollTo({
        left: card.offsetLeft - (el.clientWidth - card.offsetWidth) / 2,
        behavior: "smooth",
      })
    }
  }

  const current = recipes[active]

  return (
    <div className="relative">
      <div
        ref={scrollerRef}
        className="flex snap-x snap-mandatory gap-4 overflow-x-auto scroll-smooth px-[15%] pb-4 pt-2 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
      >
        {recipes.map((r, i) => {
          const activeCard = i === active
          const img = recipeImage(r)
          const minutes = recipeTotalMinutes(r)
          const fav = isFav(r)
          const chosen = chosenIds.has(r.id)
          const handleClick = () => {
            if (!activeCard) {
              scrollTo(i)
              return
            }
            if (planning) onToggleChosen(r)
            else onOpen(r)
          }
          return (
            <div
              key={r.id}
              data-card
              className="snap-center shrink-0 basis-[70%] transition-all duration-300 ease-out sm:basis-[48%]"
              style={{
                transform: activeCard ? "scale(1)" : "scale(0.9)",
                opacity: activeCard ? 1 : 0.55,
              }}
            >
              <button
                type="button"
                onClick={handleClick}
                aria-pressed={planning ? chosen : undefined}
                className={`group block w-full overflow-hidden rounded-2xl border bg-card text-left shadow-sm transition hover:shadow-md ${
                  planning && chosen
                    ? "border-primary ring-2 ring-primary"
                    : "border-border"
                }`}
                style={{
                  boxShadow: activeCard
                    ? "0 12px 30px -12px oklch(0.24 0.015 75 / 0.35)"
                    : undefined,
                }}
              >
                <div className="relative aspect-[4/5] w-full overflow-hidden">
                  {planning && (
                    <span
                      className={`absolute left-3 top-3 z-10 flex h-8 w-8 items-center justify-center rounded-full border-2 shadow-sm transition ${
                        chosen
                          ? "border-primary bg-primary text-primary-foreground"
                          : "border-background/80 bg-background/70 text-transparent backdrop-blur"
                      }`}
                    >
                      <Check className="h-4 w-4" />
                    </span>
                  )}
                  {img ? (
                    <img
                      src={img || "/placeholder.svg"}
                      alt={recipeTitle(r)}
                      className="h-full w-full object-cover transition duration-500 group-hover:scale-105"
                      crossOrigin="anonymous"
                    />
                  ) : (
                    <div className="flex h-full w-full flex-col items-center justify-center gap-2 bg-gradient-to-b from-secondary to-muted">
                      <ChefHat className="h-10 w-10 text-muted-foreground/70" />
                      <span className="text-xs font-medium text-muted-foreground">
                        No photo yet
                      </span>
                    </div>
                  )}
                  <span
                    onClick={(e) => {
                      e.stopPropagation()
                      onToggleFav(r)
                    }}
                    role="button"
                    tabIndex={0}
                    aria-label={fav ? "Remove from favorites" : "Add to favorites"}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" || e.key === " ") {
                        e.preventDefault()
                        e.stopPropagation()
                        onToggleFav(r)
                      }
                    }}
                    className="absolute right-3 top-3 flex h-9 w-9 items-center justify-center rounded-full bg-background/80 text-foreground shadow-sm backdrop-blur transition hover:bg-background"
                  >
                    <Star className={`h-4 w-4 ${fav ? "fill-accent text-accent" : ""}`} />
                  </span>
                  <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-foreground/75 to-transparent p-4 pt-10">
                    <h3 className="font-display text-lg font-semibold leading-tight text-balance text-background">
                      {recipeTitle(r)}
                    </h3>
                    <div className="mt-1.5 flex flex-wrap items-center gap-3 text-xs text-background/85">
                      {minutes !== null && (
                        <span className="flex items-center gap-1">
                          <Clock className="h-3.5 w-3.5" /> {minutes} min
                        </span>
                      )}
                      {typeof r.times_cooked === "number" && (
                        <span className="flex items-center gap-1">
                          <Flame className="h-3.5 w-3.5" /> {r.times_cooked}×
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </button>
            </div>
          )
        })}
      </div>

      <div className="mt-2 flex items-center justify-center gap-4">
        <button
          type="button"
          onClick={() => scrollTo(active - 1)}
          disabled={active === 0}
          aria-label="Previous recipe"
          className="flex h-9 w-9 items-center justify-center rounded-full border border-border bg-card text-foreground transition hover:bg-secondary disabled:opacity-40"
        >
          <ChevronLeft className="h-4 w-4" />
        </button>

        <div className="flex items-center gap-1.5">
          {recipes.slice(0, 12).map((r, i) => (
            <button
              key={r.id}
              type="button"
              onClick={() => scrollTo(i)}
              aria-label={`Go to recipe ${i + 1}`}
              className={`h-1.5 rounded-full transition-all ${
                i === active ? "w-5 bg-primary" : "w-1.5 bg-border hover:bg-muted-foreground"
              }`}
            />
          ))}
        </div>

        <button
          type="button"
          onClick={() => scrollTo(active + 1)}
          disabled={active === recipes.length - 1}
          aria-label="Next recipe"
          className="flex h-9 w-9 items-center justify-center rounded-full border border-border bg-card text-foreground transition hover:bg-secondary disabled:opacity-40"
        >
          <ChevronRight className="h-4 w-4" />
        </button>
      </div>

      {current && (
        <p className="mt-3 text-center text-sm text-muted-foreground">
          {planning ? (
            <>
              Tap the centered card to {chosenIds.has(current.id) ? "remove" : "add"}{" "}
              <span className="font-medium text-foreground">{recipeTitle(current)}</span>
            </>
          ) : (
            <>
              Tap the centered card to open{" "}
              <span className="font-medium text-foreground">{recipeTitle(current)}</span>
            </>
          )}
        </p>
      )}
    </div>
  )
}

function RecipeList({
  recipes,
  isFav,
  onToggleFav,
  onOpen,
  planning,
  chosenIds,
  onToggleChosen,
}: CardActionProps) {
  return (
    <ul className="flex flex-col gap-3">
      {recipes.map((r) => {
        const img = recipeImage(r)
        const minutes = recipeTotalMinutes(r)
        const fav = isFav(r)
        const chosen = chosenIds.has(r.id)
        return (
          <li key={r.id}>
            <div
              className={`flex items-center gap-3 overflow-hidden rounded-2xl border bg-card p-2.5 shadow-sm transition hover:shadow-md ${
                planning && chosen ? "border-primary ring-2 ring-primary" : "border-border"
              }`}
            >
              {planning && (
                <span
                  aria-hidden
                  className={`ml-1 flex h-6 w-6 shrink-0 items-center justify-center rounded-full border-2 transition ${
                    chosen
                      ? "border-primary bg-primary text-primary-foreground"
                      : "border-border text-transparent"
                  }`}
                >
                  <Check className="h-3.5 w-3.5" />
                </span>
              )}
              <button
                type="button"
                onClick={() => (planning ? onToggleChosen(r) : onOpen(r))}
                aria-pressed={planning ? chosen : undefined}
                className="flex min-w-0 flex-1 items-center gap-3 text-left"
              >
                <div className="relative h-16 w-16 shrink-0 overflow-hidden rounded-xl">
                  {img ? (
                    <img
                      src={img || "/placeholder.svg"}
                      alt={recipeTitle(r)}
                      className="h-full w-full object-cover"
                      crossOrigin="anonymous"
                    />
                  ) : (
                    <div className="flex h-full w-full items-center justify-center bg-secondary">
                      <ChefHat className="h-6 w-6 text-muted-foreground/70" />
                    </div>
                  )}
                </div>
                <div className="min-w-0 flex-1">
                  <h3 className="truncate font-display font-semibold text-foreground">
                    {recipeTitle(r)}
                  </h3>
                  <div className="mt-1 flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
                    {minutes !== null && (
                      <span className="flex items-center gap-1">
                        <Clock className="h-3.5 w-3.5" /> {minutes} min
                      </span>
                    )}
                    {typeof r.times_cooked === "number" && (
                      <span className="flex items-center gap-1">
                        <Flame className="h-3.5 w-3.5" /> Cooked {r.times_cooked}×
                      </span>
                    )}
                  </div>
                </div>
              </button>
              {!planning && (
                <button
                  type="button"
                  onClick={() => onToggleFav(r)}
                  aria-label={fav ? "Remove from favorites" : "Add to favorites"}
                  className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-foreground transition hover:bg-secondary"
                >
                  <Star className={`h-4 w-4 ${fav ? "fill-accent text-accent" : ""}`} />
                </button>
              )}
            </div>
          </li>
        )
      })}
    </ul>
  )
}
