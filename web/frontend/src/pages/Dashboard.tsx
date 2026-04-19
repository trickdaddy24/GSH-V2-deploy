import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import {
  Users, UserCheck, UserX, CalendarClock, AlertTriangle,
  DollarSign, TrendingUp, Database, Send, Bell,
} from 'lucide-react'
import { getDashboard, triggerBackup, testTelegram, getNotificationStatus, bulkRecordPayments, bulkSendDueNotices, getSubscribers } from '../lib/api'
import { formatCurrency } from '../lib/utils'
import StatCard from '../components/StatCard'
import { Card, CardHeader, CardTitle } from '../components/ui/Card'
import Button from '../components/ui/Button'
import Input from '../components/ui/Input'
import { useToast } from '../lib/ToastContext'

export default function Dashboard() {
  const { data, isLoading, error } = useQuery({ queryKey: ['dashboard'], queryFn: getDashboard })
  const { data: notifStatus } = useQuery({ queryKey: ['notif-status'], queryFn: getNotificationStatus })

  const backupMut = useMutation({
    mutationFn: triggerBackup,
    onSuccess: (d) => alert(`Backup saved: ${d.filename} (${d.size_kb} KB)`),
    onError: (e: Error) => alert(`Backup failed: ${e.message}`),
  })

  const telegramMut = useMutation({
    mutationFn: testTelegram,
    onSuccess: () => alert('Telegram test message sent!'),
    onError: (e: Error) => alert(`Failed: ${e.message}`),
  })

  if (isLoading) return <p className="text-gsh-muted dark:text-[#8899aa]">Loading dashboard…</p>
  if (error || !data) return <p className="text-red-500">Failed to load dashboard.</p>

  const revenueChange = data.revenue_last_month > 0
    ? (((data.revenue_this_month - data.revenue_last_month) / data.revenue_last_month) * 100).toFixed(1)
    : null

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-bold text-gsh-text dark:text-[#e0e6f0]">Dashboard</h1>

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard label="Total Subscribers" value={data.total_subscribers} icon={Users} />
        <StatCard label="Active" value={data.active_subscribers} icon={UserCheck} iconColor="text-emerald-500" />
        <StatCard label="Inactive" value={data.inactive_subscribers} icon={UserX} iconColor="text-gsh-muted dark:text-[#8899aa]" />
        <StatCard label="Due Today" value={data.due_today} icon={CalendarClock} iconColor="text-yellow-500" />
      </div>

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-3">
        <StatCard label="Overdue" value={data.overdue} icon={AlertTriangle} iconColor="text-red-500" />
        <StatCard label="Revenue This Month" value={formatCurrency(data.revenue_this_month)} icon={DollarSign} iconColor="text-gsh-accent" />
        <StatCard
          label="Revenue Last Month"
          value={formatCurrency(data.revenue_last_month)}
          icon={TrendingUp}
          iconColor="text-gsh-accent"
          sub={revenueChange !== null ? `${revenueChange}% vs last month` : undefined}
        />
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Notifications</CardTitle>
          </CardHeader>
          <div className="space-y-3">
            {notifStatus && Object.entries(notifStatus as Record<string, { enabled: boolean }>).map(([svc, cfg]) => (
              <div key={svc} className="flex items-center justify-between text-sm">
                <span className="capitalize text-gsh-text dark:text-[#e0e6f0]">{svc}</span>
                <span className={cfg.enabled ? 'text-emerald-500' : 'text-gsh-muted dark:text-[#8899aa]'}>
                  {cfg.enabled ? 'Enabled' : 'Disabled'}
                </span>
              </div>
            ))}
            <Button
              variant="secondary"
              size="sm"
              className="mt-2 w-full justify-center"
              onClick={() => telegramMut.mutate()}
              disabled={telegramMut.isPending}
            >
              <Send size={14} />
              {telegramMut.isPending ? 'Sending…' : 'Test Telegram'}
            </Button>
          </div>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Database</CardTitle>
          </CardHeader>
          <p className="text-sm text-gsh-muted dark:text-[#8899aa] mb-4">
            Create a timestamped backup of the SQLite database.
          </p>
          <Button
            variant="secondary"
            size="sm"
            className="w-full justify-center"
            onClick={() => backupMut.mutate()}
            disabled={backupMut.isPending}
          >
            <Database size={14} />
            {backupMut.isPending ? 'Backing up…' : 'Backup Now'}
          </Button>
        </Card>
      </div>

      <BulkPaymentCard />
      <DelinquentNoticesCard />
    </div>
  )
}

