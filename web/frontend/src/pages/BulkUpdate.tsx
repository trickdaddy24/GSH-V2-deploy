import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { CalendarClock, CheckCircle } from 'lucide-react'
import { bulkUpdateDueDates } from '../lib/api'
import { formatDate } from '../lib/utils'
import { PACKAGES, STATUSES } from '../lib/constants'
import { useToast } from '../lib/ToastContext'
import { Card, CardHeader, CardTitle } from '../components/ui/Card'
import Button from '../components/ui/Button'
import Input from '../components/ui/Input'

interface PreviewItem {
  id: string
  username: string
  old_due: string
  new_due: string
}

export default function BulkUpdate() {
  const { addToast } = useToast()
  const [advanceDays, setAdvanceDays] = useState('30')
  const [statusFilter, setStatusFilter] = useState('')
  const [packageFilter, setPackageFilter] = useState('')
  const [preview, setPreview] = useState<PreviewItem[] | null>(null)
  const [confirmed, setConfirmed] = useState(false)

  const previewMut = useMutation({
    mutationFn: () => bulkUpdateDueDates(
      { advance_days: Number(advanceDays), status_filter: statusFilter || undefined, package_filter: packageFilter || undefined },
      true,
    ),
    onSuccess: r => {
      setPreview(r.accounts.map((id, i) => ({ id, username: id, old_due: '', new_due: '' })))
      // The BulkUpdateResult only has accounts[] — re-fetch without preview to get details
    },
  })

  const applyMut = useMutation({
    mutationFn: () => bulkUpdateDueDates(
      { advance_days: Number(advanceDays), status_filter: statusFilter || undefined, package_filter: packageFilter || undefined },
      false,
    ),
    onSuccess: r => {
      addToast(`Updated ${r.affected} accounts`, 'success')
      setConfirmed(true)
      setPreview(null)
    },
  })

  const reset = () => { setPreview(null); setConfirmed(false) }

  return (
    <div className="space-y-5 max-w-2xl">
      <div className="flex items-center gap-3">
        <CalendarClock size={20} className="text-gsh-accent" />
        <h1 className="text-xl font-bold text-gsh-text dark:text-[#e0e6f0]">Bulk Due Date Update</h1>
      </div>

      <Card>
        <CardHeader><CardTitle>Configure</CardTitle></CardHeader>
        <div className="grid grid-cols-2 gap-3 md:grid-cols-3">
          <div>
            <label className="text-xs text-gsh-muted dark:text-[#8899aa] mb-1 block">Advance Days *</label>
            <Input
              type="number"
              min="1"
              value={advanceDays}
              onChange={e => { setAdvanceDays(e.target.value); reset() }}
              placeholder="e.g. 30"
            />
          </div>
          <div>
            <label className="text-xs text-gsh-muted dark:text-[#8899aa] mb-1 block">Filter by Status</label>
            <select
              value={statusFilter}
              onChange={e => { setStatusFilter(e.target.value); reset() }}
              className="w-full rounded-md border px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-gsh-accent
                         bg-white border-gray-300 text-gray-700 dark:bg-[#1a1f2e] dark:border-[#2e3650] dark:text-[#e0e6f0]"
            >
              <option value="">All statuses</option>
              {STATUSES.map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
            </select>
          </div>
          <div>
            <label className="text-xs text-gsh-muted dark:text-[#8899aa] mb-1 block">Filter by Package</label>
            <select
              value={packageFilter}
              onChange={e => { setPackageFilter(e.target.value); reset() }}
              className="w-full rounded-md border px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-gsh-accent
                         bg-white border-gray-300 text-gray-700 dark:bg-[#1a1f2e] dark:border-[#2e3650] dark:text-[#e0e6f0]"
            >
              <option value="">All packages</option>
              {PACKAGES.map(p => <option key={p.id} value={p.name}>{p.name}</option>)}
            </select>
          </div>
        </div>
        <div className="mt-4 flex gap-2">
          <Button
            variant="secondary"
            disabled={!advanceDays || Number(advanceDays) < 1 || previewMut.isPending}
            onClick={() => previewMut.mutate()}
          >
            {previewMut.isPending ? 'Loading…' : 'Preview Changes'}
          </Button>
        </div>
      </Card>

      {confirmed && (
        <div className="flex items-center gap-2 text-emerald-600 dark:text-emerald-400 text-sm font-medium">
          <CheckCircle size={16} /> Update applied successfully.
        </div>
      )}

      {previewMut.data && !confirmed && (
        <Card>
          <CardHeader>
            <CardTitle>Preview — {previewMut.data.affected} account{previewMut.data.affected !== 1 ? 's' : ''} affected</CardTitle>
            <Button
              size="sm"
              onClick={() => applyMut.mutate()}
              disabled={applyMut.isPending || previewMut.data.affected === 0}
            >
              {applyMut.isPending ? 'Applying…' : `Apply to ${previewMut.data.affected} accounts`}
            </Button>
          </CardHeader>

          {previewMut.data.affected === 0 ? (
            <p className="text-sm text-gsh-muted dark:text-[#8899aa]">No accounts match the selected filters.</p>
          ) : (
            <p className="text-sm text-gsh-muted dark:text-[#8899aa]">
              All matching active subscribers will have their due date advanced by <strong>{advanceDays} days</strong>.
              {statusFilter && <> Status filter: <strong>{statusFilter}</strong>.</>}
              {packageFilter && <> Package filter: <strong>{packageFilter}</strong>.</>}
            </p>
          )}

          {previewMut.data.accounts.length > 0 && (
            <div className="mt-3 text-xs text-gsh-muted dark:text-[#8899aa] space-y-1 max-h-48 overflow-y-auto">
              {previewMut.data.accounts.map(id => (
                <div key={id} className="font-mono">{id}</div>
              ))}
            </div>
          )}
        </Card>
      )}
    </div>
  )
}
