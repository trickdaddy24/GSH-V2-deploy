import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, Pencil, UserX, UserCheck, Trash2, Plus } from 'lucide-react'
import {
  getSubscriber, getPayments, updateSubscriber,
  deactivateSubscriber, reactivateSubscriber, deleteSubscriber, recordPayment,
} from '../lib/api'
import { formatCurrency, formatDate } from '../lib/utils'
import { PACKAGES } from '../lib/constants'
import StatusBadge from '../components/StatusBadge'
import { Card, CardHeader, CardTitle } from '../components/ui/Card'
import Button from '../components/ui/Button'
import Input from '../components/ui/Input'

export default function SubscriberDetail() {
  const { accId } = useParams<{ accId: string }>()
  const navigate = useNavigate()
  const qc = useQueryClient()
  const [editing, setEditing] = useState(false)
  const [showPayment, setShowPayment] = useState(false)

  const { data: sub, isLoading } = useQuery({
    queryKey: ['subscriber', accId],
    queryFn: () => getSubscriber(accId!),
    enabled: !!accId,
  })

  const { data: payments } = useQuery({
    queryKey: ['payments', accId],
    queryFn: () => getPayments(accId!),
    enabled: !!accId,
  })

  const qInv = () => {
    qc.invalidateQueries({ queryKey: ['subscriber', accId] })
    qc.invalidateQueries({ queryKey: ['subscribers'] })
  }

  const updateMut  = useMutation({ mutationFn: (f: Record<string, unknown>) => updateSubscriber(accId!, f), onSuccess: () => { qInv(); setEditing(false) }, onError: (e: Error) => alert(e.message) })
  const deactMut   = useMutation({ mutationFn: () => deactivateSubscriber(accId!), onSuccess: qInv, onError: (e: Error) => alert(e.message) })
  const reactMut   = useMutation({ mutationFn: () => reactivateSubscriber(accId!), onSuccess: qInv, onError: (e: Error) => alert(e.message) })
  const deleteMut  = useMutation({ mutationFn: () => deleteSubscriber(accId!), onSuccess: () => navigate('/subscribers'), onError: (e: Error) => alert(e.message) })
  const payMut     = useMutation({
    mutationFn: (body: Parameters<typeof recordPayment>[0]) => recordPayment(body),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['payments', accId] }); qInv(); setShowPayment(false) },
    onError: (e: Error) => alert(e.message),
  })

  if (isLoading) return <p className="text-gray-400 dark:text-slate-400">Loading…</p>
  if (!sub) return <p className="text-red-500">Subscriber not found.</p>

  return (
    <div className="space-y-5 max-w-3xl">
      <div className="flex items-center gap-3">
        <button onClick={() => navigate(-1)} className="text-gray-400 hover:text-gray-700 dark:text-slate-400 dark:hover:text-slate-100 transition-colors">
          <ArrowLeft size={18} />
        </button>
        <h1 className="text-xl font-bold text-gray-900 dark:text-slate-100">{sub.username}</h1>
        <span className="text-gray-400 dark:text-slate-500 text-sm">{sub.id}</span>
        <StatusBadge status={sub.status} isActive={sub.is_active} />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Account Info</CardTitle>
          <div className="flex gap-2">
            <Button size="sm" variant="secondary" onClick={() => setEditing(v => !v)}>
              <Pencil size={12} /> Edit
            </Button>
            {sub.is_active ? (
              <Button size="sm" variant="danger" onClick={() => deactMut.mutate()} disabled={deactMut.isPending}>
                <UserX size={12} /> Deactivate
              </Button>
            ) : (
              <Button size="sm" variant="secondary" onClick={() => reactMut.mutate()} disabled={reactMut.isPending}>
                <UserCheck size={12} /> Reactivate
              </Button>
            )}
            <Button size="sm" variant="danger" onClick={() => { if (confirm(`Permanently delete ${sub.username}?`)) deleteMut.mutate() }} disabled={deleteMut.isPending}>
              <Trash2 size={12} /> Delete
            </Button>
          </div>
        </CardHeader>

        {editing ? (
          <EditForm sub={sub} onSave={f => updateMut.mutate(f)} loading={updateMut.isPending} onCancel={() => setEditing(false)} />
        ) : (
          <dl className="grid grid-cols-2 gap-x-6 gap-y-3 text-sm md:grid-cols-3">
            <InfoRow label="Email" value={sub.email} />
            <InfoRow label="Phone" value={sub.phone} />
            <InfoRow label="Package" value={`${sub.package_name} (${sub.package_id})`} />
            <InfoRow label="Price" value={formatCurrency(sub.price)} />
            <InfoRow label="Due Date" value={formatDate(sub.due_date)} />
            <InfoRow label="Days Until Due" value={sub.days_until_due !== null ? String(sub.days_until_due) : '—'} />
            <InfoRow label="Last Payment" value={formatDate(sub.last_payment)} />
          </dl>
        )}
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Payment History</CardTitle>
          <Button size="sm" variant="secondary" onClick={() => setShowPayment(v => !v)}>
            <Plus size={12} /> Record Payment
          </Button>
        </CardHeader>

        {showPayment && (
          <PaymentForm accId={accId!} onSubmit={b => payMut.mutate(b)} loading={payMut.isPending} />
        )}

        {payments && payments.length > 0 ? (
          <table className="w-full text-sm mt-3">
            <thead>
              <tr className="text-xs text-gray-500 dark:text-slate-500 uppercase">
                <th className="text-left pb-2">Date</th>
                <th className="text-left pb-2">Amount</th>
                <th className="text-left pb-2">Status</th>
                <th className="text-left pb-2">New Due Date</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-slate-800">
              {payments.map(p => (
                <tr key={p.id}>
                  <td className="py-2 text-gray-700 dark:text-slate-300">{formatDate(p.date)}</td>
                  <td className="py-2 text-gray-700 dark:text-slate-300">{formatCurrency(p.amount)}</td>
                  <td className="py-2 text-gray-700 dark:text-slate-300 capitalize">{p.status}</td>
                  <td className="py-2 text-gray-700 dark:text-slate-300">{formatDate(p.new_due_date)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p className="text-sm text-gray-400 dark:text-slate-500 mt-2">No payments recorded.</p>
        )}
      </Card>
    </div>
  )
}

function InfoRow({ label, value }: { label: string; value: string | number | null | undefined }) {
  return (
    <div>
      <dt className="text-xs text-gray-500 dark:text-slate-500">{label}</dt>
      <dd className="text-gray-800 dark:text-slate-200">{value ?? '—'}</dd>
    </div>
  )
}

interface EditFormProps {
  sub: ReturnType<typeof getSubscriber> extends Promise<infer T> ? T : never
  onSave: (f: Record<string, unknown>) => void
  loading: boolean
  onCancel: () => void
}

function EditForm({ sub, onSave, loading, onCancel }: EditFormProps) {
  const [form, setForm] = useState({
    username: sub.username,
    email: sub.email ?? '',
    phone: sub.phone ?? '',
    due_date: sub.due_date,
    package_id: sub.package_id,
    custom_price: String(sub.price),
  })
  const set = (k: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setForm(f => ({ ...f, [k]: e.target.value }))
  const selectedPkg = PACKAGES.find(p => p.id === form.package_id)

  return (
    <form
      onSubmit={e => {
        e.preventDefault()
        onSave({ ...form, package: selectedPkg?.name, custom_price: Number(form.custom_price) })
      }}
      className="grid grid-cols-2 gap-3 md:grid-cols-3"
    >
      <div><label className="text-xs text-gray-500 dark:text-slate-400 mb-1 block">Username</label><Input value={form.username} onChange={set('username')} /></div>
      <div><label className="text-xs text-gray-500 dark:text-slate-400 mb-1 block">Email</label><Input type="email" value={form.email} onChange={set('email')} /></div>
      <div><label className="text-xs text-gray-500 dark:text-slate-400 mb-1 block">Phone</label><Input value={form.phone} onChange={set('phone')} /></div>
      <div>
        <label className="text-xs text-gray-500 dark:text-slate-400 mb-1 block">Package</label>
        <select
          value={form.package_id}
          onChange={set('package_id')}
          className="w-full rounded-md border px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500
                     bg-white border-gray-300 text-gray-700 dark:bg-slate-800 dark:border-slate-700 dark:text-slate-300"
        >
          {PACKAGES.map(p => (
            <option key={p.id} value={p.id}>{p.name}{p.price !== null ? ` — $${p.price}/mo` : ''}</option>
          ))}
        </select>
      </div>
      <div><label className="text-xs text-gray-500 dark:text-slate-400 mb-1 block">Due Date</label><Input type="date" value={form.due_date} onChange={set('due_date')} /></div>
      {selectedPkg?.price === null && (
        <div><label className="text-xs text-gray-500 dark:text-slate-400 mb-1 block">Price ($)</label><Input type="number" step="0.01" value={form.custom_price} onChange={set('custom_price')} /></div>
      )}
      <div className="col-span-full flex justify-end gap-2">
        <Button type="button" variant="ghost" size="sm" onClick={onCancel}>Cancel</Button>
        <Button type="submit" size="sm" disabled={loading}>{loading ? 'Saving…' : 'Save Changes'}</Button>
      </div>
    </form>
  )
}

interface PaymentFormProps {
  accId: string
  onSubmit: (b: Parameters<typeof recordPayment>[0]) => void
  loading: boolean
}

function PaymentForm({ accId, onSubmit, loading }: PaymentFormProps) {
  const [form, setForm] = useState({ amount: '', status: 'paid', advance_days: '30', custom_due_date: '' })
  const set = (k: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setForm(f => ({ ...f, [k]: e.target.value }))

  return (
    <form
      onSubmit={e => {
        e.preventDefault()
        onSubmit({
          subscription_id: accId,
          amount: Number(form.amount),
          status: form.status,
          advance_days: form.custom_due_date ? undefined : Number(form.advance_days),
          custom_due_date: form.custom_due_date || undefined,
        })
      }}
      className="grid grid-cols-2 gap-3 mb-4 md:grid-cols-4 border-b border-gray-100 dark:border-slate-800 pb-4"
    >
      <div><label className="text-xs text-gray-500 dark:text-slate-400 mb-1 block">Amount ($) *</label><Input required type="number" step="0.01" value={form.amount} onChange={set('amount')} /></div>
      <div>
        <label className="text-xs text-gray-500 dark:text-slate-400 mb-1 block">Status</label>
        <select
          className="w-full rounded-md border px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500
                     bg-white border-gray-300 text-gray-700
                     dark:bg-slate-800 dark:border-slate-700 dark:text-slate-300"
          value={form.status} onChange={set('status')}
        >
          <option value="paid">Paid</option>
          <option value="partial">Partial</option>
          <option value="late">Late</option>
        </select>
      </div>
      <div><label className="text-xs text-gray-500 dark:text-slate-400 mb-1 block">Advance Days</label><Input type="number" value={form.advance_days} onChange={set('advance_days')} /></div>
      <div><label className="text-xs text-gray-500 dark:text-slate-400 mb-1 block">Or Custom Due Date</label><Input type="date" value={form.custom_due_date} onChange={set('custom_due_date')} /></div>
      <div className="col-span-full flex justify-end">
        <Button type="submit" size="sm" disabled={loading}>{loading ? 'Saving…' : 'Record Payment'}</Button>
      </div>
    </form>
  )
}
