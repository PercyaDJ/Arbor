/**
 * ARBOR - Composants UI de base
 * Badge sévérité, statut alerte, boutons, cartes, spinner
 */

import React, { useState } from 'react'

// --- Severity Badge ---
const SEVERITY_STYLES: Record<string, { bg: string; label: string }> = {
  critical: { bg: '#ef4444', label: 'Critique' },
  high:     { bg: '#f97316', label: 'Haute' },
  medium:   { bg: '#eab308', label: 'Moyenne' },
  low:      { bg: '#3b82f6', label: 'Basse' },
  info:     { bg: '#6b7280', label: 'Info' },
}

export function SeverityBadge({ severity }: { severity: string }) {
  const s = SEVERITY_STYLES[severity?.toLowerCase()] || { bg: '#6b7280', label: 'Info' }
  return (
    <span style={{
      background: s.bg,
      color: '#0a0f0d',
      padding: '2px 10px',
      borderRadius: '4px',
      fontWeight: 700,
      fontSize: '11px',
      textTransform: 'uppercase',
      letterSpacing: '0.05em',
      display: 'inline-block',
    }}>
      {s.label}
    </span>
  )
}

// --- Status Badge ---
const STATUS_STYLES: Record<string, { bg: string; label: string }> = {
  new:            { bg: 'rgba(239,68,68,0.15)', label: 'Nouvelle' },
  acknowledged:   { bg: 'rgba(249,115,22,0.15)', label: 'Prise en compte' },
  in_progress:    { bg: 'rgba(234,179,8,0.15)', label: 'En cours' },
  resolved:       { bg: 'rgba(34,197,94,0.15)', label: 'Résolue' },
  not_applicable: { bg: 'rgba(107,114,128,0.15)', label: 'Non applicable' },
}

const STATUS_TEXT: Record<string, string> = {
  new: '#ef4444', acknowledged: '#f97316', in_progress: '#eab308',
  resolved: '#22c55e', not_applicable: '#6b7280',
}

export function StatusBadge({ status }: { status: string }) {
  const s = STATUS_STYLES[status] || { bg: 'rgba(239,68,68,0.15)', label: 'Nouvelle' }
  const color = STATUS_TEXT[status] ?? '#ef4444'
  return (
    <span style={{
      background: s.bg,
      color,
      padding: '3px 10px',
      borderRadius: '20px',
      fontSize: '12px',
      fontWeight: 500,
      display: 'inline-block',
    }}>
      {s.label}
    </span>
  )
}

// --- Button ---
interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger'
  size?: 'sm' | 'md' | 'lg'
  loading?: boolean
}

export function Button({
  variant = 'primary', size = 'md', loading, children, style, disabled, ...props
}: ButtonProps) {
  const base: React.CSSProperties = {
    display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: '8px',
    border: 'none', borderRadius: '8px', fontFamily: 'inherit',
    fontWeight: 600, cursor: disabled || loading ? 'not-allowed' : 'pointer',
    opacity: disabled || loading ? 0.6 : 1,
    transition: 'all 150ms ease',
    ...(size === 'sm' && { padding: '6px 14px', fontSize: '13px' }),
    ...(size === 'md' && { padding: '10px 20px', fontSize: '14px' }),
    ...(size === 'lg' && { padding: '13px 28px', fontSize: '16px' }),
    ...(variant === 'primary' && { background: '#4ade80', color: '#0a0f0d' }),
    ...(variant === 'secondary' && { background: '#1e2b26', color: '#e8f0ec', border: '1px solid #243029' }),
    ...(variant === 'ghost' && { background: 'transparent', color: '#94a89d', border: '1px solid #243029' }),
    ...(variant === 'danger' && { background: 'rgba(239,68,68,0.1)', color: '#ef4444', border: '1px solid rgba(239,68,68,0.3)' }),
    ...style,
  }

  return (
    <button style={base} disabled={disabled || loading} {...props}>
      {loading && <Spinner size={14} />}
      {children}
    </button>
  )
}

// --- Spinner ---
export function Spinner({ size = 20 }: { size?: number }) {
  return (
    <div style={{
      width: size, height: size,
      border: `2px solid rgba(74,222,128,0.2)`,
      borderTopColor: '#4ade80',
      borderRadius: '50%',
      animation: 'arbor-spin 0.7s linear infinite',
      flexShrink: 0,
    }} />
  )
}

