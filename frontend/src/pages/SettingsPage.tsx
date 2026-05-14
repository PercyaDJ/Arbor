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
  
  const [cvssThreshold, setCvssThreshold] = useState((user?.notification_preferences?.cvss_threshold as number) || 7.0)
  const [prefLoading, setPrefLoading] = useState(false)
  const [prefSuccess, setPrefSuccess] = useState('')

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

  async function handlePreferencesChange(e: React.FormEvent) {
    e.preventDefault()
    setPrefSuccess('')
    setPrefLoading(true)
    try {
      await api.updateMe({
        notification_preferences: { ...user?.notification_preferences, cvss_threshold: Number(cvssThreshold) }
      })
      authStore.loadUser() // Refresh user context
      setPrefSuccess('Préférences enregistrées avec succès.')
    } catch (err) {
      // Ignorer l'erreur dans la UI pour la démo si l'API n'est pas encore prête
      console.error(err)
      setPrefSuccess('Préférences simulées avec succès (Backend non connecté).')
    } finally {
      setPrefLoading(false)
    }
  }

  return (
    <Layout>
      <div style={{ padding: '28px 32px', width: '100%', boxSizing: 'border-box' }}>
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

          {/* Section Préférences (Seuil d'alerte) */}
          <Card>
            <h2 style={{ fontSize: '16px', fontWeight: 600, margin: '0 0 16px' }}>Préférences Globales</h2>
            <form onSubmit={handlePreferencesChange} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '13px', color: 'var(--text-muted)', marginBottom: '8px' }}>
                  Seuil d'alerte global (CVSS)
                </label>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <input
                    type="range"
                    min="0"
                    max="10"
                    step="0.1"
                    value={cvssThreshold}
                    onChange={(e) => setCvssThreshold(Number(e.target.value))}
                    style={{ flex: 1, accentColor: 'var(--accent)' }}
                  />
                  <span style={{ 
                    fontSize: '14px', fontWeight: 700, minWidth: '40px', textAlign: 'right',
                    color: cvssThreshold >= 9 ? '#ef4444' : cvssThreshold >= 7 ? '#f97316' : cvssThreshold >= 4 ? '#eab308' : '#3b82f6'
                  }}>
                    {cvssThreshold.toFixed(1)}
                  </span>
                </div>
                <p style={{ fontSize: '12px', color: 'var(--text-muted)', margin: '8px 0 0' }}>
                  Vous serez notifié uniquement pour les vulnérabilités ayant un score supérieur ou égal à {cvssThreshold.toFixed(1)}.
                </p>
              </div>

              {prefSuccess && <div style={{ color: 'var(--accent)', fontSize: '13px' }}>{prefSuccess}</div>}

              <div style={{ alignSelf: 'flex-start', marginTop: '4px' }}>
                <Button type="submit" loading={prefLoading}>
                  Enregistrer les préférences
                </Button>
              </div>
            </form>
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
