
import { useState, type FormEvent } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { ArrowRightOutlined, EyeInvisibleOutlined, EyeOutlined, LockOutlined, SafetyCertificateOutlined, SettingOutlined, UserOutlined } from '@ant-design/icons'
import './Login.css'

import { login as loginApi } from '../api/auth'
import { useAuth } from '../context/AuthContext'


export default function Login() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [showPassword, setShowPassword] = useState(false)

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
    <main className="login-page">
      <header className="login-header">
        <div className="login-brand"><SettingOutlined aria-hidden="true" /><div>ManuAgent <span>AI-MES</span><small>智能制造 · 协同未来</small></div></div>
        <span className="login-status"><i /> 智能制造协同平台</span>
      </header>
      <div className="login-content">
        <section className="login-intro" aria-label="智能制造平台">
          <span className="login-eyebrow">INTELLIGENT MANUFACTURING</span>
          <h1>让制造更智能<span>让协同更高效</span></h1>
          <p>连接设备、数据与决策，开启智能制造新体验。</p>
          <div className="login-capabilities"><span>设备互联</span><span>生产协同</span><span>智能决策</span></div>
        </section>
        <section className="login-panel" aria-labelledby="login-title">
          <div className="login-panel-heading">
            <div className="login-emblem"><SettingOutlined aria-hidden="true" /></div>
            <span className="login-eyebrow">WELCOME TO MANUAGENT</span>
            <h2 id="login-title">欢迎登录智能制造平台</h2>
            <p>登录您的账号，进入智能生产工作台</p>
          </div>
          <form onSubmit={handleSubmit}>
          <label className="login-label" htmlFor="username">账号</label>
          <div className="login-input-wrap">
          <UserOutlined aria-hidden="true" />
          <input
            id="username"
            name="username"
            placeholder="请输入用户名"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoComplete="username"
            required
          />
        </div>

          <label className="login-label" htmlFor="password">密码</label>
          <div className="login-input-wrap">
          <LockOutlined aria-hidden="true" />
          <input
            id="password"
            name="password"
            type={showPassword ? 'text' : 'password'}
            placeholder="请输入登录密码"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
            required
          />
          <button className="login-password-toggle" type="button" aria-label={showPassword ? '隐藏密码' : '显示密码'} aria-pressed={showPassword} onClick={() => setShowPassword(!showPassword)}>
            {showPassword ? <EyeInvisibleOutlined /> : <EyeOutlined />}
          </button>
        </div>

        {error && (
          <p role="alert" className="login-error">
            {error}
          </p>
        )}

        <button
          type="submit"
          disabled={loading}
          className="login-submit"
        >
          <span>{loading ? '登录中...' : '登 录'}</span><ArrowRightOutlined aria-hidden="true" />
        </button>
        <p className="login-security"><SafetyCertificateOutlined aria-hidden="true" /> 企业级安全认证 · 守护生产数据</p>
      </form>
      <div className="login-panel-footer">MANUAGENT <span>工业智能 · 高效协同</span></div>
      </section>
      </div>
      <footer className="login-footer">ManuAgent 智能制造协同平台 <span>以数据驱动制造，以智能连接未来</span></footer>
    </main>
  )
}
