/**
 * ARBOR — Client API TypeScript
 * Couche d'abstraction pour les appels à l'API backend.
 */

const API_BASE = '/api/v1'

interface ApiError {
  detail: string
  status: number
}

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

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`
    }

    if (!isFormData) {
      headers['Content-Type'] = 'application/json'
    }

    const response = await fetch(`${API_BASE}${path}`, {
      method,
      headers,
      body: isFormData ? (body as FormData) : body ? JSON.stringify(body) : undefined,
    })

    if (!response.ok) {
      const error: ApiError = {
        detail: 'Erreur inconnue',
        status: response.status,
      }
      try {
        const data = await response.json()
        error.detail = data.detail || error.detail
      } catch {
        // Pas de body JSON dans la réponse d'erreur
      }
      throw error
    }

    return response.json() as Promise<T>
  }

  // --- Auth ---
  async login(email: string, password: string) {
    return this.request<{ access_token: string; refresh_token: string }>(
      'POST', '/auth/login', { email, password }
    )
  }

  // --- Santé ---
  async health() {
    return this.request<{ status: string; app: string; version: string }>(
      'GET', '/../health' // /api/health
    )
  }
}

export const api = new ArborApiClient()
export type { ApiError }
