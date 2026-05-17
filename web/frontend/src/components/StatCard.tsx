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

export default function StatCard({ label, value, icon: Icon, iconColor, sub }: Props) {
  return (
    <Card className="!p-3">
      <div className="flex items-start justify-between">
        <p className="op-eyebrow" style={{ fontSize: 9 }}>{label}</p>
        <Icon size={14} className={cn('op-dim', iconColor)} />
      </div>
      <p className="op-num op-accent" style={{ fontSize: 24, marginTop: 6, fontWeight: 500 }}>
        {value}
      </p>
      {sub && <p className="op-mono op-dim" style={{ fontSize: 10, marginTop: 4 }}>{sub}</p>}
    </Card>
  )
}
