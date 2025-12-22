import { useState } from 'react'
import type { FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { isAxiosError } from 'axios'
import { login } from './api'

type FastAPIValidationItem = {
  loc?: Array<string | number>
  msg?: string
}

const detailArrayToMessage = (detail: FastAPIValidationItem[]): string => {
  return detail
    .map((item) => {
      if (!item || typeof item !== 'object') return null
      const loc = Array.isArray(item.loc) ? item.loc.join('.') : item.loc
      const msg = item.msg ?? 'Invalid input'
      return loc ? `${loc}: ${msg}` : msg
    })
    .filter((segment): segment is string => Boolean(segment))
    .join(' | ')
}

const formatFastAPIDetail = (detail: unknown): string | undefined => {
  if (!detail) {
    return undefined
  }
  if (typeof detail === 'string') {
    return detail
  }
  if (Array.isArray(detail)) {
    return detailArrayToMessage(detail as FastAPIValidationItem[])
  }
  if (typeof detail === 'object') {
    const record = detail as Record<string, unknown>
    if (record.detail) {
      const nested = formatFastAPIDetail(record.detail)
      if (nested) {
        return nested
      }
    }
    const item = record as FastAPIValidationItem
    const loc = Array.isArray(item.loc) ? item.loc.join('.') : item.loc
    if (typeof item.msg === 'string') {
      return loc ? `${loc}: ${item.msg}` : item.msg
    }
  }
  return undefined
}

const logLoginError = (err: unknown) => {
  if (!import.meta.env.DEV) {
    return
  }
  if (isAxiosError(err)) {
    console.error('Login failed', err.response?.data ?? err.message)
  } else {
    console.error('Login failed', err)
  }
}

const toErrorMessage = (err: unknown): string => {
  if (isAxiosError(err)) {
    const data = err.response?.data as { detail?: unknown; message?: string } | undefined
    const formatted =
      formatFastAPIDetail(data?.detail) ??
      (typeof data?.message === 'string' ? data.message : undefined)
    if (formatted) {
      return formatted
    }
    if (typeof err.message === 'string' && err.message) {
      return err.message
    }
  }
  if (err instanceof Error && err.message) {
    return err.message
  }
  return 'Login failed. Please try again.'
}

export default function Login() {
  const [identifier, setIdentifier] = useState('admin@example.com')
  const [password, setPassword] = useState('adminpass')
  const [error, setError] = useState('')
  const navigate = useNavigate()

  const handleLogin = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setError('')
    const normalized = identifier.trim()
    if (!normalized) {
      setError('Email or username is required.')
      return
    }
    try {
      const data = await login(normalized, password)
      localStorage.setItem('token', data.access_token)
      navigate('/dashboard')
    } catch (err) {
      logLoginError(err)
      setError(toErrorMessage(err))
    }
  }

  return (
    <div className="flex h-screen items-center justify-center bg-slate-900">
      <form
        onSubmit={handleLogin}
        className="w-96 rounded-lg bg-slate-800 p-8 shadow-xl border border-slate-700"
      >
        <h1 className="mb-6 text-2xl font-bold text-white text-center">🤖 Finbot Pro</h1>

        {error && <div className="mb-4 text-red-400 text-sm text-center">{error}</div>}

        <div className="mb-4">
          <label className="block text-slate-400 text-sm mb-1">Email or Username</label>
          <input
            type="text"
            value={identifier}
            onChange={(e) => setIdentifier(e.target.value)}
            placeholder="you@example.com or trader01"
            className="w-full rounded bg-slate-700 p-2 text-white border border-slate-600 focus:outline-none focus:border-blue-500"
          />
        </div>

        <div className="mb-6">
          <label className="block text-slate-400 text-sm mb-1">Password</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full rounded bg-slate-700 p-2 text-white border border-slate-600 focus:outline-none focus:border-blue-500"
          />
        </div>

        <button className="w-full rounded bg-blue-600 py-2 font-bold text-white hover:bg-blue-500 transition">
          Unlock Terminal
        </button>
      </form>
    </div>
  )
}
