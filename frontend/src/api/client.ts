/**
 * ARBOR - Client API TypeScript complet
 */

const API_BASE = '/api/v1'

export interface ApiError {
  detail: string
  status: number
}

// --- Types ---
export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface User {
  id: string
  email: string
  display_name: string
  is_active: boolean
  is_superuser: boolean
  organisation_id: string
  notification_preferences: Record<string, unknown>
  created_at: string
}

export interface Project {
  id: string
  name: string
  description: string | null
  organisation_id: string
  settings: Record<string, unknown>
  archived_at: string | null
  created_at: string
  updated_at: string
  alert_count: number
  critical_alert_count: number
  last_bom_date: string | null
  member_count: number
}

export interface BOM {
  id: string
  project_id: string
  version_label: string
  format: string
  type: string
  sha256_hash: string
  component_count: number
  parsed_at: string | null
  created_by: string | null
  bom_metadata: Record<string, unknown>
  created_at: string
}

export interface BOMUploadResponse {
  bom: BOM
  components_added: number
  components_existing: number
  alerts_generated: number
}

export interface Component {
  id: string
  purl: string
  name: string
  version: string
  type: string
  cpe: string | null
  supplier: string | null
  license: string | null
}

export interface Alert {
  id: string
  project_id: string
  vulnerability_id: string
  component_id: string
  bom_version_id: string | null
  status: string
  notified_at: string | null
  resolved_at: string | null
  created_at: string
  cve_id: string
  severity: string
  cvss_score: number | null
  component_name: string
  component_version: string
}

export interface Member {
  id: string
  project_id: string
  user_id: string
  role: string
  user_email: string
  user_display_name: string
  created_at: string
}

export interface Invitation {
  id: string
  email: string
  invitation_url: string
  created_at: string
}

// --- Client ---
class ArborApiClient {
  private token: string | null = null

  constructor() {
    this.token = localStorage.getItem('arbor_token')
  }

  setToken(token: string) {
    this.token = token
    localStorage.setItem('arbor_token', token)
  }

  clearToken() {
    this.token = null
    localStorage.removeItem('arbor_token')
  }

  private async request<T>(
    method: string,
    path: string,
    body?: unknown,
    isFormData = false,
  ): Promise<T> {
    const headers: Record<string, string> = {}

    if (this.token) headers['Authorization'] = `Bearer ${this.token}`
    if (!isFormData) headers['Content-Type'] = 'application/json'

    const response = await fetch(`${API_BASE}${path}`, {
      method,
      headers,
      body: isFormData ? (body as FormData) : body ? JSON.stringify(body) : undefined,
    })

    if (!response.ok) {
      const error: ApiError = { detail: 'Erreur inconnue', status: response.status }
      try {
        const data = await response.json()
        error.detail = data.detail || error.detail
      } catch { /* pas de body JSON */ }
      throw error
    }

    if (response.status === 204) return undefined as T
    return response.json() as Promise<T>
  }

  // Auth
  login(email: string, password: string) {
    return this.request<TokenResponse>('POST', '/auth/login', { email, password })
  }
  refresh(refresh_token: string) {
    return this.request<TokenResponse>('POST', '/auth/refresh', { refresh_token })
  }
  register(invitation_token: string, password: string, display_name: string) {
    return this.request<User>('POST', '/auth/register', { invitation_token, password, display_name })
  }
  getMe() { return this.request<User>('GET', '/auth/me') }
  updateMe(data: Partial<User>) { return this.request<User>('PATCH', '/auth/me', data) }

  // Projects
  getProjects() { return this.request<Project[]>('GET', '/projects/') }
  getProject(id: string) { return this.request<Project>('GET', `/projects/${id}`) }
  createProject(data: { name: string; description?: string }) {
    return this.request<Project>('POST', '/projects/', data)
  }
  updateProject(id: string, data: Partial<Project>) {
    return this.request<Project>('PATCH', `/projects/${id}`, data)
  }
  archiveProject(id: string) {
    return this.request<Project>('POST', `/projects/${id}/archive`)
  }

  // Members
  getMembers(projectId: string) {
    return this.request<Member[]>('GET', `/projects/${projectId}/members`)
  }
  addMember(projectId: string, user_id: string, role: string) {
    return this.request<Member>('POST', `/projects/${projectId}/members`, { user_id, role })
  }
  updateMember(projectId: string, memberId: string, role: string) {
    return this.request<Member>('PATCH', `/projects/${projectId}/members/${memberId}`, { role })
  }
  removeMember(projectId: string, memberId: string) {
    return this.request<void>('DELETE', `/projects/${projectId}/members/${memberId}`)
  }

  // BOM
  getBoms(projectId: string) { return this.request<BOM[]>('GET', `/projects/${projectId}/bom`) }
  getBom(projectId: string, bomId: string) {
    return this.request<BOM>('GET', `/projects/${projectId}/bom/${bomId}`)
  }
  getBomComponents(projectId: string, bomId: string) {
    return this.request<Component[]>('GET', `/projects/${projectId}/bom/${bomId}/components`)
  }
  uploadBom(projectId: string, file: File, versionLabel?: string) {
    const fd = new FormData()
    fd.append('file', file)
    const qs = versionLabel ? `?version_label=${encodeURIComponent(versionLabel)}` : ''
    return this.request<BOMUploadResponse>('POST', `/projects/${projectId}/bom${qs}`, fd, true)
  }
  purgeBoms(projectId: string, keepLast = 3) {
    return this.request<{ deleted_count: number }>('POST', `/projects/${projectId}/bom/purge?keep_last=${keepLast}`)
  }

  // Alerts
  getAlerts(projectId: string, filters?: { status?: string; severity?: string }) {
    const qs = new URLSearchParams()
    if (filters?.status) qs.set('status', filters.status)
    if (filters?.severity) qs.set('severity', filters.severity)
    return this.request<Alert[]>('GET', `/projects/${projectId}/alerts?${qs}`)
  }
  updateAlertStatus(projectId: string, alertId: string, status: string) {
    return this.request<Alert>('PATCH', `/projects/${projectId}/alerts/${alertId}`, { status })
  }

  // Health
  health() {
    return this.request<{ status: string; app: string; version: string }>('GET', '/../health')
  }
}

export const api = new ArborApiClient()
