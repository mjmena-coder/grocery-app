"use client"

import { useMemo, useState } from "react"
import { Store, Check, ShoppingCart, Leaf, ClipboardList, ClipboardCheck, Edit2, Trash2, ArrowRightLeft, Check as SaveIcon, Scale } from "lucide-react"
import {
  apiUrl,
  copyToClipboard,
  formatItemsForKeep,
  itemCategory,
  itemChecked,
  itemName,
  itemQuantity,
  itemStore,
  deleteGroceryItem,
  restoreGroceryItem,
  updateGroceryItemQuantity,
  updateGroceryItemStore,
  type ConsolidatedItem,
} from "@/lib/api"
import { parseQuantityAndUnit, isValidQuantityNumber, pluralizeUnit } from "@/lib/utils"

interface StoreSplitViewProps {
  items: ConsolidatedItem[] | { [key: string]: ConsolidatedItem[] } | { items: ConsolidatedItem[] }
  allStores?: string[]
  onRefresh?: () => void
}

type StoreGroup = {
  store: string
  categories: { category: string; items: ConsolidatedItem[] }[]
  total: number
  done: number
}

// A small palette rotation so each store column gets its own accent stripe.
const STORE_ACCENTS = [
  "var(--color-primary)",
  "var(--color-accent)",
  "var(--color-chart-3)",
  "var(--color-chart-4)",
  "var(--color-chart-5)",
]

