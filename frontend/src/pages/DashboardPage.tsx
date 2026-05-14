/**
 * ARBOR - Dashboard principal
 */

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { api } from '@/api/client'
import { Layout, PageHeader, StatCard } from '@/components/Layout'
import { Spinner, EmptyState, Button } from '@/components/ui'
import type { Project } from '@/api/client'

export function DashboardPage() {
  const navigate = useNavigate()

  const { data: projects = [], isLoading: loadingProjects } = useQuery({
    queryKey: ['projects'],
    queryFn: () => api.getProjects(),
  })

  const totalAlerts = projects.reduce((sum, p) => sum + p.alert_count, 0)
  const criticalAlerts = projects.reduce((sum, p) => sum + p.critical_alert_count, 0)
  const activeProjectCount = projects.filter((p) => !p.archived_at).length
  
  const [showSourcesModal, setShowSourcesModal] = useState(false)

  return (
    <Layout>
      <div style={{ padding: '28px 32px', width: '100%', boxSizing: 'border-box' }}>
        <PageHeader
          title="Tableau de bord"
          subtitle="Vue d'ensemble de votre posture de sécurité"
        />

        {/* Stats */}
        <div style={{
          display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '16px', margin: '28px 0',
        }}>
          <StatCard icon="" label="Projets actifs" value={activeProjectCount} color="var(--accent)" />
          <StatCard icon="" label="Alertes actives" value={totalAlerts} color="#f97316" />
          <StatCard icon="" label="Alertes critiques" value={criticalAlerts} color="#ef4444" />
          <StatCard icon="" label="Sources surveillées" value={2} color="#3b82f6" onClick={() => setShowSourcesModal(true)} />
        </div>

        {/* Projects list */}
        <div style={{ marginBottom: '32px' }}>
          <h2 style={{
            fontSize: '16px', fontWeight: 600, color: 'var(--text-primary)',
            margin: '0 0 16px', display: 'flex', alignItems: 'center', gap: '8px',
          }}>
            Projets récents
          </h2>

          {loadingProjects ? (
            <div style={{ display: 'flex', justifyContent: 'center', padding: '40px' }}>
              <Spinner size={32} />
            </div>
          ) : projects.length === 0 ? (
            <EmptyState
              icon=""
              title="Aucun projet"
              description="Créez votre premier projet pour commencer à déposer des BOM."
              action={
                <button
                  onClick={() => navigate('/projects/new')}
                  style={{
                    background: 'var(--accent)', color: '#0a0f0d', border: 'none',
                    borderRadius: '8px', padding: '10px 20px', cursor: 'pointer',
                    fontWeight: 600, fontSize: '14px', fontFamily: 'inherit',
                  }}
                >
                  + Nouveau projet
                </button>
              }
            />
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {projects.slice(0, 8).map((project) => (
                <ProjectRow
                  key={project.id}
                  project={project}
                  onClick={() => navigate(`/projects/${project.id}`)}
                />
              ))}
              {projects.length > 8 && (
                <button
                  onClick={() => navigate('/projects')}
                  style={{
                    background: 'transparent', border: '1px dashed var(--border)',
                    borderRadius: '10px', padding: '12px', cursor: 'pointer',
                    color: 'var(--text-muted)', fontSize: '13px', fontFamily: 'inherit',
                  }}
                >
                  Voir tous les projets ({projects.length})
                </button>
              )}
            </div>
          )}
        </div>
      </div>

      {showSourcesModal && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          background: 'rgba(0,0,0,0.6)', display: 'flex', alignItems: 'center', justifyContent: 'center',
          zIndex: 100, padding: '20px',
        }}>
          <div className="arbor-animate-in" style={{
            background: 'var(--bg-secondary)', borderRadius: '16px', padding: '32px',
            maxWidth: '500px', width: '100%', border: '1px solid var(--border)'
          }}>
            <h2 style={{ margin: '0 0 16px', fontSize: '20px', fontWeight: 600 }}>Sources de Vulnérabilités</h2>
            <p style={{ fontSize: '14px', color: 'var(--text-muted)', marginBottom: '24px', lineHeight: 1.5 }}>
              Voici les bases de données interrogées pour identifier les vulnérabilités dans vos composants.
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', marginBottom: '32px' }}>
              <div style={{ padding: '16px', border: '1px solid var(--border)', borderRadius: '12px', background: 'var(--bg-tertiary)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <h3 style={{ margin: 0, fontSize: '15px', fontWeight: 600 }}>NVD (National Vulnerability Database)</h3>
                  <span style={{ fontSize: '12px', background: 'rgba(59, 130, 246, 0.1)', color: '#3b82f6', padding: '4px 8px', borderRadius: '12px', fontWeight: 600 }}>Actif</span>
                </div>
                <p style={{ margin: '0 0 8px', fontSize: '13px', color: 'var(--text-muted)' }}>La base de données officielle du gouvernement américain (NIST).</p>
                <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Mise à jour : <strong style={{ color: 'var(--text-primary)' }}>Toutes les 2 heures</strong></div>
              </div>

              <div style={{ padding: '16px', border: '1px solid var(--border)', borderRadius: '12px', background: 'var(--bg-tertiary)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <h3 style={{ margin: 0, fontSize: '15px', fontWeight: 600 }}>GitHub Advisory Database</h3>
                  <span style={{ fontSize: '12px', background: 'rgba(59, 130, 246, 0.1)', color: '#3b82f6', padding: '4px 8px', borderRadius: '12px', fontWeight: 600 }}>Actif</span>
                </div>
                <p style={{ margin: '0 0 8px', fontSize: '13px', color: 'var(--text-muted)' }}>Vulnérabilités signalées sur les paquets open source (npm, PyPI, etc.).</p>
                <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Mise à jour : <strong style={{ color: 'var(--text-primary)' }}>Temps réel</strong></div>
              </div>
              
              <div style={{ padding: '16px', border: '1px dashed var(--border)', borderRadius: '12px', background: 'transparent' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <h3 style={{ margin: 0, fontSize: '15px', fontWeight: 600, color: 'var(--text-muted)' }}>OSV (Open Source Vulnerability)</h3>
                  <span style={{ fontSize: '12px', background: 'rgba(156, 163, 175, 0.1)', color: 'var(--text-muted)', padding: '4px 8px', borderRadius: '12px' }}>Désactivé</span>
                </div>
                <p style={{ margin: 0, fontSize: '13px', color: 'var(--text-muted)' }}>Activez cette source dans les paramètres de vos projets pour augmenter la couverture.</p>
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <Button onClick={() => setShowSourcesModal(false)}>Fermer</Button>
            </div>
          </div>
        </div>
      )}
    </Layout>
  )
}

function ProjectRow({ project, onClick }: { project: Project; onClick: () => void }) {
  return (
    <div
      onClick={onClick}
      style={{
        display: 'flex', alignItems: 'center', gap: '16px',
        background: 'var(--bg-secondary)', border: '1px solid var(--border)',
        borderRadius: '10px', padding: '14px 18px', cursor: 'pointer',
        transition: 'all 150ms ease',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.borderColor = 'var(--border-hover)'
        e.currentTarget.style.background = 'var(--bg-tertiary)'
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.borderColor = 'var(--border)'
        e.currentTarget.style.background = 'var(--bg-secondary)'
      }}
    >
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: '14px' }}>
          {project.name}
          {project.archived_at && (
            <span style={{ marginLeft: '8px', fontSize: '11px', color: 'var(--text-muted)', fontWeight: 400 }}>
              (archivé)
            </span>
          )}
        </div>
        {project.description && (
          <div style={{ fontSize: '13px', color: 'var(--text-muted)', marginTop: '2px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {project.description}
          </div>
        )}
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '20px', flexShrink: 0 }}>
        {project.critical_alert_count > 0 && (
          <span style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '13px', color: '#ef4444', fontWeight: 600 }}>
            {project.critical_alert_count}
          </span>
        )}
        {project.alert_count > 0 && (
          <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
            {project.alert_count} alerte{project.alert_count > 1 ? 's' : ''}
          </span>
        )}
        <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
          {project.last_bom_date
            ? new Date(project.last_bom_date).toLocaleDateString('fr-FR')
            : 'Aucune BOM'}
        </span>
        <span style={{ color: 'var(--text-muted)', fontSize: '16px' }}>›</span>
      </div>
    </div>
  )
}
