export const PACKAGES = [
  { id: '0', name: 'OnDemand',    price: 10 },
  { id: '1', name: 'Grandfather', price: 25 },
  { id: '2', name: 'Silver',      price: 30 },
  { id: '3', name: 'Gold',        price: 40 },
  { id: '4', name: 'Platinum',    price: 50 },
  { id: '5', name: 'Custom',      price: null },
] as const

export const STATUSES = [
  { value: 'active',     label: 'Active' },
  { value: 'paid',       label: 'Paid' },
  { value: 'initial',    label: 'Initial' },
  { value: 'pending',    label: 'Pending' },
  { value: 'delinquent', label: 'Delinquent' },
]
