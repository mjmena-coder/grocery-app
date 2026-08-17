"use client"

import { useMemo, useState } from "react"
import { Store, Check, ShoppingCart, Leaf, ClipboardList, ClipboardCheck } from "lucide-react"
import {
  apiUrl,
  copyToClipboard,
  formatItemsForKeep,
  itemCategory,
  itemChecked,
  itemName,
  itemQuantity,
  itemStore,
  type ConsolidatedItem,
} from "@/lib/api"

interface StoreSplitViewProps {
  items: ConsolidatedItem[] | { [key: string]: ConsolidatedItem[] } | { items: ConsolidatedItem[] }
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

export function StoreSplitView({ items }: StoreSplitViewProps) {
  const [checkedOverrides, setCheckedOverrides] = useState<Record<number, boolean>>({})
  const [copiedStore, setCopiedStore] = useState<string | null>(null)

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
      await fetch(apiUrl(`/grocery/items/${item.id}/toggle`), {
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
                      const qty = itemQuantity(item)
                      return (
                        <li key={item.id}>
                          <button
                            type="button"
                            onClick={() => toggleItem(item)}
                            aria-pressed={isChecked}
                            className="group flex w-full items-center gap-3 rounded-lg px-2 py-1.5 text-left transition hover:bg-secondary"
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

                            {item.dirty_dozen && (
                              <span
                                title="Dirty Dozen — buy organic"
                                className="flex items-center gap-1 rounded-full bg-accent/20 px-2 py-0.5 text-[10px] font-medium text-accent-foreground"
                              >
                                <Leaf className="h-3 w-3" /> Organic
                              </span>
                            )}
                            {qty && (
                              <span className="shrink-0 text-xs tabular-nums text-muted-foreground">
                                {qty}
                              </span>
                            )}
                          </button>
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
  )
}