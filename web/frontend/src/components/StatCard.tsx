import { LucideIcon } from 'lucide-react'
import { Card } from './ui/Card'
import { cn } from '../lib/utils'

interface Props {
  label: string
  value: string | number
  icon: LucideIcon
  iconColor?: string
  sub?: string
}

export default function StatCard({ label, value, icon: Icon, iconColor = 'text-brand-500', sub }: Props) {
  return (
    <Card className="flex items-start gap-4">
      <div className={cn('mt-0.5 rounded-lg bg-slate-800 p-2', iconColor)}>
        <Icon size={20} />
      </div>
      <div>
        <p className="text-xs text-slate-500 uppercase tracking-wide">{label}</p>
        <p className="text-2xl font-bold text-slate-100">{value}</p>
        {sub && <p className="text-xs text-slate-500 mt-0.5">{sub}</p>}
      </div>
    </Card>
  )
}
