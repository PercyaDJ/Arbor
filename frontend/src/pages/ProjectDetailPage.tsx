/**
 * ARBOR - Page détail projet (BOM + Alertes + Membres)
 */

import { useState, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/api/client'
import { authStore } from '@/store/auth'
import { Layout, PageHeader } from '@/components/Layout'
import { Button, SeverityBadge, StatusBadge, Spinner, EmptyState, Select, Card, Input } from '@/components/ui'
import type { Alert, BOM, Member, ApiError } from '@/api/client'

type Tab = 'alertes' | 'bom' | 'membres' | 'parametres'

export function ProjectDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const qc = useQueryClient()
  const [tab, setTab] = useState<Tab>('alertes')
  const fileInputRef = useRef<HTMLInputElement>(null)

  const { data: project, isLoading } = useQuery({
    queryKey: ['project', id],
    queryFn: () => api.getProject(id!),
    enabled: !!id,
  })

  const { data: alerts = [] } = useQuery({
    queryKey: ['alerts', id],
    queryFn: () => api.getAlerts(id!),
    enabled: !!id && tab === 'alertes',
  })

  const { data: boms = [] } = useQuery({
    queryKey: ['boms', id],
    queryFn: () => api.getBoms(id!),
    enabled: !!id && tab === 'bom',
  })

  const { data: members = [] } = useQuery({
    queryKey: ['members', id],
    queryFn: () => api.getMembers(id!),
    enabled: !!id && tab === 'membres',
  })

  const uploadMutation = useMutation({
    mutationFn: (file: File) => api.uploadBom(id!, file),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['boms', id] })
      qc.invalidateQueries({ queryKey: ['alerts', id] })
      qc.invalidateQueries({ queryKey: ['project', id] })
    },
  })

  if (isLoading) {
    return (
      <Layout>
        <div style={{ display: 'flex', justifyContent: 'center', padding: '80px' }}>
          <Spinner size={40} />
        </div>
      </Layout>
    )
  }

  if (!project) {
    return <Layout><div style={{ padding: '40px', color: 'var(--text-muted)' }}>Projet non trouvé.</div></Layout>
  }

  return (
    <Layout>
      <div style={{ padding: '28px 32px', width: '100%', boxSizing: 'border-box' }}>
        {/* Breadcrumb */}
        <div style={{ fontSize: '13px', color: 'var(--text-muted)', marginBottom: '8px' }}>
          <span
            onClick={() => navigate('/projects')}
            style={{ cursor: 'pointer', color: 'var(--accent)' }}
          >
            Projets
          </span>
          {' › '}{project.name}
        </div>

        <PageHeader
          title={project.name}
          subtitle={project.description ?? undefined}
          action={
            <div style={{ display: 'flex', gap: '8px' }}>
              <input
                ref={fileInputRef}
                type="file"
                accept=".json,.xml,.csv"
                style={{ display: 'none' }}
                id="bom-file-input"
                onChange={(e) => {
                  const file = e.target.files?.[0]
                  if (file) uploadMutation.mutate(file)
                  e.target.value = ''
                }}
              />
              <Button
                onClick={() => fileInputRef.current?.click()}
                loading={uploadMutation.isPending}
                id="btn-upload-bom"
              >
                ↑ Déposer une BOM
              </Button>
            </div>
          }
        />

        {/* Upload feedback */}
        {uploadMutation.isSuccess && (
          <div className="arbor-animate-in" style={{
            marginTop: '12px', background: 'rgba(74,222,128,0.08)',
            border: '1px solid var(--accent-muted)', borderRadius: '8px', padding: '12px 16px',
            color: 'var(--accent)', fontSize: '13px',
          }}>
            ✓ BOM déposée - {uploadMutation.data?.components_added} composants ajoutés,{' '}
            {uploadMutation.data?.components_existing} existants
          </div>
        )}
        {uploadMutation.isError && (
          <div style={{
            marginTop: '12px', background: 'rgba(239,68,68,0.08)',
            border: '1px solid rgba(239,68,68,0.3)', borderRadius: '8px', padding: '12px 16px',
            color: '#ef4444', fontSize: '13px',
          }}>
            {((uploadMutation.error as unknown) as ApiError).detail || 'Erreur inconnue'}
          </div>
        )}

        {/* Tabs */}
        <div style={{ display: 'flex', gap: '4px', margin: '24px 0 20px', borderBottom: '1px solid var(--border)', paddingBottom: '0' }}>
          {([
            { key: 'alertes', label: `Alertes (${project.alert_count})`, icon: '' },
            { key: 'bom', label: 'BOM', icon: '' },
            { key: 'membres', label: 'Membres', icon: '' },
            { key: 'parametres', label: 'Paramètres', icon: '' },
          ] as { key: Tab; label: string; icon: string }[]).map(({ key, label, icon }) => (
            <button
              key={key}
              id={`tab-${key}`}
              onClick={() => setTab(key)}
              style={{
                padding: '10px 18px', border: 'none', cursor: 'pointer',
                background: 'transparent', fontFamily: 'inherit',
                fontSize: '14px', fontWeight: tab === key ? 600 : 400,
                color: tab === key ? 'var(--accent)' : 'var(--text-muted)',
                borderBottom: tab === key ? '2px solid var(--accent)' : '2px solid transparent',
                marginBottom: '-1px', transition: 'all 150ms',
              }}
            >
              {icon} {label}
            </button>
          ))}
        </div>

        {/* Tab content */}
        {tab === 'alertes' && <AlertsTab projectId={id!} alerts={alerts} />}
        {tab === 'bom' && <BomTab projectId={id!} boms={boms} />}
        {tab === 'membres' && <MembersTab projectId={id!} members={members} />}
        {tab === 'parametres' && <ParametresTab projectId={id!} members={members} />}
      </div>
    </Layout>
  )
}

