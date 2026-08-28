"use client"

import { X } from "lucide-react"
import type { ConsolidatedItem } from "@/lib/api"

interface KitchenStaplesModalProps {
  isOpen: boolean
  onClose: () => void
  staples: ConsolidatedItem[]
}

export function KitchenStaplesModal({
  isOpen,
  onClose,
  staples,
}: KitchenStaplesModalProps) {
  if (!isOpen) return null

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
                className="flex flex-col gap-1 py-2 border-b border-border last:border-b-0"
              >
                <div className="flex items-center justify-between">
                  <span className="font-medium text-foreground">
                    {staple.canonical_name}
                  </span>
                  <span className="text-sm text-muted-foreground">
                    {staple.quantity_display}
                  </span>
                </div>

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