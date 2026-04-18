import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { ShieldAlert, Shield, Send } from 'lucide-react'
import { getGeneralRisk, getEnhancedRisk, sendRiskReminders, RiskPrediction } from '../lib/api'
import { riskColor } from '../lib/utils'
import { useToast } from '../lib/ToastContext'
import { Card, CardHeader, CardTitle } from '../components/ui/Card'
import Button from '../components/ui/Button'
import Badge from '../components/ui/Badge'

type Mode = 'general' | 'enhanced'

const RISK_BADGE: Record<string, 'danger' | 'warning' | 'default' | 'muted'> = {
  critical: 'danger',
  high:     'warning',
  medium:   'default',
  low:      'muted',
}

export default function Risk() {
  const [mode, setMode] = useState<Mode>('general')
  const { addToast } = useToast()

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['risk', mode],
    queryFn: mode === 'general' ? getGeneralRisk : getEnhancedRisk,
    staleTime: 60_000,
  })

  const reminderMut = useMutation({
    mutationFn: () => sendRiskReminders(mode),
    onSuccess: r => addToast(r.message + (r.errors.length ? ` (${r.errors.length} failed)` : ''), r.errors.length ? 'info' : 'success'),
  })

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-gsh-text dark:text-[#e0e6f0]">Risk Analysis</h1>
        <div className="flex gap-2">
          <Button size="sm" variant={mode === 'general' ? 'primary' : 'secondary'} onClick={() => setMode('general')}>
            <Shield size={14} /> General (7-day)
          </Button>
          <Button size="sm" variant={mode === 'enhanced' ? 'primary' : 'secondary'} onClick={() => setMode('enhanced')}>
            <ShieldAlert size={14} /> Enhanced (4-day)
          </Button>
          {data && data.total_at_risk > 0 && (
            <Button size="sm" variant="secondary" onClick={() => reminderMut.mutate()} disabled={reminderMut.isPending}>
              <Send size={14} /> {reminderMut.isPending ? 'Sending…' : 'Send Reminders'}
            </Button>
          )}
        </div>
      </div>

      {isLoading && <p className="text-gsh-muted dark:text-[#8899aa]">Analyzing risk…</p>}
      {error && (
        <div className="text-red-500 space-y-2">
          <p>Failed to load risk report.</p>
          <Button size="sm" variant="secondary" onClick={() => refetch()}>Retry</Button>
        </div>
      )}

      {data && (
        <>
          <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
            <MetaStat label="Model" value={data.model} />
            <MetaStat label="Threshold" value={`${data.threshold_days} days`} />
            <MetaStat label="At Risk" value={String(data.total_at_risk)} />
            <MetaStat label="Generated" value={new Date(data.generated_at).toLocaleTimeString()} />
          </div>

          {data.predictions.length === 0 ? (
            <Card className="text-center py-10">
              <Shield size={32} className="mx-auto text-emerald-500 mb-3" />
              <p className="text-gsh-text dark:text-[#e0e6f0] font-medium">No at-risk subscribers detected.</p>
              <p className="text-sm text-gsh-muted dark:text-[#8899aa] mt-1">All accounts appear to be in good standing.</p>
            </Card>
          ) : (
            <div className="space-y-3">
              {data.predictions.map(p => <RiskCard key={p.id} p={p} />)}
            </div>
          )}
        </>
      )}
    </div>
  )
}

function MetaStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg bg-white dark:bg-[#242938] border border-gray-200 dark:border-[#2e3650] px-4 py-3">
      <p className="text-xs text-gsh-muted dark:text-[#8899aa] uppercase tracking-wide">{label}</p>
      <p className="text-gsh-text dark:text-[#e0e6f0] font-medium mt-0.5">{value}</p>
    </div>
  )
}

function RiskCard({ p }: { p: RiskPrediction }) {
  const level = p.risk_level.toLowerCase() as keyof typeof RISK_BADGE
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <span className="font-semibold text-gsh-text dark:text-[#e0e6f0]">{p.username}</span>
          <span className="text-xs text-gsh-muted dark:text-[#8899aa]">{p.id}</span>
          <Badge variant={RISK_BADGE[level] ?? 'default'}>{p.risk_level}</Badge>
        </div>
        <span className={`text-lg font-bold ${riskColor(p.risk_level)}`}>
          Score {p.risk_score}
        </span>
      </CardHeader>

      <div className="grid grid-cols-1 gap-3 md:grid-cols-2 text-sm">
        {p.flags.length > 0 && (
          <div>
            <p className="text-xs text-gsh-muted dark:text-[#8899aa] uppercase mb-1">Risk Flags</p>
            <ul className="space-y-0.5">
              {p.flags.map((f, i) => (
                <li key={i} className="text-gsh-text dark:text-[#e0e6f0] flex gap-1.5">
                  <span className="text-red-500">!</span> {f}
                </li>
              ))}
            </ul>
          </div>
        )}
        {p.suggested_actions.length > 0 && (
          <div>
            <p className="text-xs text-gsh-muted dark:text-[#8899aa] uppercase mb-1">Suggested Actions</p>
            <ul className="space-y-0.5">
              {p.suggested_actions.map((a, i) => (
                <li key={i} className="text-gsh-text dark:text-[#e0e6f0] flex gap-1.5">
                  <span className="text-gsh-accent">→</span> {a}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </Card>
  )
}
