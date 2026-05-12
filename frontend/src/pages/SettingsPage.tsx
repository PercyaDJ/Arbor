import React, { useState } from 'react'
import { Layout, PageHeader } from '@/components/Layout'
import { Button, Input, Card } from '@/components/ui'
import { authStore } from '@/store/auth'
import { api } from '@/api/client'
import type { ApiError } from '@/api/client'

export function SettingsPage() {
  const user = authStore.getState().user
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  async function handlePasswordChange(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setSuccess('')

    if (newPassword.length < 8) {
      setError('Le nouveau mot de passe doit faire au moins 8 caractères.')
      return
    }

    setLoading(true)
    try {
      await api.changePassword(currentPassword, newPassword)
      setSuccess('Mot de passe modifié avec succès.')
      setCurrentPassword('')
      setNewPassword('')
    } catch (err) {
      const apiErr = err as ApiError
      setError(apiErr.detail ?? (err instanceof Error ? err.message : String(err)))
    } finally {
      setLoading(false)
    }
  }

  return (
    <Layout>
      <div style={{ padding: '28px 32px', maxWidth: '800px', margin: '0 auto' }}>
        <PageHeader title="Paramètres du compte" />

        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', marginTop: '24px' }}>
          {/* Section Profil */}
          <Card>
            <h2 style={{ fontSize: '16px', fontWeight: 600, margin: '0 0 16px' }}>Profil</h2>
            <div style={{ display: 'grid', gap: '16px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '13px', color: 'var(--text-muted)', marginBottom: '4px' }}>
                  Adresse Email
                </label>
                <div style={{ padding: '10px 14px', background: 'var(--bg-tertiary)', borderRadius: '8px', border: '1px solid var(--border)', color: 'var(--text-secondary)' }}>
                  {user?.email}
                </div>
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '13px', color: 'var(--text-muted)', marginBottom: '4px' }}>
                  Rôle Global
                </label>
                <div style={{ display: 'inline-block', padding: '4px 10px', background: user?.is_superuser ? 'rgba(74,222,128,0.1)' : 'var(--bg-tertiary)', color: user?.is_superuser ? 'var(--accent)' : 'var(--text-secondary)', borderRadius: '20px', fontSize: '13px', fontWeight: 500, border: user?.is_superuser ? '1px solid var(--accent-muted)' : '1px solid var(--border)' }}>
                  {user?.is_superuser ? 'Super Administrateur' : 'Utilisateur'}
                </div>
              </div>
            </div>
          </Card>

          {/* Section Sécurité */}
          <Card>
            <h2 style={{ fontSize: '16px', fontWeight: 600, margin: '0 0 16px' }}>Sécurité</h2>
            <form onSubmit={handlePasswordChange} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <Input
                label="Mot de passe actuel"
                type="password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                required
              />
              <Input
                label="Nouveau mot de passe"
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                required
              />

              {error && <div style={{ color: '#ef4444', fontSize: '13px' }}>{error}</div>}
              {success && <div style={{ color: 'var(--accent)', fontSize: '13px' }}>{success}</div>}

              <div style={{ alignSelf: 'flex-start', marginTop: '8px' }}>
                <Button type="submit" loading={loading} disabled={!currentPassword || !newPassword}>
                  Mettre à jour le mot de passe
                </Button>
              </div>
            </form>
          </Card>
        </div>
      </div>
    </Layout>
  )
}
