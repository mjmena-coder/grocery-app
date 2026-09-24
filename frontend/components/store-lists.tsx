"use client"

import { useEffect, useMemo, useState } from "react"
import { Loader2, AlertCircle, Plus } from "lucide-react"
import { apiUrl, type ConsolidatedItem } from "@/lib/api"
import { StoreSplitView } from "@/components/store-split-view"
import { FrequentItemsModal } from "@/components/frequent-items-modal"
import { KitchenStaplesModal } from "@/components/kitchen-staples-modal"

// Recipe indicator color rotation for key and item badges across store list and modals
export const RECIPE_COLORS = [
  "bg-rose-500",
  "bg-amber-500",
  "bg-emerald-500",
  "bg-sky-500",
  "bg-indigo-500",
  "bg-fuchsia-500",
  "bg-teal-500",
  "bg-orange-500",
  "bg-violet-500",
  "bg-lime-600",
]

function normalizeItemsArray(rawItems: unknown): ConsolidatedItem[] {
  if (!rawItems) return []
  if (Array.isArray(rawItems)) return rawItems
  if (typeof rawItems === "object") {
    const obj = rawItems as Record<string, unknown>
    if (Array.isArray(obj.items)) return obj.items as ConsolidatedItem[]
    
    // Handle grouped store objects: { "Store Name": [items...] }
    const accumulated: ConsolidatedItem[] = []
    for (const key of Object.keys(obj)) {
      if (Array.isArray(obj[key])) {
        accumulated.push(...(obj[key] as ConsolidatedItem[]))
      }
    }
    return accumulated
  }
  return []
}

export function StoreLists() {
  const [items, setItems] = useState<ConsolidatedItem[]>([])
  const [kitchenStaples, setKitchenStaples] = useState<ConsolidatedItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  
  // State for controlling the modals
  const [showFrequentModal, setShowFrequentModal] = useState(false)
  const [showStaplesModal, setShowStaplesModal] = useState(false)

  const fetchItems = async () => {
    setLoading(true)
    setError(null)

    const endpoints = [
      "/grocery-list/current",
      "/grocery-list/consolidated",
      "/grocery-list",
    ]

    for (const path of endpoints) {
      try {
        const res = await fetch(apiUrl(path))
        if (res.ok) {
          const data = await res.json()
          
          const parsedItems = normalizeItemsArray(data.items ?? data)
          const parsedStaples = normalizeItemsArray(data.kitchen_staples)

          setItems(parsedItems)
          setKitchenStaples(parsedStaples)
          setLoading(false)
          return
        }
      } catch {
        // Try the next endpoint if this route isn't mounted.
      }
    }

    setError("Could not connect to the grocery list endpoint. Is the FastAPI server running on port 8000?")
    setLoading(false)
  }

  useEffect(() => {
    fetchItems()
  }, [])

  const recipeColorMap = useMemo(() => {
    const names = new Set<string>()
    const safeItems = normalizeItemsArray(items)
    const safeStaples = normalizeItemsArray(kitchenStaples)
    const allItems = [...safeItems, ...safeStaples]

    for (const item of allItems) {
      if (item?.recipes) {
        for (const r of item.recipes) {
          const trimmed = r?.trim()
          if (trimmed) names.add(trimmed)
        }
      }
    }
    const map = new Map<string, string>()
    Array.from(names)
      .sort((a, b) => a.localeCompare(b))
      .forEach((name, index) => {
        map.set(name, RECIPE_COLORS[index % RECIPE_COLORS.length])
      })
    return map
  }, [items, kitchenStaples])

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h2 className="font-display text-xl font-semibold text-foreground">This Week&apos;s Route</h2>
          <p className="text-sm text-muted-foreground">
            Split by store &amp; aisle. Tap a store&apos;s{" "}
            <span className="font-medium text-foreground">copy</span> icon to paste it into a
            Google Keep checklist.
          </p>
        </div>
        
        <div className="flex items-center gap-2">
          {kitchenStaples.length > 0 && (
            <button
              type="button"
              onClick={() => setShowStaplesModal(true)}
              className="flex items-center gap-1.5 rounded-lg border border-border bg-card px-3 py-2 text-sm font-medium text-foreground transition hover:bg-secondary"
            >
              Kitchen Staples ({kitchenStaples.length})
            </button>
          )}

          <button
            type="button"
            onClick={() => setShowFrequentModal(true)}
            className="flex items-center gap-1.5 rounded-lg border border-border bg-card px-3 py-2 text-sm font-medium text-foreground transition hover:bg-secondary"
          >
            <Plus className="h-4 w-4" />
            Add Frequent Items
          </button>
        </div>
      </div>

      {loading && (
        <div className="flex items-center justify-center gap-2 py-20 text-muted-foreground">
          <Loader2 className="h-6 w-6 animate-spin" /> Fetching store lists…
        </div>
      )}

      {error && !loading && (
        <div className="flex items-start gap-3 rounded-xl border border-destructive/30 bg-destructive/5 p-4 text-sm text-foreground">
          <AlertCircle className="h-5 w-5 shrink-0 text-destructive" />
          <span>{error}</span>
        </div>
      )}

      {!loading && !error && (
        <StoreSplitView
          items={items}
          recipeColorMap={recipeColorMap}
          onRefresh={fetchItems}
        />
      )}

      {/* Kitchen Staples Modal */}
      <KitchenStaplesModal
        isOpen={showStaplesModal}
        onClose={() => setShowStaplesModal(false)}
        staples={kitchenStaples}
        recipeColorMap={recipeColorMap}
        onRefresh={fetchItems}
      />

      {/* Frequent Items Modal */}
      <FrequentItemsModal
        isOpen={showFrequentModal}
        onClose={() => setShowFrequentModal(false)}
        stores={["King Soopers", "Trader Joe's", "Whole Foods"]}
        onRefresh={fetchItems}
      />
    </div>
  )
}
