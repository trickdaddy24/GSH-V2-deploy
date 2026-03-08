import { useEffect, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Send, MessageSquare, Bell, Mail, Eye, EyeOff, FlaskConical } from 'lucide-react'
import {
  getNotificationSettings, updateNotificationSettings, NotificationSettings,
  testTelegram, testDiscord, testPushover, testEmail,
} from '../lib/api'
import { useToast } from '../lib/ToastContext'
import { Card, CardHeader, CardTitle } from '../components/ui/Card'
import Button from '../components/ui/Button'
import Input from '../components/ui/Input'

function useTest(fn: () => Promise<{ message: string }>, label: string) {
  const { addToast } = useToast()
  return useMutation({
    mutationFn: fn,
    onSuccess: r => addToast(r.message, 'success'),
  })
}

export default function Settings() {
  const qc = useQueryClient()
  const { addToast } = useToast()

  const { data, isLoading } = useQuery({
    queryKey: ['notification-settings'],
    queryFn: getNotificationSettings,
  })

  const saveMut = useMutation({
    mutationFn: updateNotificationSettings,
    onSuccess: r => {
      addToast(r.message, 'success')
      qc.invalidateQueries({ queryKey: ['notification-settings'] })
      qc.invalidateQueries({ queryKey: ['notif-status'] })
    },
  })

  const tgTest  = useTest(testTelegram, 'Telegram')
  const dcTest  = useTest(testDiscord,  'Discord')
  const poTest  = useTest(testPushover, 'Pushover')
  const emTest  = useTest(testEmail,    'Email')

  if (isLoading) return <p className="text-gray-400 dark:text-slate-400">Loading settings…</p>
  if (!data) return <p className="text-red-500">Failed to load settings.</p>

  return (
    <div className="space-y-6 max-w-2xl">
      <h1 className="text-xl font-bold text-gray-900 dark:text-slate-100">Notification Settings</h1>
      <p className="text-sm text-gray-500 dark:text-slate-400">
        Changes save to <code className="text-xs bg-gray-100 dark:bg-slate-800 px-1 py-0.5 rounded">.env</code> and
        take effect immediately without restart.
      </p>

      <TelegramCard  initial={data.telegram}  onSave={v => saveMut.mutate({ telegram: v })}  loading={saveMut.isPending}  onTest={() => tgTest.mutate()}  testing={tgTest.isPending} />
      <DiscordCard   initial={data.discord}   onSave={v => saveMut.mutate({ discord: v })}   loading={saveMut.isPending}  onTest={() => dcTest.mutate()}  testing={dcTest.isPending} />
      <PushoverCard  initial={data.pushover}  onSave={v => saveMut.mutate({ pushover: v })}  loading={saveMut.isPending}  onTest={() => poTest.mutate()}  testing={poTest.isPending} />
      <EmailCard     initial={data.email}     onSave={v => saveMut.mutate({ email: v })}     loading={saveMut.isPending}  onTest={() => emTest.mutate()}  testing={emTest.isPending} />
    </div>
  )
}

// ── Shared helpers ────────────────────────────────────────────────────────────

function Toggle({ checked, onChange }: { checked: boolean; onChange: (v: boolean) => void }) {
  return (
    <button
      type="button"
      onClick={() => onChange(!checked)}
      className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors focus:outline-none ${
        checked ? 'bg-brand-600' : 'bg-gray-300 dark:bg-slate-700'
      }`}
    >
      <span className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white shadow transition-transform ${
        checked ? 'translate-x-4.5' : 'translate-x-1'
      }`} />
    </button>
  )
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="text-xs text-gray-500 dark:text-slate-400 mb-1 block">{label}</label>
      {children}
    </div>
  )
}

function SecretInput({ value, onChange, placeholder }: { value: string; onChange: (v: string) => void; placeholder?: string }) {
  const [show, setShow] = useState(false)
  return (
    <div className="relative">
      <Input
        type={show ? 'text' : 'password'}
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder={placeholder}
        className="pr-9"
      />
      <button
        type="button"
        onClick={() => setShow(v => !v)}
        className="absolute right-2.5 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:text-slate-500 dark:hover:text-slate-300"
      >
        {show ? <EyeOff size={14} /> : <Eye size={14} />}
      </button>
    </div>
  )
}

// ── Telegram ──────────────────────────────────────────────────────────────────

function TelegramCard({ initial, onSave, loading, onTest, testing }: {
  initial: NotificationSettings['telegram']
  onSave: (v: NotificationSettings['telegram']) => void
  loading: boolean; onTest: () => void; testing: boolean
}) {
  const [form, setForm] = useState(initial)
  useEffect(() => setForm(initial), [initial])
  const set = (k: keyof typeof form) => (v: string | boolean) => setForm(f => ({ ...f, [k]: v }))

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <Send size={16} className="text-blue-500" />
          <CardTitle>Telegram</CardTitle>
        </div>
        <Toggle checked={form.enabled} onChange={set('enabled')} />
      </CardHeader>
      <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
        <Field label="Bot Token">
          <SecretInput value={form.bot_token} onChange={v => set('bot_token')(v)} placeholder="123456:ABC-DEF..." />
        </Field>
        <Field label="Chat ID">
          <Input value={form.chat_id} onChange={e => set('chat_id')(e.target.value)} placeholder="-100123456789" />
        </Field>
      </div>
      <div className="flex justify-end gap-2 mt-3">
        <Button size="sm" variant="secondary" onClick={onTest} disabled={testing || !form.enabled}>
          <FlaskConical size={13} /> {testing ? 'Sending…' : 'Test'}
        </Button>
        <Button size="sm" onClick={() => onSave(form)} disabled={loading}>
          {loading ? 'Saving…' : 'Save Telegram'}
        </Button>
      </div>
    </Card>
  )
}

