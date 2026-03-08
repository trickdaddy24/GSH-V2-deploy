import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import {
  useReactTable, getCoreRowModel, flexRender,
  createColumnHelper,
} from '@tanstack/react-table'
import { Search, Plus, ChevronLeft, ChevronRight } from 'lucide-react'
import { getSubscribers, createSubscriber, Subscriber } from '../lib/api'
import { formatCurrency, formatDate } from '../lib/utils'
import StatusBadge from '../components/StatusBadge'
import Button from '../components/ui/Button'
import Input from '../components/ui/Input'

const col = createColumnHelper<Subscriber>()

const columns = [
  col.accessor('id', { header: 'ID', size: 110 }),
  col.accessor('username', { header: 'Username' }),
  col.accessor('package_name', { header: 'Package' }),
  col.accessor('price', { header: 'Price', cell: i => formatCurrency(i.getValue()) }),
  col.accessor('due_date', { header: 'Due Date', cell: i => formatDate(i.getValue()) }),
  col.accessor('status', {
    header: 'Status',
    cell: i => <StatusBadge status={i.getValue()} isActive={i.row.original.is_active} />,
  }),
  col.accessor('last_payment', { header: 'Last Payment', cell: i => formatDate(i.getValue()) }),
]

export default function Subscribers() {
  const navigate = useNavigate()
  const qc = useQueryClient()
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [includeInactive, setIncludeInactive] = useState(false)
  const [page, setPage] = useState(1)
  const [showAdd, setShowAdd] = useState(false)

  const { data, isLoading } = useQuery({
    queryKey: ['subscribers', search, statusFilter, includeInactive, page],
    queryFn: () => getSubscribers({ search, status: statusFilter || undefined, include_inactive: includeInactive, page, page_size: 50 }),
  })

  const addMut = useMutation({
    mutationFn: createSubscriber,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['subscribers'] }); setShowAdd(false) },
    onError: (e: Error) => alert(e.message),
  })

  const table = useReactTable({
    data: data?.subscribers ?? [],
    columns,
    getCoreRowModel: getCoreRowModel(),
    manualPagination: true,
    pageCount: data?.total_pages ?? 1,
  })

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-gray-900 dark:text-slate-100">Subscribers</h1>
        <Button size="sm" onClick={() => setShowAdd(v => !v)}>
          <Plus size={14} /> Add Subscriber
        </Button>
      </div>

      {showAdd && <AddForm onSubmit={d => addMut.mutate(d)} loading={addMut.isPending} />}

      {/* Filters */}
      <div className="flex flex-wrap gap-2">
        <div className="relative flex-1 min-w-48">
          <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-400 dark:text-slate-500" />
          <Input
            className="pl-8"
            placeholder="Search username / email…"
            value={search}
            onChange={e => { setSearch(e.target.value); setPage(1) }}
          />
        </div>
        <select
          className="rounded-md border px-3 py-1.5 text-sm transition-colors focus:outline-none focus:ring-2 focus:ring-brand-500
                     bg-white border-gray-300 text-gray-700
                     dark:bg-slate-800 dark:border-slate-700 dark:text-slate-300"
          value={statusFilter}
          onChange={e => { setStatusFilter(e.target.value); setPage(1) }}
        >
          <option value="">All statuses</option>
          <option value="current">Current</option>
          <option value="due today">Due Today</option>
          <option value="overdue">Overdue</option>
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
            {table.getHeaderGroups().map(hg => (
              <tr key={hg.id}>
                {hg.headers.map(h => (
                  <th key={h.id} className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-slate-500 uppercase tracking-wide">
                    {flexRender(h.column.columnDef.header, h.getContext())}
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody className="divide-y divide-gray-100 dark:divide-slate-800 bg-white dark:bg-slate-950">
            {isLoading ? (
              <tr><td colSpan={columns.length} className="px-3 py-6 text-center text-gray-400 dark:text-slate-500">Loading…</td></tr>
            ) : table.getRowModel().rows.length === 0 ? (
              <tr><td colSpan={columns.length} className="px-3 py-6 text-center text-gray-400 dark:text-slate-500">No subscribers found.</td></tr>
            ) : (
              table.getRowModel().rows.map(row => (
                <tr
                  key={row.id}
                  className="hover:bg-gray-50 dark:hover:bg-slate-800/50 cursor-pointer transition-colors"
                  onClick={() => navigate(`/subscribers/${row.original.id}`)}
                >
                  {row.getVisibleCells().map(cell => (
                    <td key={cell.id} className="px-3 py-2.5 text-gray-700 dark:text-slate-300">
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
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
          <span>
            {data.total} subscribers &bull; page {data.page} of {data.total_pages}
          </span>
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

interface AddFormProps {
  onSubmit: (d: Parameters<typeof createSubscriber>[0]) => void
  loading: boolean
}

function AddForm({ onSubmit, loading }: AddFormProps) {
  const [form, setForm] = useState({
    username: '', email: '', phone: '', package_id: '', due_date: '', custom_price: '',
  })
  const set = (k: string) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm(f => ({ ...f, [k]: e.target.value }))

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
      <div><label className="text-xs text-gray-500 dark:text-slate-400 mb-1 block">Username *</label><Input required value={form.username} onChange={set('username')} placeholder="john_doe" /></div>
      <div><label className="text-xs text-gray-500 dark:text-slate-400 mb-1 block">Email</label><Input type="email" value={form.email} onChange={set('email')} placeholder="john@example.com" /></div>
      <div><label className="text-xs text-gray-500 dark:text-slate-400 mb-1 block">Phone</label><Input value={form.phone} onChange={set('phone')} placeholder="+1 555-0100" /></div>
      <div><label className="text-xs text-gray-500 dark:text-slate-400 mb-1 block">Package ID *</label><Input required value={form.package_id} onChange={set('package_id')} placeholder="e.g. P1" /></div>
      <div><label className="text-xs text-gray-500 dark:text-slate-400 mb-1 block">Due Date *</label><Input required type="date" value={form.due_date} onChange={set('due_date')} /></div>
      <div><label className="text-xs text-gray-500 dark:text-slate-400 mb-1 block">Custom Price ($)</label><Input type="number" step="0.01" value={form.custom_price} onChange={set('custom_price')} placeholder="Leave blank for default" /></div>
      <div className="col-span-full flex justify-end">
        <Button type="submit" disabled={loading}>{loading ? 'Saving…' : 'Create Subscriber'}</Button>
      </div>
    </form>
  )
}
