import { useState } from 'react'
import type { FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { login } from './api'

export default function Login() {
  const [email, setEmail] = useState('admin@finbot.com')
  const [password, setPassword] = useState('admin123')
  const [error, setError] = useState('')
  const navigate = useNavigate()

  const handleLogin = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    try {
      const data = await login(email, password)
      localStorage.setItem('token', data.access_token)
      navigate('/dashboard')
    } catch (err) {
      console.error(err)
      setError('Invalid Credentials or Backend Offline')
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
          <label className="block text-slate-400 text-sm mb-1">Email</label>
          <input
            type="text"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
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
