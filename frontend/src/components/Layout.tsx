/**
 * ARBOR - Layout principal : sidebar + header
 */

import React from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { authStore } from '@/store/auth'

const NAV_ITEMS = [
  { path: '/dashboard', icon: '⬡', label: 'Tableau de bord' },
  { path: '/projects', icon: '', label: 'Projets' },
  { path: '/settings', icon: '', label: 'Paramètres' },
]

export function Layout({ children }: { children: React.ReactNode }) {
  const location = useLocation()
  const navigate = useNavigate()
  const user = authStore.getState().user

  function handleLogout() {
    authStore.logout()
    navigate('/login')
  }

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: 'var(--bg-primary)' }}>
      {/* Sidebar */}
      <aside style={{
        width: '240px', flexShrink: 0,
        background: 'var(--bg-secondary)',
        borderRight: '1px solid var(--border)',
        display: 'flex', flexDirection: 'column',
        position: 'fixed', top: 0, left: 0, bottom: 0, zIndex: 10,
      }}>
        {/* Logo */}
        <div style={{ padding: '24px 20px', borderBottom: '1px solid var(--border)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ fontSize: '24px' }}></span>
            <div>
              <div style={{ fontWeight: 800, fontSize: '16px', color: 'var(--text-primary)', letterSpacing: '-0.02em' }}>ARBOR</div>
              <div style={{ fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>Risk Registry</div>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav style={{ flex: 1, padding: '16px 10px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
          {NAV_ITEMS.map((item) => {
            const active = location.pathname.startsWith(item.path)
            return (
              <Link
                key={item.path}
                to={item.path}
                style={{
                  display: 'flex', alignItems: 'center', gap: '10px',
                  padding: '9px 12px', borderRadius: '8px',
                  color: active ? 'var(--accent)' : 'var(--text-secondary)',
                  background: active ? 'var(--accent-subtle)' : 'transparent',
                  textDecoration: 'none', fontSize: '14px', fontWeight: active ? 600 : 400,
                  transition: 'all 150ms ease',
                  border: active ? '1px solid var(--accent-muted)' : '1px solid transparent',
                }}
              >
                <span style={{ fontSize: '16px' }}>{item.icon}</span>
                {item.label}
              </Link>
            )
          })}
        </nav>

        {/* User footer */}
        <div style={{ padding: '16px', borderTop: '1px solid var(--border)' }}>
          <div style={{
            padding: '10px 12px', borderRadius: '8px',
            background: 'var(--bg-tertiary)', marginBottom: '8px',
          }}>
            <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '2px' }}>
              {user?.display_name ?? '-'}
            </div>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {user?.email}
            </div>
            {user?.is_superuser && (
              <span style={{
                display: 'inline-block', marginTop: '4px',
                background: 'var(--accent-muted)', color: 'var(--accent)',
                fontSize: '10px', padding: '1px 6px', borderRadius: '3px', fontWeight: 600,
              }}>ADMIN</span>
            )}
          </div>
          <button
            onClick={handleLogout}
            style={{
              width: '100%', padding: '8px 12px', borderRadius: '8px',
              background: 'transparent', border: '1px solid var(--border)',
              color: 'var(--text-muted)', fontSize: '13px', cursor: 'pointer',
              transition: 'all 150ms', fontFamily: 'inherit',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = '#ef4444'
              e.currentTarget.style.color = '#ef4444'
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = 'var(--border)'
              e.currentTarget.style.color = 'var(--text-muted)'
            }}
          >
            Déconnexion
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main style={{ flex: 1, marginLeft: '240px', minHeight: '100vh' }}>
        {children}
      </main>
    </div>
  )
}

// --- Page Header ---
export function PageHeader({
  title, subtitle, action,
}: { title: string; subtitle?: string; action?: React.ReactNode }) {
  return (
    <div style={{
      padding: '28px 32px 0',
      display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between',
      gap: '16px',
    }}>
      <div>
        <h1 style={{ fontSize: '22px', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>{title}</h1>
        {subtitle && <p style={{ margin: '4px 0 0', color: 'var(--text-secondary)', fontSize: '14px' }}>{subtitle}</p>}
      </div>
      {action && <div style={{ flexShrink: 0 }}>{action}</div>}
    </div>
  )
}

// --- Stats Card ---
export function StatCard({
  label, value, color = 'var(--accent)', icon,
}: { label: string; value: number | string; color?: string; icon: string }) {
  return (
    <div style={{
      background: 'var(--bg-secondary)', border: '1px solid var(--border)',
      borderRadius: '12px', padding: '20px 24px',
      display: 'flex', alignItems: 'center', gap: '16px',
    }}>
      <div style={{
        width: '44px', height: '44px', borderRadius: '10px',
        background: `${color}18`, display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: '22px', flexShrink: 0,
      }}>
        {icon}
      </div>
      <div>
        <div style={{ fontSize: '26px', fontWeight: 700, color, lineHeight: 1.1 }}>{value}</div>
        <div style={{ fontSize: '13px', color: 'var(--text-muted)', marginTop: '2px' }}>{label}</div>
      </div>
    </div>
  )
}
