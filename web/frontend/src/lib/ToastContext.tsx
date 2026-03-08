import { createContext, useCallback, useContext, useState, ReactNode } from 'react'

export type ToastType = 'error' | 'success' | 'info'

interface Toast {
  id: number
  message: string
  type: ToastType
}

interface ToastCtx {
  addToast: (message: string, type?: ToastType) => void
}

const ToastContext = createContext<ToastCtx>({ addToast: () => {} })

export const useToast = () => useContext(ToastContext)

let _nextId = 0

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([])

  const addToast = useCallback((message: string, type: ToastType = 'error') => {
    const id = ++_nextId
    setToasts(t => [...t, { id, message, type }])
    setTimeout(() => setToasts(t => t.filter(x => x.id !== id)), 6000)
  }, [])

  const remove = (id: number) => setToasts(t => t.filter(x => x.id !== id))

  return (
    <ToastContext.Provider value={{ addToast }}>
      {children}
      <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-sm w-full pointer-events-none">
        {toasts.map(t => (
          <div
            key={t.id}
            className={`flex items-start gap-3 px-4 py-3 rounded-lg shadow-lg text-sm text-white pointer-events-auto ${
              t.type === 'error'   ? 'bg-red-600 dark:bg-red-700' :
              t.type === 'success' ? 'bg-emerald-600 dark:bg-emerald-700' :
                                     'bg-blue-600 dark:bg-blue-700'
            }`}
          >
            <span className="flex-1 break-words leading-relaxed">{t.message}</span>
            <button
              onClick={() => remove(t.id)}
              className="text-white/60 hover:text-white text-base leading-none mt-0.5 flex-shrink-0"
            >
              ✕
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  )
}