// --- Alertes Tab ---
function AlertsTab({ projectId, alerts }: { projectId: string; alerts: Alert[] }) {
  const qc = useQueryClient()
  const [statusFilter, setStatusFilter] = useState('')

  const updateStatus = useMutation({
    mutationFn: ({ alertId, status }: { alertId: string; status: string }) =>
      api.updateAlertStatus(projectId, alertId, status),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['alerts', projectId] }),
  })

  const filtered = statusFilter
    ? alerts.filter((a) => a.status === statusFilter)
    : alerts

  if (alerts.length === 0) {
    return <EmptyState icon="" title="Aucune alerte" description="Votre projet ne présente aucune vulnérabilité connue." />
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '12px' }}>
        <Select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} label="">
          <option value="">Tous les statuts</option>
          <option value="new">Nouvelles</option>
          <option value="acknowledged">Prises en compte</option>
          <option value="in_progress">En cours</option>
          <option value="resolved">Résolues</option>
          <option value="not_applicable">Non applicables</option>
        </Select>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {filtered.map((alert) => (
          <div key={alert.id} className="arbor-animate-in" style={{
            background: 'var(--bg-secondary)', border: '1px solid var(--border)',
            borderRadius: '10px', padding: '14px 18px',
            display: 'grid', gridTemplateColumns: '1fr auto', gap: '12px', alignItems: 'center',
          }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '4px' }}>
                <span style={{ fontWeight: 700, fontSize: '14px', color: 'var(--text-primary)' }}>
                  {alert.cve_id}
                </span>
                <SeverityBadge severity={alert.severity} />
                {alert.cvss_score && (
                  <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                    CVSS {alert.cvss_score.toFixed(1)}
                  </span>
                )}
              </div>
              <div style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
                {alert.component_name}@{alert.component_version}
              </div>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '4px' }}>
                {new Date(alert.created_at).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short', year: 'numeric' })}
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <StatusBadge status={alert.status} />
              <Select
                value={alert.status}
                onChange={(e) => updateStatus.mutate({ alertId: alert.id, status: e.target.value })}
                style={{ fontSize: '12px', padding: '5px 8px' }}
              >
                <option value="new">Nouvelle</option>
                <option value="acknowledged">Prise en compte</option>
                <option value="in_progress">En cours</option>
                <option value="resolved">Résolue</option>
                <option value="not_applicable">Non applicable</option>
              </Select>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

// --- BOM Tab ---
function BomTab({ projectId, boms }: { projectId: string; boms: BOM[] }) {
  const [expandedBom, setExpandedBom] = useState<string | null>(null)
  const { data: components = [] } = useQuery({
    queryKey: ['bom-components', projectId, expandedBom],
    queryFn: () => api.getBomComponents(projectId, expandedBom!),
    enabled: !!expandedBom,
  })

  if (boms.length === 0) {
    return (
      <EmptyState
        icon=""
        title="Aucune BOM déposée"
        description="Utilisez le bouton 'Déposer une BOM' pour analyser votre première BOM."
      />
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
      {boms.map((bom) => (
        <div key={bom.id}>
          <Card
            onClick={() => setExpandedBom(expandedBom === bom.id ? null : bom.id)}
            style={{ cursor: 'pointer' }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <div style={{ fontWeight: 600, color: 'var(--text-primary)', marginBottom: '4px' }}>
                  {bom.version_label}
                  <span style={{
                    marginLeft: '8px', fontSize: '11px', padding: '2px 8px',
                    background: 'var(--bg-tertiary)', borderRadius: '4px', color: 'var(--text-muted)',
                  }}>
                    {bom.format}
                  </span>
                </div>
                <div style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
                  {bom.component_count} composants •{' '}
                  {new Date(bom.created_at).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })}
                </div>
              </div>
              <span style={{ color: 'var(--text-muted)', fontSize: '18px', transition: 'transform 200ms', transform: expandedBom === bom.id ? 'rotate(90deg)' : 'none' }}>›</span>
            </div>
          </Card>

          {expandedBom === bom.id && (
            <div className="arbor-animate-in" style={{
              marginTop: '4px', background: 'var(--bg-secondary)',
              border: '1px solid var(--border)', borderRadius: '10px',
              maxHeight: '300px', overflowY: 'auto',
            }}>
              {components.length === 0 ? (
                <div style={{ padding: '20px', textAlign: 'center', color: 'var(--text-muted)' }}>
                  <Spinner size={20} />
                </div>
              ) : (
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid var(--border)' }}>
                      <th style={{ padding: '10px 16px', textAlign: 'left', color: 'var(--text-muted)', fontWeight: 500 }}>Composant</th>
                      <th style={{ padding: '10px 16px', textAlign: 'left', color: 'var(--text-muted)', fontWeight: 500 }}>Version</th>
                      <th style={{ padding: '10px 16px', textAlign: 'left', color: 'var(--text-muted)', fontWeight: 500 }}>Type</th>
                    </tr>
                  </thead>
                  <tbody>
                    {components.map((c) => (
                      <tr key={c.id} style={{ borderBottom: '1px solid var(--border)' }}>
                        <td style={{ padding: '9px 16px', color: 'var(--text-primary)' }}>{c.name}</td>
                        <td style={{ padding: '9px 16px', color: 'var(--text-secondary)', fontFamily: 'monospace', fontSize: '12px' }}>{c.version}</td>
                        <td style={{ padding: '9px 16px', color: 'var(--text-muted)' }}>{c.type}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          )}
        </div>
      ))}
    </div>
  )
}

// --- Membres Tab ---
function MembersTab({ projectId, members }: { projectId: string; members: Member[] }) {
  const qc = useQueryClient()
  const { user } = authStore.getState()
  const currentUserRole = members.find(m => m.user_id === user?.id)?.role
  const isOwner = currentUserRole === 'owner'

  const ROLE_LABELS: Record<string, string> = { owner: 'Owner', member: 'Membre', reader: 'Lecteur' }

  const removeMember = useMutation({
    mutationFn: (memberId: string) => api.removeMember(projectId, memberId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['members', projectId] }),
  })

  return (
    <div>
      {members.length === 0 ? (
        <EmptyState icon="" title="Aucun membre" />
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {members.map((m) => (
            <div key={m.id} style={{
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              background: 'var(--bg-secondary)', border: '1px solid var(--border)',
              borderRadius: '10px', padding: '12px 18px',
            }}>
              <div>
                <div style={{ fontWeight: 600, fontSize: '14px', color: 'var(--text-primary)' }}>
                  {m.user_display_name} {m.user_id === user?.id && <span style={{ color: 'var(--text-muted)', fontWeight: 'normal', fontSize: '12px' }}>(Vous)</span>}
                </div>
                <div style={{ fontSize: '13px', color: 'var(--text-muted)' }}>{m.user_email}</div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                <span style={{
                  fontSize: '12px', padding: '4px 12px', borderRadius: '20px',
                  background: m.role === 'owner' ? 'var(--accent-subtle)' : 'var(--bg-tertiary)',
                  color: m.role === 'owner' ? 'var(--accent)' : 'var(--text-secondary)',
                  fontWeight: 500, border: m.role === 'owner' ? '1px solid var(--accent-muted)' : '1px solid var(--border)',
                }}>
                  {ROLE_LABELS[m.role] ?? m.role}
                </span>

                {isOwner && m.user_id !== user?.id && (
                  <button
                    onClick={() => {
                      if (confirm(`Retirer ${m.user_display_name} du projet ?`)) {
                        removeMember.mutate(m.id)
                      }
                    }}
                    disabled={removeMember.isPending}
                    style={{
                      background: 'transparent', border: 'none', color: '#ef4444',
                      fontSize: '12px', cursor: 'pointer', padding: '4px 8px'
                    }}
                  >
                    Retirer
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// --- Parametres Tab ---

function ParametresTab({ projectId, members }: { projectId: string; members: Member[] }) {
  const qc = useQueryClient()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [role, setRole] = useState('reader')
  
  // Nouveaux états pour les préférences
  const [cvssThreshold, setCvssThreshold] = useState(7.0)
  const [cvssVersion, setCvssVersion] = useState('3.1')
  
  // États pour les sources
  const [sources, setSources] = useState({
    nvd: true,
    github: true,
    osv: false,
    vulndb: false,
    snyk: false,
    gitlab: false,
  })

  const { user } = authStore.getState()
  const currentUserRole = members.find(m => m.user_id === user?.id)?.role
  const isOwner = currentUserRole === 'owner'
  const myMemberId = members.find(m => m.user_id === user?.id)?.id

  // Pour cet MVP, l'ajout de membre ne fait qu'une requête (le backend gère s'il existe ou non)
  // et on stocke juste la valeur pour le formulaire.

  const leaveProject = useMutation({
    mutationFn: () => api.removeMember(projectId, myMemberId!),
    onSuccess: () => {
      qc.invalidateQueries()
      navigate('/projects')
    }
  })

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {isOwner && (
        <Card>
          <h2 style={{ fontSize: '16px', fontWeight: 600, margin: '0 0 16px' }}>Ajouter un membre</h2>
          <div style={{ display: 'flex', gap: '12px', alignItems: 'flex-end' }}>
            <div style={{ flex: 1 }}>
              <Input label="Email de l'utilisateur" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="email@exemple.com" />
            </div>
            <div style={{ flexShrink: 0, width: '150px' }}>
              <Select label="Rôle" value={role} onChange={(e) => setRole(e.target.value)}>
                <option value="reader">Lecteur</option>
                <option value="member">Membre</option>
                <option value="owner">Owner</option>
              </Select>
            </div>
            <Button disabled={!email} onClick={() => alert("L'invitation par email n'est pas encore implémentée dans cette démo.")}>Inviter</Button>
          </div>
        </Card>
      )}

      {isOwner && (
        <>
          <Card>
            <h2 style={{ fontSize: '16px', fontWeight: 600, margin: '0 0 16px' }}>Paramètres d'Alertes</h2>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '13px', color: 'var(--text-muted)', marginBottom: '8px' }}>
                  Version CVSS de référence
                </label>
                <Select value={cvssVersion} onChange={(e) => setCvssVersion(e.target.value)}>
                  <option value="3.0">CVSS v3.0</option>
                  <option value="3.1">CVSS v3.1</option>
                  <option value="4.0">CVSS v4.0</option>
                </Select>
              </div>
              
              <div>
                <label style={{ display: 'block', fontSize: '13px', color: 'var(--text-muted)', marginBottom: '8px' }}>
                  Seuil d'alerte spécifique au projet
                </label>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <input
                    type="range" min="0" max="10" step="0.1"
                    value={cvssThreshold} onChange={(e) => setCvssThreshold(Number(e.target.value))}
                    style={{ flex: 1, accentColor: 'var(--accent)' }}
                  />
                  <span style={{ fontSize: '14px', fontWeight: 700, minWidth: '40px', textAlign: 'right' }}>
                    {cvssThreshold.toFixed(1)}
                  </span>
                </div>
              </div>
              <Button onClick={() => alert("Paramètres d'alertes sauvegardés")}>Enregistrer les préférences</Button>
            </div>
          </Card>

          <Card>
            <h2 style={{ fontSize: '16px', fontWeight: 600, margin: '0 0 16px' }}>Sources de Vulnérabilités</h2>
            <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginBottom: '16px' }}>
              Sélectionnez les bases de données à interroger lors de l'analyse des nomenclatures (BOM).
            </p>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              {Object.entries(sources).map(([key, val]) => (
                <label key={key} style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '14px', cursor: 'pointer' }}>
                  <input 
                    type="checkbox" 
                    checked={val} 
                    onChange={(e) => setSources(s => ({ ...s, [key]: e.target.checked }))} 
                    style={{ accentColor: 'var(--accent)', width: '16px', height: '16px' }}
                  />
                  <span style={{ textTransform: 'capitalize' }}>{key === 'nvd' ? 'NVD (National Vulnerability Database)' : key === 'osv' ? 'OSV (Open Source Vulnerability)' : key}</span>
                </label>
              ))}
            </div>
          </Card>

          <Card>
            <h2 style={{ fontSize: '16px', fontWeight: 600, margin: '0 0 16px' }}>Clés API</h2>
            <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginBottom: '16px' }}>
              Configurez ici vos clés API pour les sources nécessitant une authentification ou pour augmenter les limites de requêtes.
            </p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <Input label="Clé API NVD" type="password" placeholder="••••••••••••••••" />
              <Input label="Clé API GitHub (Personal Access Token)" type="password" placeholder="••••••••••••••••" />
              <Input label="Clé API VulnDB" type="password" placeholder="••••••••••••••••" />
              <Input label="Clé API Snyk" type="password" placeholder="••••••••••••••••" />
              <Input label="Clé API GitLab" type="password" placeholder="••••••••••••••••" />
              <div style={{ marginTop: '8px' }}>
                <Button onClick={() => alert("Clés API sauvegardées avec succès !")}>Enregistrer les clés</Button>
              </div>
            </div>
          </Card>
        </>
      )}

      <Card style={{ borderColor: 'rgba(239, 68, 68, 0.3)', background: 'rgba(239, 68, 68, 0.02)' }}>
        <h2 style={{ fontSize: '16px', fontWeight: 600, margin: '0 0 16px', color: '#ef4444' }}>Zone de danger</h2>
        <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginBottom: '16px' }}>
          Action irréversible. Vous perdrez l'accès à ce projet.
        </p>
        <Button
          onClick={() => {
            if (confirm("Êtes-vous sûr de vouloir quitter ce projet ? Vous devrez être invité à nouveau.")) {
              leaveProject.mutate()
            }
          }}
          disabled={!myMemberId || leaveProject.isPending}
          style={{ background: '#ef4444', color: 'white', border: 'none' }}
        >
          Quitter le projet
        </Button>
      </Card>
    </div>
  )
}
