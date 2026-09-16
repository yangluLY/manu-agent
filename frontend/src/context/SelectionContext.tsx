import { createContext, useContext, useMemo, useState, type ReactNode } from 'react'

interface SelectionState {
  lineCode?: string
  machineId?: number
}

interface SelectionContextValue extends SelectionState {
  selectLine: (lineCode?: string) => void
  selectMachine: (machineId?: number, lineCode?: string) => void
}

const STORAGE_KEY = 'manu-agent-selection'
const SelectionContext = createContext<SelectionContextValue | null>(null)

function readInitialState(): SelectionState {
  try {
    const value = window.localStorage.getItem(STORAGE_KEY)
    return value ? (JSON.parse(value) as SelectionState) : {}
  } catch {
    return {}
  }
}

export function SelectionProvider({ children }: { children: ReactNode }) {
  const [selection, setSelection] = useState<SelectionState>(readInitialState)

  const update = (next: SelectionState) => {
    setSelection(next)
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next))
  }

  const value = useMemo<SelectionContextValue>(
    () => ({
      ...selection,
      selectLine: (lineCode) => update({ lineCode }),
      selectMachine: (machineId, lineCode) => update({ machineId, lineCode }),
    }),
    [selection],
  )

  return <SelectionContext.Provider value={value}>{children}</SelectionContext.Provider>
}

export function useSelection() {
  const value = useContext(SelectionContext)
  if (!value) throw new Error('useSelection 必须在 SelectionProvider 内使用')
  return value
}
