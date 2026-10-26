
import { useState, type FormEvent } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'

import { login as loginApi } from '../api/auth'
import { useAuth } from '../context/AuthContext'


export default function Login() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    if (loading) return

    setLoading(true)
    setError('')

    try {
      const response = await loginApi({
        username,
        password,
      })

      login(response.access_token)

      const from = (
        location.state as {
          from?: {
            pathname?: string
          }
        } | null
      )?.from?.pathname

      navigate(
        from && from.startsWith('/') && !from.startsWith('//')
          ? from
          : '/equipment',
        { replace: true },
      )
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : '登录失败',
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <main
      style={{
        maxWidth: 420,
        margin: '80px auto',
        padding: 24,
      }}
    >
      <h1>ManuAgent 登录</h1>

      <form onSubmit={handleSubmit}>
        <div>
          <label htmlFor="username">用户名</label>
          <input
            id="username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoComplete="username"
            required
          />
        </div>

        <div style={{ marginTop: 16 }}>
          <label htmlFor="password">密码</label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
            required
          />
        </div>

        {error && (
          <p role="alert" style={{ color: 'red' }}>
            {error}
          </p>
        )}

        <button
          type="submit"
          disabled={loading}
          style={{ marginTop: 20 }}
        >
          {loading ? '登录中...' : '登录'}
        </button>
      </form>
    </main>
  )
}