// ── Discord ───────────────────────────────────────────────────────────────────

function DiscordCard({ initial, onSave, loading, onTest, testing }: {
  initial: NotificationSettings['discord']
  onSave: (v: NotificationSettings['discord']) => void
  loading: boolean; onTest: () => void; testing: boolean
}) {
  const [form, setForm] = useState(initial)
  useEffect(() => setForm(initial), [initial])
  const set = (k: keyof typeof form) => (v: string | boolean) => setForm(f => ({ ...f, [k]: v }))

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <MessageSquare size={16} className="text-indigo-500" />
          <CardTitle>Discord</CardTitle>
        </div>
        <Toggle checked={form.enabled} onChange={set('enabled')} />
      </CardHeader>
      <Field label="Webhook URL">
        <SecretInput value={form.webhook_url} onChange={v => set('webhook_url')(v)} placeholder="https://discord.com/api/webhooks/..." />
      </Field>
      <div className="flex justify-end gap-2 mt-3">
        <Button size="sm" variant="secondary" onClick={onTest} disabled={testing || !form.enabled}>
          <FlaskConical size={13} /> {testing ? 'Sending…' : 'Test'}
        </Button>
        <Button size="sm" onClick={() => onSave(form)} disabled={loading}>
          {loading ? 'Saving…' : 'Save Discord'}
        </Button>
      </div>
    </Card>
  )
}

// ── Pushover ──────────────────────────────────────────────────────────────────

function PushoverCard({ initial, onSave, loading, onTest, testing }: {
  initial: NotificationSettings['pushover']
  onSave: (v: NotificationSettings['pushover']) => void
  loading: boolean; onTest: () => void; testing: boolean
}) {
  const [form, setForm] = useState(initial)
  useEffect(() => setForm(initial), [initial])
  const set = (k: keyof typeof form) => (v: string | boolean) => setForm(f => ({ ...f, [k]: v }))

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <Bell size={16} className="text-orange-500" />
          <CardTitle>Pushover</CardTitle>
        </div>
        <Toggle checked={form.enabled} onChange={set('enabled')} />
      </CardHeader>
      <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
        <Field label="API Token">
          <SecretInput value={form.api_token} onChange={v => set('api_token')(v)} placeholder="azGDORePK8gMaC..." />
        </Field>
        <Field label="User Key">
          <SecretInput value={form.user_key} onChange={v => set('user_key')(v)} placeholder="uQiRzpo4DXghDmr..." />
        </Field>
      </div>
      <div className="flex justify-end gap-2 mt-3">
        <Button size="sm" variant="secondary" onClick={onTest} disabled={testing || !form.enabled}>
          <FlaskConical size={13} /> {testing ? 'Sending…' : 'Test'}
        </Button>
        <Button size="sm" onClick={() => onSave(form)} disabled={loading}>
          {loading ? 'Saving…' : 'Save Pushover'}
        </Button>
      </div>
    </Card>
  )
}

// ── Email ─────────────────────────────────────────────────────────────────────

function EmailCard({ initial, onSave, loading, onTest, testing }: {
  initial: NotificationSettings['email']
  onSave: (v: NotificationSettings['email']) => void
  loading: boolean; onTest: () => void; testing: boolean
}) {
  const [form, setForm] = useState(initial)
  useEffect(() => setForm(initial), [initial])
  const set = (k: keyof typeof form) => (v: string | boolean) => setForm(f => ({ ...f, [k]: v }))

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <Mail size={16} className="text-emerald-500" />
          <CardTitle>Email (SMTP)</CardTitle>
        </div>
        <Toggle checked={form.enabled} onChange={set('enabled')} />
      </CardHeader>
      <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
        <Field label="SMTP Server">
          <Input value={form.smtp_server} onChange={e => set('smtp_server')(e.target.value)} placeholder="smtp.gmail.com" />
        </Field>
        <Field label="SMTP Port">
          <Input value={form.smtp_port} onChange={e => set('smtp_port')(e.target.value)} placeholder="587" />
        </Field>
        <Field label="Username">
          <Input value={form.username} onChange={e => set('username')(e.target.value)} placeholder="you@gmail.com" />
        </Field>
        <Field label="Password">
          <SecretInput value={form.password} onChange={v => set('password')(v)} placeholder="Leave blank to keep current" />
        </Field>
        <Field label="From Email">
          <Input value={form.from_email} onChange={e => set('from_email')(e.target.value)} placeholder="billing@guardianstreams.com" />
        </Field>
        <Field label="From Name">
          <Input value={form.from_name} onChange={e => set('from_name')(e.target.value)} placeholder="GuardianStreams Billing" />
        </Field>
      </div>
      <div className="flex justify-end gap-2 mt-3">
        <Button size="sm" variant="secondary" onClick={onTest} disabled={testing || !form.enabled}>
          <FlaskConical size={13} /> {testing ? 'Sending…' : 'Test'}
        </Button>
        <Button size="sm" onClick={() => onSave(form)} disabled={loading}>
          {loading ? 'Saving…' : 'Save Email'}
        </Button>
      </div>
    </Card>
  )
}