function DelinquentNoticesCard() {
  const { addToast } = useToast()

  const { data: subsData } = useQuery({
    queryKey: ['delinquent-count'],
    queryFn: () => getSubscribers({ status: 'delinquent', page_size: 1 }),
  })
  const delinquentCount = subsData?.total ?? 0

  const noticeMut = useMutation({
    mutationFn: () => bulkSendDueNotices(),
    onSuccess: r => addToast(r.message, 'success'),
    onError: (e: Error) => addToast(e.message, 'error'),
  })

  return (
    <Card>
      <CardHeader>
        <CardTitle>Delinquent Notices</CardTitle>
        {delinquentCount > 0 && (
          <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300">
            {delinquentCount} delinquent
          </span>
        )}
      </CardHeader>
      <p className="text-sm text-gsh-muted dark:text-[#8899aa] mb-4">
        Send a Telegram due-notice with a payment button to all delinquent subscribers.
      </p>
      <Button
        variant="teal"
        size="sm"
        className="w-full justify-center"
        disabled={delinquentCount === 0 || noticeMut.isPending}
        onClick={() => noticeMut.mutate()}
      >
        <Bell size={14} />
        {noticeMut.isPending
          ? 'Sending…'
          : `Send Due Notices${delinquentCount > 0 ? ` (${delinquentCount})` : ''}`}
      </Button>
    </Card>
  )
}

function BulkPaymentCard() {
  const { addToast } = useToast()
  const [amount, setAmount] = useState('')
  const [status, setStatus] = useState('paid')
  const [advanceDays, setAdvanceDays] = useState('30')
  const [statusFilter, setStatusFilter] = useState('')
  const [preview, setPreview] = useState<{ affected: number } | null>(null)

  const previewMut = useMutation({
    mutationFn: () => bulkRecordPayments({ amount: Number(amount), status, advance_days: Number(advanceDays), status_filter: statusFilter || undefined }, true),
    onSuccess: r => setPreview({ affected: r.affected }),
    onError: (e: Error) => addToast(e.message, 'error'),
  })

  const applyMut = useMutation({
    mutationFn: () => bulkRecordPayments({ amount: Number(amount), status, advance_days: Number(advanceDays), status_filter: statusFilter || undefined }, false),
    onSuccess: r => { addToast(r.message, 'success'); setPreview(null) },
    onError: (e: Error) => addToast(e.message, 'error'),
  })

  return (
    <Card>
      <CardHeader><CardTitle>Bulk Payment</CardTitle></CardHeader>
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <div>
          <label className="text-xs text-gsh-muted dark:text-[#8899aa] mb-1 block">Amount ($) *</label>
          <Input required type="number" step="0.01" min="0.01" value={amount} onChange={e => { setAmount(e.target.value); setPreview(null) }} />
        </div>
        <div>
          <label className="text-xs text-gsh-muted dark:text-[#8899aa] mb-1 block">Status</label>
          <select
            value={status}
            onChange={e => { setStatus(e.target.value); setPreview(null) }}
            className="w-full rounded-md border px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-gsh-accent bg-white border-gsh-border text-gsh-text dark:bg-[#1a1f2e] dark:border-[#2e3650] dark:text-[#e0e6f0]"
          >
            <option value="paid">Paid</option>
            <option value="failed">Failed</option>
            <option value="grace_period">Grace Period</option>
          </select>
        </div>
        <div>
          <label className="text-xs text-gsh-muted dark:text-[#8899aa] mb-1 block">Advance Days</label>
          <Input type="number" min="1" value={advanceDays} onChange={e => { setAdvanceDays(e.target.value); setPreview(null) }} />
        </div>
        <div>
          <label className="text-xs text-gsh-muted dark:text-[#8899aa] mb-1 block">Filter by Status</label>
          <select
            value={statusFilter}
            onChange={e => { setStatusFilter(e.target.value); setPreview(null) }}
            className="w-full rounded-md border px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-gsh-accent bg-white border-gsh-border text-gsh-text dark:bg-[#1a1f2e] dark:border-[#2e3650] dark:text-[#e0e6f0]"
          >
            <option value="">All active subscribers</option>
            <option value="paid">Paid</option>
            <option value="pending">Pending</option>
            <option value="delinquent">Delinquent</option>
            <option value="initial">Initial</option>
          </select>
        </div>
      </div>
      <div className="mt-3 flex items-center gap-2">
        <Button
          size="sm"
          variant="secondary"
          disabled={!amount || Number(amount) <= 0 || previewMut.isPending}
          onClick={() => previewMut.mutate()}
        >
          {previewMut.isPending ? 'Checking…' : 'Preview'}
        </Button>
        {preview && (
          <>
            <span className="text-sm text-gsh-muted dark:text-[#8899aa]">
              {preview.affected} account{preview.affected !== 1 ? 's' : ''} will be updated
            </span>
            <Button
              size="sm"
              disabled={preview.affected === 0 || applyMut.isPending}
              onClick={() => applyMut.mutate()}
            >
              {applyMut.isPending ? 'Applying…' : `Apply to ${preview.affected}`}
            </Button>
          </>
        )}
      </div>
    </Card>
  )
}
