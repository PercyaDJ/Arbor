/**
 * ARBOR — Liste des projets
 */

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { api } from '@/api/client'
import { Layout, PageHeader } from '@/components/Layout'
import { Button, Card, EmptyState, Input, Spinner } from '@/components/ui'
import type { ApiError } from '@/api/client'

export function ProjectsPage() {
  const navigate = useNavigate()
  const qc = useQueryClient()
  const [showCreate, setShowCreate] = useState(false)
  const [newName, setNewName] = useState('')
  const [newDesc, setNewDesc] = useState('')
  const [createError, setCreateError] = useState('')

  const { data: projects = [], isLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: () => api.getProjects(),
  })

  const createMutation = useMutation({
    mutationFn: () => api.createProject({ name: newName, description: newDesc || undefined }),
    onSuccess: (p) => {
      qc.invalidateQueries({ queryKey: ['projects'] })
      setShowCreate(false)
      setNewName('')
      setNewDesc('')
      navigate(`/projects/${p.id}`)
    },
    onError: (err) => setCreateError((err as ApiError).detail),
  })

  const activeProjects = projects.filter((p) => !p.archived_at)
  const archivedProjects = projects.filter((p) => p.archived_at)

  return (
    <Layout>
      <div style={{ padding: '28px 32px', maxWidth: '1100px' }}>
        <PageHeader
          title="Projets"
          subtitle={`${activeProjects.length} projet${activeProjects.length !== 1 ? 's' : ''} actif${activeProjects.length !== 1 ? 's' : ''}`}
          action={
            <Button onClick={() => setShowCreate(!showCreate)} id="btn-new-project">
              + Nouveau projet
            </Button>
          }
        />

        {/* Formulaire de création */}
        {showCreate && (
          <div className="arbor-animate-in" style={{
            margin: '20px 0', background: 'var(--bg-secondary)',
            border: '1px solid var(--accent-muted)', borderRadius: '12px', padding: '20px',
          }}>
            <h3 style={{ margin: '0 0 16px', fontSize: '15px', color: 'var(--text-primary)' }}>
              Nouveau projet
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <Input
                label="Nom du projet *"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                placeholder="ex: API Backend, Frontend Web, Infra K8s..."
                id="project-name"
              />
              <Input
                label="Description (optionnelle)"
                value={newDesc}
                onChange={(e) => setNewDesc(e.target.value)}
                placeholder="Brève description du périmètre..."
                id="project-desc"
              />
              {createError && (
                <div style={{ color: '#ef4444', fontSize: '13px' }}>⚠ {createError}</div>
              )}
              <div style={{ display: 'flex', gap: '8px' }}>
                <Button
                  onClick={() => createMutation.mutate()}
                  loading={createMutation.isPending}
                  disabled={!newName.trim()}
                  id="project-create-submit"
                >
                  Créer le projet
                </Button>
                <Button variant="ghost" onClick={() => setShowCreate(false)}>Annuler</Button>
              </div>
            </div>
          </div>
        )}

        {/* Liste */}
        {isLoading ? (
          <div style={{ display: 'flex', justifyContent: 'center', padding: '60px' }}>
            <Spinner size={36} />
          </div>
        ) : projects.length === 0 ? (
          <div style={{ marginTop: '32px' }}>
            <EmptyState
              icon="📁"
              title="Aucun projet"
              description="Créez votre premier projet pour commencer à déposer des BOM."
              action={<Button onClick={() => setShowCreate(true)}>+ Créer un projet</Button>}
            />
          </div>
        ) : (
          <div style={{ marginTop: '24px' }}>
            <ProjectGrid projects={activeProjects} onSelect={(id) => navigate(`/projects/${id}`)} />

            {archivedProjects.length > 0 && (
              <div style={{ marginTop: '32px' }}>
                <div style={{ fontSize: '13px', color: 'var(--text-muted)', marginBottom: '12px', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                  Archivés ({archivedProjects.length})
                </div>
                <ProjectGrid projects={archivedProjects} onSelect={(id) => navigate(`/projects/${id}`)} dimmed />
              </div>
            )}
          </div>
        )}
      </div>
    </Layout>
  )
}

function ProjectGrid({ projects, onSelect, dimmed }: {
  projects: ReturnType<typeof api.getProjects> extends Promise<infer T> ? T : never
  onSelect: (id: string) => void
  dimmed?: boolean
}) {
  return (
    <div style={{
      display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
      gap: '14px', opacity: dimmed ? 0.6 : 1,
    }}>
      {projects.map((project) => (
        <Card key={project.id} onClick={() => onSelect(project.id)}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
            <div style={{ fontWeight: 700, fontSize: '15px', color: 'var(--text-primary)' }}>
              {project.name}
            </div>
            {project.critical_alert_count > 0 && (
              <span style={{
                background: 'rgba(239,68,68,0.15)', color: '#ef4444',
                borderRadius: '20px', padding: '2px 10px', fontSize: '12px', fontWeight: 600,
              }}>
                🚨 {project.critical_alert_count}
              </span>
            )}
          </div>

          {project.description && (
            <div style={{
              fontSize: '13px', color: 'var(--text-muted)', marginBottom: '14px',
              overflow: 'hidden', textOverflow: 'ellipsis',
              display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical',
            }}>
              {project.description}
            </div>
          )}

          <div style={{
            display: 'flex', justifyContent: 'space-between',
            fontSize: '12px', color: 'var(--text-muted)',
            paddingTop: '12px', borderTop: '1px solid var(--border)',
          }}>
            <span>
              {project.alert_count > 0
                ? `${project.alert_count} alerte${project.alert_count > 1 ? 's' : ''}`
                : '✓ Aucune alerte'}
            </span>
            <span>
              {project.last_bom_date
                ? new Date(project.last_bom_date).toLocaleDateString('fr-FR')
                : 'Aucune BOM'}
            </span>
          </div>
        </Card>
      ))}
    </div>
  )
}
