"use client"

import { useState } from "react"
import { ShoppingBag, X, Check, Plus, Loader2 } from "lucide-react"
import { quickAddGroceryItem } from "@/lib/api"

interface FrequentItemsModalProps {
  isOpen: boolean
  onClose: () => void
  stores: string[]
  onRefresh?: () => void
}

interface StagedItem {
  name: string
  category: string
  defaultQuantity?: string
}

const FREQUENT_ITEMS: StagedItem[] = [
  { name: "Eggs", category: "Dairy & Eggs", defaultQuantity: "1 dozen" },
  { name: "Milk", category: "Dairy & Eggs", defaultQuantity: "1 gal" },
  { name: "Yogurt", category: "Dairy & Eggs" },
  { name: "Butter", category: "Dairy & Eggs" },
  { name: "Bread", category: "Bakery" },
  { name: "Coffee", category: "Pantry" },
  { name: "Bananas", category: "Produce", defaultQuantity: "1 bunch" },
  { name: "Apples", category: "Produce", defaultQuantity: "2" },
  { name: "Avocados", category: "Produce" },
]

export function FrequentItemsModal({
  isOpen,
  onClose,
  stores,
  onRefresh,
}: FrequentItemsModalProps) {
  const [selectedStore, setSelectedStore] = useState(stores[0] || "King Soopers")
  const [stagedNames, setStagedNames] = useState<Set<string>>(new Set())
  const [isSubmitting, setIsSubmitting] = useState(false)

  if (!isOpen) return null

  const toggleStage = (itemName: string) => {
    setStagedNames((prev) => {
      const next = new Set(prev)
      if (next.has(itemName)) {
        next.delete(itemName)
      } else {
        next.add(itemName)
      }
      return next
    })
  }

  const handleAddStagedItems = async () => {
    if (stagedNames.size === 0) {
      onClose()
      return
    }

    setIsSubmitting(true)
    try {
      const itemsToAdd = FREQUENT_ITEMS.filter((item) => stagedNames.has(item.name))
      for (const item of itemsToAdd) {
        await quickAddGroceryItem(
          item.name,
          selectedStore,
          item.category,
          item.defaultQuantity || "1"
        )
      }
      setStagedNames(new Set())
      onRefresh?.()
      onClose()
    } catch {
      alert("Failed to add some frequent items.")
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm">
      <div className="w-full max-w-lg rounded-2xl border border-border bg-card p-6 shadow-xl">
        <div className="flex items-center justify-between pb-4 border-b border-border">
          <div className="flex items-center gap-2">
            <ShoppingBag className="h-5 w-5 text-primary" />
            <h3 className="font-display text-lg font-semibold text-foreground">
              Add Frequent Items
            </h3>
          </div>
          <button
            type="button"
            disabled={isSubmitting}
            onClick={onClose}
            className="rounded-lg p-1 text-muted-foreground hover:bg-secondary disabled:opacity-50"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Store Selector Prompt */}
        <div className="my-4">
          <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1.5">
            Target Store
          </label>
          <select
            value={selectedStore}
            disabled={isSubmitting}
            onChange={(e) => setSelectedStore(e.target.value)}
            className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-primary disabled:opacity-50"
          >
            {stores.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </div>

        {/* Frequent Items Grid (Staging area) */}
        <div className="my-4 max-h-72 overflow-y-auto grid grid-cols-2 gap-2 pr-1">
          {FREQUENT_ITEMS.map((item) => {
            const isStaged = stagedNames.has(item.name)

            return (
              <button
                key={item.name}
                type="button"
                disabled={isSubmitting}
                onClick={() => toggleStage(item.name)}
                className={`flex items-center justify-between gap-2 rounded-lg border px-3 py-2 text-sm font-medium transition ${
                  isStaged
                    ? "border-primary/40 bg-primary/10 text-primary"
                    : "border-border bg-background text-foreground hover:bg-secondary"
                }`}
              >
                <div className="flex flex-col text-left">
                  <span>{item.name}</span>
                  <span className="text-[10px] text-muted-foreground">
                    {item.defaultQuantity ? `${item.defaultQuantity} • ` : ""}
                    {item.category}
                  </span>
                </div>
                {isStaged ? (
                  <Check className="h-4 w-4 shrink-0 text-primary" />
                ) : (
                  <Plus className="h-4 w-4 shrink-0 text-muted-foreground" />
                )}
              </button>
            )
          })}
        </div>

        <div className="flex justify-end gap-2 pt-3 border-t border-border">
          <button
            type="button"
            disabled={isSubmitting}
            onClick={onClose}
            className="rounded-lg border border-border bg-card px-4 py-2 text-sm font-medium text-foreground hover:bg-secondary disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            type="button"
            disabled={isSubmitting || stagedNames.size === 0}
            onClick={handleAddStagedItems}
            className="flex items-center gap-1.5 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
          >
            {isSubmitting ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" /> Adding…
              </>
            ) : (
              `Add ${stagedNames.size > 0 ? `(${stagedNames.size})` : ""}`
            )}
          </button>
        </div>
      </div>
    </div>
  )
}