// --- Card ---
export function Card({
  children, style, onClick,
}: { children: React.ReactNode; style?: React.CSSProperties; onClick?: () => void }) {
  return (
    <div
      onClick={onClick}
      style={{
        background: '#131a16',
        border: '1px solid #243029',
        borderRadius: '12px',
        padding: '20px',
        cursor: onClick ? 'pointer' : 'default',
        transition: 'border-color 200ms ease, background 200ms ease',
        ...style,
      }}
      onMouseEnter={onClick ? (e) => {
        (e.currentTarget as HTMLElement).style.borderColor = '#344a3d'
        ;(e.currentTarget as HTMLElement).style.background = '#1a2420'
      } : undefined}
      onMouseLeave={onClick ? (e) => {
        (e.currentTarget as HTMLElement).style.borderColor = '#243029'
        ;(e.currentTarget as HTMLElement).style.background = '#131a16'
      } : undefined}
    >
      {children}
    </div>
  )
}

// --- Empty State ---
export function EmptyState({ icon, title, description, action }: {
  icon: string; title: string; description?: string; action?: React.ReactNode
}) {
  return (
    <div style={{ textAlign: 'center', padding: '48px 24px', color: '#5f7368' }}>
      <div style={{ fontSize: '48px', marginBottom: '16px' }}>{icon}</div>
      <div style={{ fontSize: '16px', fontWeight: 600, color: '#94a89d', marginBottom: '8px' }}>{title}</div>
      {description && <div style={{ fontSize: '14px', marginBottom: '20px' }}>{description}</div>}
      {action}
    </div>
  )
}

// --- Input ---
interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
}

export function Input({ label, error, style, type, ...props }: InputProps) {
  const [showPassword, setShowPassword] = useState(false)
  const isPassword = type === 'password'
  const currentType = isPassword ? (showPassword ? 'text' : 'password') : type

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
      {label && <label style={{ fontSize: '13px', fontWeight: 500, color: '#94a89d' }}>{label}</label>}
      <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
        <input
          type={currentType}
          style={{
            background: '#131a16',
            border: `1px solid ${error ? '#ef4444' : '#243029'}`,
            borderRadius: '8px',
            padding: '10px 14px',
            paddingRight: isPassword ? '40px' : '14px',
            color: '#e8f0ec',
            fontSize: '14px',
            fontFamily: 'inherit',
            outline: 'none',
            width: '100%',
            boxSizing: 'border-box',
            transition: 'border-color 150ms',
            ...style,
          }}
          onFocus={(e) => { if (!error) e.currentTarget.style.borderColor = '#4ade80' }}
          onBlur={(e) => { if (!error) e.currentTarget.style.borderColor = '#243029' }}
          {...props}
        />
        {isPassword && (
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            style={{
              position: 'absolute', right: '12px',
              background: 'transparent', border: 'none',
              color: '#5f7368', cursor: 'pointer',
              padding: '0', display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}
            aria-label={showPassword ? "Masquer le mot de passe" : "Afficher le mot de passe"}
          >
            {showPassword ? (
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path>
                <line x1="1" y1="1" x2="23" y2="23"></line>
              </svg>
            ) : (
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                <circle cx="12" cy="12" r="3"></circle>
              </svg>
            )}
          </button>
        )}
      </div>
      {error && <span style={{ fontSize: '12px', color: '#ef4444' }}>{error}</span>}
    </div>
  )
}

// --- Select ---
export function Select({
  label, children, ...props
}: { label?: string } & React.SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
      {label && <label style={{ fontSize: '13px', fontWeight: 500, color: '#94a89d' }}>{label}</label>}
      <select
        style={{
          background: '#131a16', border: '1px solid #243029', borderRadius: '8px',
          padding: '10px 14px', color: '#e8f0ec', fontSize: '14px',
          fontFamily: 'inherit', outline: 'none', cursor: 'pointer',
        }}
        {...props}
      >
        {children}
      </select>
    </div>
  )
}

// Injection des animations globales
if (typeof document !== 'undefined' && !document.getElementById('arbor-ui-styles')) {
  const style = document.createElement('style')
  style.id = 'arbor-ui-styles'
  style.textContent = `
    @keyframes arbor-spin { to { transform: rotate(360deg); } }
    @keyframes arbor-fade-in { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: none; } }
    .arbor-animate-in { animation: arbor-fade-in 0.3s ease both; }
  `
  document.head.appendChild(style)
}
