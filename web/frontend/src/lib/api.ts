import axios from 'axios'
import type { ToastType } from './ToastContext'

const API_KEY = import.meta.env.VITE_API_KEY ?? ''

export const api = axios.create({
  baseURL: '/api',
  headers: API_KEY ? { 'X-API-Key': API_KEY } : {},
})

// Allows App to register the toast function after mount
type ToastFn = (msg: string, type?: ToastType) => void
let _toast: ToastFn = () => {}
export const registerToast = (fn: ToastFn) => { _toast = fn }

api.interceptors.response.use(
  res => res,
  err => {
    const detail = err.response?.data?.detail
    const msg = Array.isArray(detail)
      ? detail.map((d: { msg: string }) => d.msg).join('; ')
      : (detail ?? err.message ?? 'Unknown error')
    _toast(`${err.config?.url ?? 'API'}: ${msg}`, 'error')
    return Promise.reject(new Error(msg))
  },
)

// ── Types ──────────────────────────────────────────────────────────────────

export interface DashboardStats {
  total_subscribers: number
  active_subscribers: number
  inactive_subscribers: number
  due_today: number
  overdue: number
  revenue_this_month: number
  revenue_last_month: number
}

export interface Subscriber {
  id: string
  username: string
  email: string | null
  phone: string | null
  package_id: string
  package_name: string
  price: number
  due_date: string
  status: string
  days_until_due: number | null
  last_payment: string | null
  is_active: number
}

export interface SubscriberList {
  subscribers: Subscriber[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface Payment {
  id: number
  subscription_id: string
  amount: number
  status: string
  date: string
  new_due_date: string | null
}

export interface RiskPrediction {
  id: string
  username: string
  risk_score: number
  risk_level: string
  days_overdue: number | null
  flags: string[]
  suggested_actions: string[]
}

export interface RiskReport {
  generated_at: string
  model: string
  threshold_days: number
  total_at_risk: number
  predictions: RiskPrediction[]
}

export interface BulkUpdateResult {
  preview: boolean
  affected: number
  accounts: string[]
}

// ── Endpoints ──────────────────────────────────────────────────────────────

export const getDashboard = () =>
  api.get<DashboardStats>('/dashboard').then(r => r.data)

export const getSubscribers = (params: Record<string, unknown> = {}) =>
  api.get<SubscriberList>('/subscribers', { params }).then(r => r.data)

export const getSubscriber = (accId: string) =>
  api.get<Subscriber>(`/subscribers/${accId}`).then(r => r.data)

export const createSubscriber = (body: {
  username: string
  email?: string
  phone?: string
  package_id: string
  due_date: string
  custom_price?: number
}) => api.post('/subscribers', body).then(r => r.data)

export const updateSubscriber = (accId: string, fields: Record<string, unknown>) =>
  api.patch(`/subscribers/${accId}`, fields).then(r => r.data)

export const deactivateSubscriber = (accId: string) =>
  api.post(`/subscribers/${accId}/deactivate`).then(r => r.data)

export const reactivateSubscriber = (accId: string) =>
  api.post(`/subscribers/${accId}/reactivate`).then(r => r.data)

export const deleteSubscriber = (accId: string) =>
  api.delete(`/subscribers/${accId}`).then(r => r.data)

export const getPayments = (accId: string) =>
  api.get<Payment[]>(`/payments/${accId}`).then(r => r.data)

export const recordPayment = (body: {
  subscription_id: string
  amount: number
  status: string
  advance_days?: number
  custom_due_date?: string
}) => api.post('/payments', body).then(r => r.data)

export const getGeneralRisk = () =>
  api.get<RiskReport>('/risk/general').then(r => r.data)

export const getEnhancedRisk = () =>
  api.get<RiskReport>('/risk/enhanced').then(r => r.data)

export const sendRiskReminders = (mode: 'general' | 'enhanced') =>
  api.post<{ sent: number; total: number; errors: string[]; message: string }>(
    '/risk/send-reminders', null, { params: { mode } }
  ).then(r => r.data)

export const bulkUpdateDueDates = (body: {
  advance_days: number
  account_ids?: string[]
  status_filter?: string
  package_filter?: string
}, preview = false) =>
  api.post<BulkUpdateResult>('/subscribers/bulk/due-dates', body, { params: { preview } }).then(r => r.data)

export const exportSubscribers = () =>
  api.get<unknown[]>('/subscribers/export/json').then(r => r.data)

export const importSubscribers = (data: unknown[]) =>
  api.post<{ imported: number; skipped: number }>('/subscribers/import/json', data).then(r => r.data)

export const triggerBackup = () =>
  api.post('/notifications/backup').then(r => r.data)

export const testTelegram  = () => api.post<{ message: string }>('/notifications/test/telegram').then(r => r.data)
export const testDiscord   = () => api.post<{ message: string }>('/notifications/test/discord').then(r => r.data)
export const testPushover  = () => api.post<{ message: string }>('/notifications/test/pushover').then(r => r.data)
export const testEmail     = () => api.post<{ message: string }>('/notifications/test/email').then(r => r.data)

export const getNotificationStatus = () =>
  api.get('/notifications/status').then(r => r.data)

export interface NotificationSettings {
  telegram:  { enabled: boolean; bot_token: string; chat_id: string }
  discord:   { enabled: boolean; webhook_url: string }
  pushover:  { enabled: boolean; api_token: string; user_key: string }
  email:     { enabled: boolean; smtp_server: string; smtp_port: string; username: string; password: string; from_email: string; from_name: string }
}

export const getNotificationSettings = () =>
  api.get<NotificationSettings>('/notifications/settings').then(r => r.data)

export const updateNotificationSettings = (body: Partial<NotificationSettings>) =>
  api.patch<{ updated: string[]; message: string }>('/notifications/settings', body).then(r => r.data)
