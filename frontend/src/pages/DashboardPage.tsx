/**
 * ARBOR — Dashboard principal
 */

import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { api } from '@/api/client'
import { Layout, PageHeader, StatCard } from '@/components/Layout'
import { Spinner, EmptyState } from '@/components/ui'
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

  return (
    <Layout>
      <div style={{ padding: '28px 32px', maxWidth: '1200px' }}>
        <PageHeader
          title="Tableau de bord"
          subtitle="Vue d'ensemble de votre posture de sécurité"
        />

        {/* Stats */}
        <div style={{
          display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '16px', margin: '28px 0',
        }}>
          <StatCard icon="📁" label="Projets actifs" value={activeProjectCount} color="var(--accent)" />
          <StatCard icon="🔔" label="Alertes actives" value={totalAlerts} color="#f97316" />
          <StatCard icon="🚨" label="Alertes critiques" value={criticalAlerts} color="#ef4444" />
          <StatCard icon="🔍" label="Sources surveillées" value={2} color="#3b82f6" />
        </div>

        {/* Projects list */}
        <div style={{ marginBottom: '32px' }}>
          <h2 style={{
            fontSize: '16px', fontWeight: 600, color: 'var(--text-primary)',
            margin: '0 0 16px', display: 'flex', alignItems: 'center', gap: '8px',
          }}>
            📁 Projets récents
          </h2>

          {loadingProjects ? (
            <div style={{ display: 'flex', justifyContent: 'center', padding: '40px' }}>
              <Spinner size={32} />
            </div>
          ) : projects.length === 0 ? (
            <EmptyState
              icon="📁"
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
            🚨 {project.critical_alert_count}
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
