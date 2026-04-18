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

export default function StatCard({ label, value, icon: Icon, iconColor = 'text-gsh-accent', sub }: Props) {
  return (
    <Card className="flex items-start gap-4">
      <div className={cn('mt-0.5 rounded-lg bg-[#F3F0FF] dark:bg-[rgba(138,77,255,0.12)] p-2', iconColor)}>
        <Icon size={20} />
      </div>
      <div>
        <p className="text-xs text-gsh-muted dark:text-[#8899aa] uppercase tracking-wide">{label}</p>
        <p className="text-2xl font-bold text-gsh-accent">{value}</p>
        {sub && <p className="text-xs text-gsh-muted dark:text-[#8899aa] mt-0.5">{sub}</p>}
      </div>
    </Card>
  )
}
