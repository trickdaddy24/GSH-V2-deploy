import { useRef, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { Search, Plus, ChevronLeft, ChevronRight, Download, Upload, ChevronUp, ChevronDown } from 'lucide-react'
import { getSubscribers, createSubscriber, exportSubscribers, importSubscribers, Subscriber } from '../lib/api'
import { formatCurrency, formatDate } from '../lib/utils'
import { PACKAGES, STATUSES } from '../lib/constants'
import { useToast } from '../lib/ToastContext'
import StatusBadge from '../components/StatusBadge'
import Button from '../components/ui/Button'
import Input from '../components/ui/Input'

type SortKey = 'id' | 'username' | 'due_date' | 'price' | 'status'

const COLUMNS: { key: SortKey | null; label: string; render?: (s: Subscriber) => React.ReactNode }[] = [
  { key: 'id',           label: 'ID' },
  { key: 'username',     label: 'Username' },
  { key: null,           label: 'Package' },
  { key: 'price',        label: 'Price',        render: s => formatCurrency(s.price) },
  { key: 'due_date',     label: 'Due Date',     render: s => formatDate(s.due_date) },
  { key: 'status',       label: 'Status',       render: s => <StatusBadge status={s.status} isActive={s.is_active} /> },
  { key: null,           label: 'Last Payment', render: s => formatDate(s.last_payment) },
]

function cellValue(s: Subscriber, key: SortKey | null, label: string): React.ReactNode {
  const col = COLUMNS.find(c => c.label === label)
  if (col?.render) return col.render(s)
  if (label === 'Package') return s.package_name
  if (key) return String(s[key] ?? '—')
  return '—'
}

export default function Subscribers() {
  const navigate = useNavigate()
  const qc = useQueryClient()
  const { addToast } = useToast()
  const fileRef = useRef<HTMLInputElement>(null)

  const [search, setSearch]               = useState('')
  const [statusFilter, setStatusFilter]   = useState('')
  const [includeInactive, setIncludeInactive] = useState(false)
  const [page, setPage]                   = useState(1)
  const [showAdd, setShowAdd]             = useState(false)
  const [sortBy, setSortBy]               = useState<SortKey>('id')
  const [sortDir, setSortDir]             = useState<'asc' | 'desc'>('asc')

  const { data, isLoading } = useQuery({
    queryKey: ['subscribers', search, statusFilter, includeInactive, page, sortBy, sortDir],
    queryFn: () => getSubscribers({
      search, status: statusFilter || undefined,
      include_inactive: includeInactive,
      page, page_size: 50,
      sort_by: sortBy, sort_dir: sortDir,
    }),
  })

  const addMut = useMutation({
    mutationFn: createSubscriber,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['subscribers'] }); setShowAdd(false) },
  })

  const handleSort = (key: SortKey | null) => {
    if (!key) return
    if (key === sortBy) setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    else { setSortBy(key); setSortDir('asc') }
    setPage(1)
  }

  const handleExport = async () => {
    try {
      const data = await exportSubscribers()
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `gsh-export-${new Date().toISOString().slice(0, 10)}.json`
      a.click()
      URL.revokeObjectURL(url)
      addToast(`Exported ${data.length} subscribers`, 'success')
    } catch { /* toast shown by interceptor */ }
  }

  const handleImport = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    e.target.value = ''
    let json: unknown[]
    try {
      const text = await file.text()
      const parsed = JSON.parse(text)
      if (!Array.isArray(parsed)) { addToast('Invalid file: expected a JSON array', 'error'); return }
      json = parsed
    } catch {
      addToast('Invalid JSON file — could not parse', 'error')
      return
    }
    try {
      const result = await importSubscribers(json)
      if (result.error) {
        addToast(`Import failed: ${result.error}`, 'error')
      } else if (result.imported === 0) {
        const reason = result.skip_reasons?.[0] ?? 'check file format'
        addToast(`Nothing imported — ${reason}`, 'error')
      } else if (result.skipped > 0) {
        addToast(`Imported ${result.imported}, skipped ${result.skipped} — see console for details`, 'info')
        console.warn('Skipped entries:', result.skip_reasons)
        qc.invalidateQueries({ queryKey: ['subscribers'] })
      } else {
        addToast(`Successfully imported ${result.imported} subscriber${result.imported !== 1 ? 's' : ''}`, 'success')
        qc.invalidateQueries({ queryKey: ['subscribers'] })
      }
    } catch {
      // axios interceptor already showed the error toast
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-gray-900 dark:text-slate-100">
          Subscribers
          {data && <span className="ml-2 text-sm font-normal text-gray-400 dark:text-slate-500">({data.total})</span>}
        </h1>
        <div className="flex gap-2">
          <Button size="sm" variant="secondary" onClick={handleExport}>
            <Download size={14} /> Export
          </Button>
          <Button size="sm" variant="secondary" onClick={() => fileRef.current?.click()}>
            <Upload size={14} /> Import
          </Button>
          <input ref={fileRef} type="file" accept=".json" className="hidden" onChange={handleImport} />
          <Button size="sm" onClick={() => setShowAdd(v => !v)}>
            <Plus size={14} /> Add Subscriber
          </Button>
        </div>
      </div>

      {showAdd && <AddForm onSubmit={d => addMut.mutate(d)} loading={addMut.isPending} />}

      {/* Filters */}
      <div className="flex flex-wrap gap-2">
        <div className="relative flex-1 min-w-48">
          <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-400 dark:text-slate-500" />
          <Input
            className="pl-8"
            placeholder="Search username…"
            value={search}
            onChange={e => { setSearch(e.target.value); setPage(1) }}
          />
        </div>
        <select
          className="rounded-md border px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500
                     bg-white border-gray-300 text-gray-700
                     dark:bg-slate-800 dark:border-slate-700 dark:text-slate-300"
          value={statusFilter}
          onChange={e => { setStatusFilter(e.target.value); setPage(1) }}
        >
          <option value="">All statuses</option>
          {STATUSES.map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
        </select>
        <label className="flex items-center gap-2 text-sm text-gray-500 dark:text-slate-400 cursor-pointer">
          <input
            type="checkbox"
            className="rounded"
            checked={includeInactive}
            onChange={e => { setIncludeInactive(e.target.checked); setPage(1) }}
          />
          Show Inactive
        </label>
      </div>

      {/* Table */}
      <div className="rounded-xl border border-gray-200 dark:border-slate-800 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 dark:bg-slate-900">
            <tr>
              {COLUMNS.map(col => (
                <th
                  key={col.label}
                  onClick={() => handleSort(col.key)}
                  className={`px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-slate-500 uppercase tracking-wide select-none
                    ${col.key ? 'cursor-pointer hover:text-gray-800 dark:hover:text-slate-300' : ''}`}
                >
                  <span className="inline-flex items-center gap-1">
                    {col.label}
                    {col.key === sortBy && (
                      sortDir === 'asc' ? <ChevronUp size={12} /> : <ChevronDown size={12} />
                    )}
                  </span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100 dark:divide-slate-800 bg-white dark:bg-slate-950">
            {isLoading ? (
              <tr><td colSpan={COLUMNS.length} className="px-3 py-6 text-center text-gray-400 dark:text-slate-500">Loading…</td></tr>
            ) : !data?.subscribers.length ? (
              <tr><td colSpan={COLUMNS.length} className="px-3 py-6 text-center text-gray-400 dark:text-slate-500">No subscribers found.</td></tr>
            ) : (
              data.subscribers.map(sub => (
                <tr
                  key={sub.id}
                  className="hover:bg-gray-50 dark:hover:bg-slate-800/50 cursor-pointer transition-colors"
                  onClick={() => navigate(`/subscribers/${sub.id}`)}
                >
                  {COLUMNS.map(col => (
                    <td key={col.label} className="px-3 py-2.5 text-gray-700 dark:text-slate-300">
                      {cellValue(sub, col.key, col.label)}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {data && data.total_pages > 1 && (
        <div className="flex items-center justify-between text-sm text-gray-500 dark:text-slate-400">
          <span>{data.total} subscribers &bull; page {data.page} of {data.total_pages}</span>
          <div className="flex gap-1">
            <Button variant="ghost" size="sm" disabled={page <= 1} onClick={() => setPage(p => p - 1)}>
              <ChevronLeft size={14} />
            </Button>
            <Button variant="ghost" size="sm" disabled={page >= data.total_pages} onClick={() => setPage(p => p + 1)}>
              <ChevronRight size={14} />
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}

function AddForm({ onSubmit, loading }: { onSubmit: (d: Parameters<typeof createSubscriber>[0]) => void; loading: boolean }) {
  const [form, setForm] = useState({ username: '', email: '', phone: '', package_id: '0', due_date: '', custom_price: '' })
  const set = (k: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setForm(f => ({ ...f, [k]: e.target.value }))
  const selectedPkg = PACKAGES.find(p => p.id === form.package_id)

  const submit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit({
      username: form.username,
      email: form.email || undefined,
      phone: form.phone || undefined,
      package_id: form.package_id,
      due_date: form.due_date,
      custom_price: form.custom_price ? Number(form.custom_price) : undefined,
    })
  }

  return (
    <form onSubmit={submit} className="rounded-xl border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-900 p-4 grid grid-cols-2 gap-3 md:grid-cols-3">
      <div>
        <label className="text-xs text-gray-500 dark:text-slate-400 mb-1 block">Username *</label>
        <Input required value={form.username} onChange={set('username')} placeholder="john_doe" />
      </div>
      <div>
        <label className="text-xs text-gray-500 dark:text-slate-400 mb-1 block">Email</label>
        <Input type="email" value={form.email} onChange={set('email')} placeholder="john@example.com" />
      </div>
      <div>
        <label className="text-xs text-gray-500 dark:text-slate-400 mb-1 block">Phone</label>
        <Input value={form.phone} onChange={set('phone')} placeholder="+1 555-0100" />
      </div>
      <div>
        <label className="text-xs text-gray-500 dark:text-slate-400 mb-1 block">Package *</label>
        <select
          required
          value={form.package_id}
          onChange={set('package_id')}
          className="w-full rounded-md border px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500
                     bg-white border-gray-300 text-gray-700 dark:bg-slate-800 dark:border-slate-700 dark:text-slate-300"
        >
          {PACKAGES.map(p => (
            <option key={p.id} value={p.id}>
              {p.name}{p.price !== null ? ` — $${p.price}/mo` : ''}
            </option>
          ))}
        </select>
      </div>
      <div>
        <label className="text-xs text-gray-500 dark:text-slate-400 mb-1 block">Due Date *</label>
        <Input required type="date" value={form.due_date} onChange={set('due_date')} />
      </div>
      {selectedPkg?.price === null && (
        <div>
          <label className="text-xs text-gray-500 dark:text-slate-400 mb-1 block">Custom Price ($) *</label>
          <Input required type="number" step="0.01" value={form.custom_price} onChange={set('custom_price')} placeholder="e.g. 20" />
        </div>
      )}
      <div className="col-span-full flex justify-end">
        <Button type="submit" disabled={loading}>{loading ? 'Saving…' : 'Create Subscriber'}</Button>
      </div>
    </form>
  )
}
