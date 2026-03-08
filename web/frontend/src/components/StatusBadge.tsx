import Badge from './ui/Badge'

interface Props { status: string; isActive?: number }

export default function StatusBadge({ status, isActive = 1 }: Props) {
  if (!isActive) return <Badge variant="muted">Inactive</Badge>

  switch (status.toLowerCase()) {
    case 'current':    return <Badge variant="success">{status}</Badge>
    case 'due today':  return <Badge variant="warning">{status}</Badge>
    case 'overdue':    return <Badge variant="danger">{status}</Badge>
    default:           return <Badge>{status}</Badge>
  }
}
