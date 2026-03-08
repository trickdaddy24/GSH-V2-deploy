import { useQuery, useMutation } from '@tanstack/react-query'
import {
  Users, UserCheck, UserX, CalendarClock, AlertTriangle,
  DollarSign, TrendingUp, Database, Send,
} from 'lucide-react'
import { getDashboard, triggerBackup, testTelegram, getNotificationStatus } from '../lib/api'
import { formatCurrency } from '../lib/utils'
import StatCard from '../components/StatCard'
import { Card, CardHeader, CardTitle } from '../components/ui/Card'
import Button from '../components/ui/Button'

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

  if (isLoading) return <p className="text-gray-400 dark:text-slate-400">Loading dashboard…</p>
  if (error || !data) return <p className="text-red-500">Failed to load dashboard.</p>

  const revenueChange = data.revenue_last_month > 0
    ? (((data.revenue_this_month - data.revenue_last_month) / data.revenue_last_month) * 100).toFixed(1)
    : null

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-bold text-gray-900 dark:text-slate-100">Dashboard</h1>

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard label="Total Subscribers" value={data.total_subscribers} icon={Users} />
        <StatCard label="Active" value={data.active_subscribers} icon={UserCheck} iconColor="text-emerald-500" />
        <StatCard label="Inactive" value={data.inactive_subscribers} icon={UserX} iconColor="text-gray-400 dark:text-slate-500" />
        <StatCard label="Due Today" value={data.due_today} icon={CalendarClock} iconColor="text-yellow-500" />
      </div>

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-3">
        <StatCard label="Overdue" value={data.overdue} icon={AlertTriangle} iconColor="text-red-500" />
        <StatCard label="Revenue This Month" value={formatCurrency(data.revenue_this_month)} icon={DollarSign} iconColor="text-brand-500" />
        <StatCard
          label="Revenue Last Month"
          value={formatCurrency(data.revenue_last_month)}
          icon={TrendingUp}
          iconColor="text-brand-500"
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
                <span className="capitalize text-gray-700 dark:text-slate-300">{svc}</span>
                <span className={cfg.enabled ? 'text-emerald-500' : 'text-gray-400 dark:text-slate-600'}>
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
          <p className="text-sm text-gray-500 dark:text-slate-400 mb-4">
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
    </div>
  )
}
