"use client"

import { useState } from "react"
import { X, Edit2, Trash2, ArrowRightLeft, Check as SaveIcon } from "lucide-react"
import {
  deleteGroceryItem,
  updateGroceryItemQuantity,
  updateGroceryItemStore,
  itemName,
  type ConsolidatedItem,
} from "@/lib/api"
import { parseQuantityAndUnit, isValidQuantityNumber, pluralizeUnit } from "@/lib/utils"

interface KitchenStaplesModalProps {
  isOpen: boolean
  onClose: () => void
  staples: ConsolidatedItem[]
  allStores?: string[]
  onRefresh?: () => void
}

export function KitchenStaplesModal({
  isOpen,
  onClose,
  staples,
  allStores = ["King Soopers", "Trader Joe's", "Whole Foods"],
  onRefresh,
}: KitchenStaplesModalProps) {
  const [movingItem, setMovingItem] = useState<ConsolidatedItem | null>(null)
  const [editingItemId, setEditingItemId] = useState<number | null>(null)
  const [editQuantityText, setEditQuantityText] = useState("")

  if (!isOpen) return null

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

  const handleMoveItem = async (item: ConsolidatedItem, targetStore: string) => {
    try {
      await updateGroceryItemStore(item.id, targetStore, false)
      setMovingItem(null)
      onRefresh?.()
    } catch {
      alert("Failed to move item store")
    }
  }

  const handleDeleteItem = async (item: ConsolidatedItem) => {
    if (!window.confirm(`Are you sure you want to delete "${itemName(item)}"?`)) return
    try {
      await deleteGroceryItem(item.id)
      onRefresh?.()
    } catch {
      alert("Failed to delete item")
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-xs">
      <div className="relative w-full max-w-lg rounded-xl border border-border bg-card p-6 shadow-lg">
        <div className="flex items-center justify-between pb-4 border-b border-border">
          <h3 className="font-display text-lg font-semibold text-foreground">
            Kitchen Staples
          </h3>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-1 text-muted-foreground transition hover:bg-secondary hover:text-foreground"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="max-h-[60vh] overflow-y-auto py-4 space-y-3">
          <p className="text-sm text-muted-foreground bg-secondary/50 p-3 rounded-lg border border-border">
            Ensure that you have these items at home, they have been omitted from the grocery lists but are needed for the recipes selected.
          </p>
          {staples.length === 0 ? (
            <p className="text-center text-sm text-muted-foreground py-8">
              No kitchen staples required for this week&apos;s route.
            </p>
          ) : (
            staples.map((staple) => (
              <div
                key={staple.id || staple.canonical_name}
                className="group flex flex-col gap-1 py-2 border-b border-border last:border-b-0"
              >
                <div className="flex items-center justify-between">
                  <span className="font-medium text-foreground">
                    {staple.canonical_name}
                  </span>

                  <div className="flex items-center gap-2">
                    {editingItemId === staple.id ? (
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
                            if (e.key === "Enter") handleSaveQuantity(staple)
                            if (e.key === "Escape") setEditingItemId(null)
                          }}
                        />
                        {parseQuantityAndUnit(staple.quantity_display).unit && (
                          <span className="text-xs text-muted-foreground font-medium select-none">
                            {parseQuantityAndUnit(staple.quantity_display).unit}
                          </span>
                        )}
                        <button
                          type="button"
                          onClick={() => handleSaveQuantity(staple)}
                          className="flex h-6 w-6 items-center justify-center rounded bg-primary text-primary-foreground ml-1"
                        >
                          <SaveIcon className="h-3 w-3" />
                        </button>
                      </div>
                    ) : (
                      <div className="flex items-center gap-1">
                        <span className="text-sm text-muted-foreground">
                          {staple.quantity_display}
                        </span>
                        {staple.original_quantity_display &&
                          staple.original_quantity_display !== staple.quantity_display && (
                            <span className="text-[10px] text-muted-foreground/60 line-through">
                              (was {staple.original_quantity_display})
                            </span>
                          )}
                        <button
                          type="button"
                          title="Edit quantity"
                          onClick={() => {
                            const { numeric } = parseQuantityAndUnit(staple.quantity_display)
                            setEditingItemId(staple.id)
                            setEditQuantityText(numeric)
                          }}
                          className="p-1 text-muted-foreground/70 hover:text-foreground opacity-100 sm:opacity-0 sm:group-hover:opacity-100 transition-opacity"
                        >
                          <Edit2 className="h-3 w-3" />
                        </button>
                      </div>
                    )}

                    <div className="flex items-center gap-1 opacity-100 sm:opacity-0 sm:group-hover:opacity-100 transition-opacity">
                      <button
                        type="button"
                        title="Move to store list"
                        onClick={() => setMovingItem(movingItem?.id === staple.id ? null : staple)}
                        className="p-1 text-muted-foreground hover:text-foreground rounded hover:bg-secondary"
                      >
                        <ArrowRightLeft className="h-3.5 w-3.5" />
                      </button>
                      <button
                        type="button"
                        title="Delete item"
                        onClick={() => handleDeleteItem(staple)}
                        className="p-1 text-destructive/70 hover:text-destructive rounded hover:bg-destructive/10"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </div>
                </div>

                {movingItem?.id === staple.id && (
                  <div className="mt-1 p-2 rounded-lg border border-border bg-popover shadow-md flex flex-wrap items-center gap-1.5 text-xs">
                    <span className="text-muted-foreground font-medium mr-1">Move to store:</span>
                    {allStores.map((st) => (
                      <button
                        key={st}
                        type="button"
                        onClick={() => handleMoveItem(staple, st)}
                        className="px-2 py-1 rounded bg-secondary hover:bg-primary hover:text-primary-foreground transition text-foreground"
                      >
                        {st}
                      </button>
                    ))}
                  </div>
                )}

                {staple.recipes && staple.recipes.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-1">
                    {staple.recipes.map((recipeName, index) => (
                      <span
                        key={index}
                        className="rounded-md bg-secondary px-1.5 py-0.5 text-xs text-muted-foreground"
                      >
                        {recipeName}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))
          )}
        </div>

        <div className="flex justify-end pt-4 border-t border-border">
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition hover:opacity-90"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  )
}
