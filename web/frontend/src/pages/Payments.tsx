import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Search } from 'lucide-react'
import { getPayments } from '../lib/api'
import { formatCurrency, formatDate } from '../lib/utils'
import { Card } from '../components/ui/Card'
import Input from '../components/ui/Input'
import Button from '../components/ui/Button'

export default function Payments() {
  const [accId, setAccId] = useState('')
  const [query, setQuery] = useState('')

  const { data, isLoading, error } = useQuery({
    queryKey: ['payments-lookup', query],
    queryFn: () => getPayments(query),
    enabled: !!query,
  })

  return (
    <div className="space-y-5 max-w-2xl">
      <h1 className="text-xl font-bold text-slate-100">Payment Lookup</h1>

      <form
        onSubmit={e => { e.preventDefault(); setQuery(accId.trim()) }}
        className="flex gap-2"
      >
        <div className="relative flex-1">
          <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-500" />
          <Input
            className="pl-8"
            placeholder="Enter Account ID (e.g. ACC-0001)…"
            value={accId}
            onChange={e => setAccId(e.target.value)}
          />
        </div>
        <Button type="submit" disabled={!accId.trim()}>Lookup</Button>
      </form>

      {isLoading && <p className="text-slate-400">Loading payments…</p>}
      {error && <p className="text-red-400">No payment history found or invalid account ID.</p>}

      {data && (
        <Card>
          <p className="text-xs text-slate-500 mb-3 uppercase tracking-wide">
            {data.length} payment{data.length !== 1 ? 's' : ''} for <span className="text-slate-300">{query}</span>
          </p>
          {data.length === 0 ? (
            <p className="text-sm text-slate-500">No payments recorded for this account.</p>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="text-xs text-slate-500 uppercase">
                  <th className="text-left pb-2">Date</th>
                  <th className="text-left pb-2">Amount</th>
                  <th className="text-left pb-2">Status</th>
                  <th className="text-left pb-2">New Due Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {data.map(p => (
                  <tr key={p.id}>
                    <td className="py-2 text-slate-300">{formatDate(p.date)}</td>
                    <td className="py-2 text-slate-300">{formatCurrency(p.amount)}</td>
                    <td className="py-2 text-slate-300 capitalize">{p.status}</td>
                    <td className="py-2 text-slate-300">{formatDate(p.new_due_date)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Card>
      )}

      <p className="text-xs text-slate-600">
        Tip: You can also view and record payments from the Subscriber detail page.
      </p>
    </div>
  )
}