export function StoreSplitView({ items, allStores = ["King Soopers", "Trader Joe's", "Whole Foods"], onRefresh }: StoreSplitViewProps) {
  const [checkedOverrides, setCheckedOverrides] = useState<Record<number, boolean>>({})
  const [copiedStore, setCopiedStore] = useState<string | null>(null)
  const [showExactAmounts, setShowExactAmounts] = useState(false)

  const [movingItem, setMovingItem] = useState<ConsolidatedItem | null>(null)
  const [editingItemId, setEditingItemId] = useState<number | null>(null)
  const [editQuantityText, setEditQuantityText] = useState("")

  const handleSaveQuantity = async (item: ConsolidatedItem) => {
    const newNum = editQuantityText.trim()
    if (!newNum) {
      setEditingItemId(null)
      return
    }

    if (!isValidQuantityNumber(newNum)) {
      alert("Please enter a valid positive number or fraction (e.g., 2, 0.5, 1/2, or 1 1/2).")
      return
    }

    const { numeric: currentNum, unit } = parseQuantityAndUnit(item.quantity_display)
    const newFullDisplay = pluralizeUnit(newNum, unit)
    const currentFullDisplay = item.quantity_display || currentNum || "0"

    // If nothing changed, exit edit mode
    if (newFullDisplay === currentFullDisplay) {
      setEditingItemId(null)
      return
    }

    const confirmed = window.confirm(
      `Are you sure you want to update quantity of ${itemName(item)} from ${currentFullDisplay} to ${newFullDisplay}?`
    )
    if (!confirmed) return

    try {
      await updateGroceryItemQuantity(item.id, newFullDisplay)
      setEditingItemId(null)
      onRefresh?.()
    } catch {
      alert("Failed to update item quantity")
    }
  }

  const handleMoveItem = async (item: ConsolidatedItem, targetStore: string, saveDefault: boolean = false) => {
    try {
      await updateGroceryItemStore(item.id, targetStore, saveDefault)
      setMovingItem(null)
      onRefresh?.()
    } catch {
      alert("Failed to move item store")
    }
  }

  const handleDeleteItem = async (item: ConsolidatedItem) => {
    const confirmed = window.confirm(`Are you sure you want to delete "${itemName(item)}"?`)
    if (!confirmed) return

    try {
      await deleteGroceryItem(item.id)
      onRefresh?.()
    } catch {
      alert("Failed to delete item")
    }
  }

  // 🛡️ Bulletproof normalizer: handles arrays, API response wrappers, or dictionaries safely
  const safeItems = useMemo<ConsolidatedItem[]>(() => {
    if (Array.isArray(items)) return items
    if (items && typeof items === "object") {
      // Case A: API response wrapper { status: "ok", items: [...] }
      if ("items" in items && Array.isArray((items as any).items)) {
        return (items as any).items
      }
      // Case B: Store-grouped dictionary { "King Soopers": [...], "Whole Foods": [...] }
      return Object.values(items).flat() as ConsolidatedItem[]
    }
    return []
  }, [items]) 

  const copyStore = async (store: string, storeItems: ConsolidatedItem[]) => {
    const ok = await copyToClipboard(formatItemsForKeep(storeItems))
    if (ok) {
      setCopiedStore(store)
      setTimeout(() => setCopiedStore((s) => (s === store ? null : s)), 2000)
    }
  }

  const groups = useMemo<StoreGroup[]>(() => {
    const byStore = new Map<string, ConsolidatedItem[]>()
    // Use safeItems instead of items here:
    for (const item of safeItems) {
      const store = itemStore(item)
      if (!byStore.has(store)) byStore.set(store, [])
      byStore.get(store)!.push(item)
    }

    return Array.from(byStore.entries()).map(([store, storeItems]) => {
      const byCategory = new Map<string, ConsolidatedItem[]>()
      for (const item of storeItems) {
        const cat = itemCategory(item)
        if (!byCategory.has(cat)) byCategory.set(cat, [])
        byCategory.get(cat)!.push(item)
      }

      const categories = Array.from(byCategory.entries())
        .map(([category, catItems]) => ({ category, items: catItems }))
        .sort((a, b) => a.category.localeCompare(b.category))

      const done = storeItems.filter(
        (i) => checkedOverrides[i.id] ?? itemChecked(i),
      ).length

      return { store, categories, total: storeItems.length, done }
    })
  }, [safeItems, checkedOverrides])

  const toggleItem = async (item: ConsolidatedItem) => {
    const next = !(checkedOverrides[item.id] ?? itemChecked(item))
    setCheckedOverrides((prev) => ({ ...prev, [item.id]: next }))
    try {
      await fetch(apiUrl(`/grocery-list/items/${item.id}/toggle`), {
        method: "PATCH",
      })
    } catch {
      // Revert optimistic update if the backend call fails.
      setCheckedOverrides((prev) => ({ ...prev, [item.id]: !next }))
    }
  }

  if (safeItems.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-border bg-card py-20 text-center">
        <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-secondary">
          <ShoppingCart className="h-6 w-6 text-muted-foreground" />
        </div>
        <p className="font-display text-lg font-semibold text-foreground">Your weekly list is empty</p>
        <p className="mt-1 max-w-sm text-sm text-muted-foreground">
          Generate a list from your saved recipes to see items routed across stores and aisles.
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-end">
        <button
          type="button"
          onClick={() => setShowExactAmounts((prev) => !prev)}
          className="flex items-center gap-1.5 rounded-lg border border-border bg-card px-3 py-1.5 text-xs font-medium text-foreground shadow-sm transition hover:bg-secondary"
        >
          <Scale className="h-3.5 w-3.5 text-muted-foreground" />
          <span>{showExactAmounts ? "View: Recipe Exact" : "View: Store Estimate"}</span>
        </button>
      </div>
      <div className="grid gap-5 md:grid-cols-2">
        {groups.map((group, index) => {
          const accent = STORE_ACCENTS[index % STORE_ACCENTS.length]
          const pct = group.total ? Math.round((group.done / group.total) * 100) : 0
          return (
            <section
              key={group.store}
              className="overflow-hidden rounded-2xl border border-border bg-card shadow-sm"
            >
              <header
                className="flex items-center gap-3 border-b border-border px-5 py-4"
                style={{ boxShadow: `inset 4px 0 0 ${accent}` }}
              >
                <div
                  className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg"
                  style={{ backgroundColor: accent, color: "var(--color-primary-foreground)" }}
                >
                  <Store className="h-4 w-4" />
                </div>
                <div className="min-w-0 flex-1">
                  <h3 className="truncate font-display text-base font-semibold text-foreground">
                    {group.store}
                  </h3>
                  <p className="text-xs text-muted-foreground">
                    {group.done} of {group.total} gathered
                  </p>
                </div>
                <div className="text-right">
                  <span className="font-display text-lg font-semibold tabular-nums text-foreground">
                    {pct}%
                  </span>
                </div>
                <button
                  type="button"
                  onClick={() => copyStore(group.store, group.categories.flatMap((c) => c.items))}
                  aria-label={`Copy ${group.store} list for Google Keep`}
                  title="Copy list for Google Keep"
                  className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-border bg-card text-foreground transition hover:bg-secondary"
                >
                  {copiedStore === group.store ? (
                    <ClipboardCheck className="h-4 w-4 text-primary" />
                  ) : (
                    <ClipboardList className="h-4 w-4" />
                  )}
                </button>
              </header>

              <div className="divide-y divide-border">
                {group.categories.map((cat) => (
                  <div key={cat.category} className="px-5 py-4">
                    <p className="mb-2.5 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                      {cat.category}
                    </p>
                    <ul className="space-y-1">
                      {cat.items.map((item) => {
                        const isChecked = checkedOverrides[item.id] ?? itemChecked(item)
                        const qty = showExactAmounts && item.original_quantity_display
                          ? item.original_quantity_display
                          : itemQuantity(item)
                        return (
                          <li key={item.id}>
                            <div className="group flex w-full items-center gap-3 rounded-lg px-2 py-1.5 text-left transition hover:bg-secondary">
                              <button
                                type="button"
                                onClick={() => toggleItem(item)}
                                aria-pressed={isChecked}
                                className="flex items-center gap-3 flex-1 min-w-0 text-left"
                              >
                                <span
                                  className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-md border transition ${
                                    isChecked
                                      ? "border-primary bg-primary text-primary-foreground"
                                      : "border-border bg-card group-hover:border-primary"
                                  }`}
                                >
                                  {isChecked && <Check className="h-3.5 w-3.5" />}
                                </span>

                                {/* Item Name & Recipe Provenance Column */}
                                <div className="flex flex-col flex-1 min-w-0">
                                  <span
                                    className={`text-sm transition truncate ${
                                      isChecked
                                        ? "text-muted-foreground line-through"
                                        : "text-foreground"
                                    }`}
                                  >
                                    {itemName(item)}
                                  </span>
                                  {item.recipes && item.recipes.length > 0 && (
                                    <span className="text-[11px] text-muted-foreground/70 truncate">
                                      From: {item.recipes.join(", ")}
                                    </span>
                                  )}
                                </div>
                              </button>

                              {item.dirty_dozen && (
                                <span
                                  title="Dirty Dozen — buy organic"
                                  className="flex items-center gap-1 rounded-full bg-accent/20 px-2 py-0.5 text-[10px] font-medium text-accent-foreground shrink-0"
                                >
                                  <Leaf className="h-3 w-3" /> Organic
                                </span>
                              )}

                              {/* Quantity Editing and Original Quantity Display */}
                              <div className="flex items-center gap-1.5 shrink-0">
                                {editingItemId === item.id ? (
                                  <div className="flex items-center gap-1">
                                    <input
                                      type="text"
                                      title="Enter new numeric quantity"
                                      placeholder="Qty"
                                      className="h-6 w-14 rounded border border-border bg-background px-1.5 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                                      value={editQuantityText}
                                      onChange={(e) => setEditQuantityText(e.target.value)}
                                      autoFocus
                                      onKeyDown={(e) => {
                                        if (e.key === "Enter") handleSaveQuantity(item)
                                        if (e.key === "Escape") setEditingItemId(null)
                                      }}
                                    />
                                    {parseQuantityAndUnit(item.quantity_display).unit && (
                                      <span className="text-xs text-muted-foreground font-medium select-none">
                                        {parseQuantityAndUnit(item.quantity_display).unit}
                                      </span>
                                    )}
                                    <button
                                      type="button"
                                      onClick={() => handleSaveQuantity(item)}
                                      className="flex h-6 w-6 items-center justify-center rounded bg-primary text-primary-foreground ml-1"
                                    >
                                      <SaveIcon className="h-3 w-3" />
                                    </button>
                                  </div>
                                ) : (
                                  <div className="flex items-center gap-1">
                                    {qty && (
                                      <span className="text-xs tabular-nums text-muted-foreground">
                                        {qty}
                                      </span>
                                    )}
                                    {item.original_quantity_display && item.original_quantity_display !== item.quantity_display && (
                                      <span className="text-[10px] text-muted-foreground/60 line-through">
                                        (was {item.original_quantity_display})
                                      </span>
                                    )}
                                    <button
                                      type="button"
                                      title="Edit quantity"
                                      onClick={() => {
                                        const { numeric } = parseQuantityAndUnit(item.quantity_display)
                                        setEditingItemId(item.id)
                                        setEditQuantityText(numeric)
                                      }}
                                      className="p-1 text-muted-foreground/70 hover:text-foreground opacity-100 sm:opacity-0 sm:group-hover:opacity-100 transition-opacity"
                                    >
                                      <Edit2 className="h-3 w-3" />
                                    </button>
                                  </div>
                                )}
                              </div>

                              {/* Actions: Move Store & Soft Delete */}
                              <div className="flex items-center gap-1 shrink-0 opacity-100 sm:opacity-0 sm:group-hover:opacity-100 transition-opacity">
                                <button
                                  type="button"
                                  title="Move to another store"
                                  onClick={() => setMovingItem(movingItem?.id === item.id ? null : item)}
                                  className="p-1 text-muted-foreground hover:text-foreground rounded hover:bg-secondary"
                                >
                                  <ArrowRightLeft className="h-3.5 w-3.5" />
                                </button>
                                <button
                                  type="button"
                                  title="Delete item"
                                  onClick={() => handleDeleteItem(item)}
                                  className="p-1 text-destructive/70 hover:text-destructive rounded hover:bg-destructive/10"
                                >
                                  <Trash2 className="h-3.5 w-3.5" />
                                </button>
                              </div>
                            </div>

                            {/* Quick Store Selector Dropdown */}
                            {movingItem?.id === item.id && (
                              <div className="mt-2 ml-8 p-2 rounded-lg border border-border bg-popover shadow-md flex flex-wrap items-center gap-1.5 text-xs">
                                <span className="text-muted-foreground font-medium mr-1">Move to:</span>
                                {allStores.map((st) => (
                                  <button
                                    key={st}
                                    type="button"
                                    onClick={() => handleMoveItem(item, st)}
                                    className="px-2 py-1 rounded bg-secondary hover:bg-primary hover:text-primary-foreground transition text-foreground"
                                  >
                                    {st}
                                  </button>
                                ))}
                              </div>
                            )}
                          </li>
                        )
                      })}
                    </ul>
                  </div>
                ))}
              </div>
            </section>
          )
        })}
      </div>
    </div>
  )
}
