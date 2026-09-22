"use client"

import { useState } from "react"
import { Plus, Check, ShoppingBag, X } from "lucide-react"
import { quickAddGroceryItem } from "@/lib/api"

interface FrequentItemsModalProps {
  isOpen: boolean
  onClose: () => void
  stores: string[]
  onRefresh?: () => void
}

const FREQUENT_ITEMS = [
  { name: "Eggs", category: "Dairy & Eggs" },
  { name: "Milk", category: "Dairy & Eggs" },
  { name: "Yogurt", category: "Dairy & Eggs" },
  { name: "Butter", category: "Dairy & Eggs" },
  { name: "Cheese", category: "Dairy & Eggs" },
  { name: "Bread", category: "Bakery" },
  { name: "Coffee", category: "Pantry" },
  { name: "Bananas", category: "Produce" },
  { name: "Apples", category: "Produce" },
  { name: "Avocados", category: "Produce" },
  { name: "Onions", category: "Produce" },
  { name: "Garlic", category: "Produce" },
  { name: "Olive Oil", category: "Pantry" },
  { name: "Sparkling Water", category: "Beverages" },
]

export function FrequentItemsModal({
  isOpen,
  onClose,
  stores,
  onRefresh,
}: FrequentItemsModalProps) {
  const [selectedStore, setSelectedStore] = useState(stores[0] || "King Soopers")
  const [addingItem, setAddingItem] = useState<string | null>(null)
  const [addedItems, setAddedItems] = useState<Set<string>>(new Set())

  if (!isOpen) return null

  const handleAddItem = async (item: { name: string; category: string }) => {
    setAddingItem(item.name)
    try {
      await quickAddGroceryItem(item.name, selectedStore, item.category)
      setAddedItems((prev) => new Set(prev).add(item.name))
      onRefresh?.()
    } catch {
      alert(`Failed to add ${item.name}`)
    } finally {
      setAddingItem(null)
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
            onClick={onClose}
            className="rounded-lg p-1 text-muted-foreground hover:bg-secondary"
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
            onChange={(e) => setSelectedStore(e.target.value)}
            className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
          >
            {stores.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </div>

        {/* Frequent Items Grid */}
        <div className="my-4 max-h-72 overflow-y-auto grid grid-cols-2 gap-2 pr-1">
          {FREQUENT_ITEMS.map((item) => {
            const isAdded = addedItems.has(item.name)
            const isLoading = addingItem === item.name

            return (
              <button
                key={item.name}
                type="button"
                disabled={isLoading}
                onClick={() => handleAddItem(item)}
                className={`flex items-center justify-between gap-2 rounded-lg border px-3 py-2 text-sm font-medium transition ${
                  isAdded
                    ? "border-primary/40 bg-primary/10 text-primary"
                    : "border-border bg-background text-foreground hover:bg-secondary"
                }`}
              >
                <div className="flex flex-col text-left">
                  <span>{item.name}</span>
                  <span className="text-[10px] text-muted-foreground">
                    {item.category}
                  </span>
                </div>
                {isAdded ? (
                  <Check className="h-4 w-4 shrink-0 text-primary" />
                ) : (
                  <Plus className="h-4 w-4 shrink-0 text-muted-foreground" />
                )}
              </button>
            )
          })}
        </div>

        <div className="flex justify-end pt-3 border-t border-border">
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  )
}
