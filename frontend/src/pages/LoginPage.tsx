/**
 * ARBOR - Page de connexion
 */

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { authStore } from '@/store/auth'
import { Button, Input } from '@/components/ui'
import type { ApiError } from '@/api/client'

export function LoginPage() {
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await authStore.login(email, password)
      navigate('/dashboard')
    } catch (err) {
      const apiErr = err as ApiError
      setError(apiErr.detail ?? 'Erreur de connexion')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{
      minHeight: '100vh', background: 'var(--bg-primary)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      padding: '24px',
    }}>
      {/* Background grid pattern */}
      <div style={{
        position: 'fixed', inset: 0, zIndex: 0,
        backgroundImage: 'radial-gradient(circle at 25% 25%, rgba(74,222,128,0.03) 0%, transparent 50%), radial-gradient(circle at 75% 75%, rgba(74,222,128,0.02) 0%, transparent 50%)',
        pointerEvents: 'none',
      }} />

      <div className="arbor-animate-in" style={{
        width: '100%', maxWidth: '420px', position: 'relative', zIndex: 1,
      }}>
        {/* Logo */}
        <div style={{ textAlign: 'center', marginBottom: '40px' }}>
          <div style={{ fontSize: '48px', marginBottom: '12px' }}></div>
          <h1 style={{
            fontSize: '28px', fontWeight: 800, color: 'var(--text-primary)',
            margin: '0 0 4px', letterSpacing: '-0.03em',
          }}>ARBOR</h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '13px', margin: 0 }}>
            Automated Risk & Bill Of Materials Registry
          </p>
        </div>

        {/* Card */}
        <div style={{
          background: 'var(--bg-secondary)',
          border: '1px solid var(--border)',
          borderRadius: '16px',
          padding: '32px',
          boxShadow: 'var(--shadow-lg)',
        }}>
          <h2 style={{ fontSize: '18px', fontWeight: 700, margin: '0 0 24px', color: 'var(--text-primary)' }}>
            Connexion
          </h2>

          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <Input
              label="Adresse email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="admin@arbor.local"
              required
              autoComplete="email"
              id="login-email"
            />
            <Input
              label="Mot de passe"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
              autoComplete="current-password"
              id="login-password"
            />

            {error && (
              <div style={{
                background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)',
                borderRadius: '8px', padding: '10px 14px',
                color: '#ef4444', fontSize: '13px',
              }}>
                {error}
              </div>
            )}

            <Button
              type="submit"
              loading={loading}
              style={{ marginTop: '8px', width: '100%' }}
              id="login-submit"
            >
              Se connecter
            </Button>
          </form>
        </div>

        <p style={{ textAlign: 'center', marginTop: '20px', color: 'var(--text-muted)', fontSize: '12px' }}>
          Accès sur invitation uniquement
        </p>
      </div>
    </div>
  )
}
