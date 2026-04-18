import { useState, FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { Shield } from 'lucide-react'
import { login } from '../lib/auth'

export default function Login() {
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(username, password)
      navigate('/dashboard', { replace: true })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gsh-bg dark:bg-[#1a1f2e] px-4">
      <div className="w-full max-w-sm">
        <div className="flex flex-col items-center mb-8 gap-3">
          <div className="flex items-center justify-center w-12 h-12 rounded-xl bg-gsh-accent text-white">
            <Shield size={24} />
          </div>
          <div className="text-center">
            <h1 className="text-xl font-bold text-gsh-text dark:text-[#e0e6f0]">GuardianStreams</h1>
            <p className="text-sm text-gsh-muted dark:text-[#8899aa]">Sign in to your account</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="bg-white dark:bg-[#242938] rounded-xl border border-gsh-border dark:border-[#2e3650] p-6 space-y-4 shadow-sm">
          {error && (
            <div className="rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 px-3 py-2 text-sm text-red-700 dark:text-red-400">
              {error}
            </div>
          )}

          <div className="space-y-1">
            <label htmlFor="username" className="block text-sm font-medium text-gsh-text dark:text-[#e0e6f0]">
              Username
            </label>
            <input
              id="username"
              type="text"
              autoComplete="username"
              required
              value={username}
              onChange={e => setUsername(e.target.value)}
              className="w-full rounded-lg border border-gsh-border dark:border-[#2e3650] bg-white dark:bg-[#1a1f2e] px-3 py-2 text-sm text-gsh-text dark:text-[#e0e6f0] placeholder-gsh-muted dark:placeholder-[#8899aa] focus:outline-none focus:ring-2 focus:ring-gsh-accent focus:border-transparent"
              placeholder="admin"
            />
          </div>

          <div className="space-y-1">
            <label htmlFor="password" className="block text-sm font-medium text-gsh-text dark:text-[#e0e6f0]">
              Password
            </label>
            <input
              id="password"
              type="password"
              autoComplete="current-password"
              required
              value={password}
              onChange={e => setPassword(e.target.value)}
              className="w-full rounded-lg border border-gsh-border dark:border-[#2e3650] bg-white dark:bg-[#1a1f2e] px-3 py-2 text-sm text-gsh-text dark:text-[#e0e6f0] placeholder-gsh-muted dark:placeholder-[#8899aa] focus:outline-none focus:ring-2 focus:ring-gsh-accent focus:border-transparent"
              placeholder="••••••••"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-lg bg-gsh-accent hover:bg-gsh-accent-hover disabled:opacity-60 disabled:cursor-not-allowed px-4 py-2 text-sm font-semibold text-white transition-colors focus:outline-none focus:ring-2 focus:ring-gsh-accent focus:ring-offset-2"
          >
            {loading ? 'Signing in…' : 'Sign in'}
          </button>
        </form>
      </div>
    </div>
  )
}
