import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function parseQuantityAndUnit(displayStr: string | null | undefined): { numeric: string; unit: string } {
  if (!displayStr) return { numeric: "", unit: "" }
  const match = displayStr.trim().match(/^((?:\d+\/\d+|\d+(?:\.\d+)?(?:\s+\d+\/\d+)?))\s*(.*)$/)
  if (match) {
    return { numeric: match[1], unit: match[2] }
  }
  return { numeric: displayStr.trim(), unit: "" }
}

export function isValidQuantityNumber(val: string): boolean {
  const trimmed = val.trim()
  if (!trimmed) return false
  if (/^\d+(?:\.\d+)?$/.test(trimmed)) {
    return parseFloat(trimmed) > 0
  }
  if (/^\d+\/\d+$/.test(trimmed)) {
    const [num, den] = trimmed.split("/").map(Number)
    return den !== 0 && num / den > 0
  }
  if (/^\d+\s+\d+\/\d+$/.test(trimmed)) {
    const [whole, frac] = trimmed.split(/\s+/)
    const [num, den] = frac.split("/").map(Number)
    return den !== 0 && (Number(whole) + num / den) > 0
  }
  return false
}

export function pluralizeUnit(numStr: string, unitStr: string): string {
  if (!unitStr) return numStr
  const num = parseFloat(numStr)
  if (isNaN(num)) return `${numStr} ${unitStr}`

  const pluralMap: Record<string, string> = {
    "cup": "cups", "clove": "cloves", "tablespoon": "tablespoons", "tbsp": "tbsp",
    "teaspoon": "teaspoons", "tsp": "tsp", "ounce": "ounces", "oz": "oz",
    "pound": "pounds", "lb": "lbs", "gram": "grams", "g": "g",
    "kilogram": "kilograms", "kg": "kg", "can": "cans", "bunch": "bunches",
    "head": "heads", "slice": "slices", "pinch": "pinches", "dash": "dashes"
  }

  const singularMap: Record<string, string> = {
    "cups": "cup", "cloves": "clove", "tablespoons": "tablespoon",
    "teaspoons": "teaspoon", "ounces": "ounce", "pounds": "pound",
    "grams": "gram", "kilograms": "kilogram", "cans": "can",
    "bunches": "bunch", "heads": "head", "slices": "slice",
    "pinches": "pinch", "dashes": "dash"
  }

  const lowerUnit = unitStr.toLowerCase()
  if (num === 1.0) {
    const singular = singularMap[lowerUnit] || lowerUnit
    return `${numStr} ${singular}`
  } else {
    const plural = pluralMap[lowerUnit] || (lowerUnit.endsWith("s") ? lowerUnit : `${lowerUnit}s`)
    return `${numStr} ${plural}`
  }
}
