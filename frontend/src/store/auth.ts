/**
 * ARBOR - Store d'authentification (state global léger sans Redux)
 */

import { api } from '@/api/client'

interface AuthState {
  token: string | null
  user: User | null
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

// State réactif simple basé sur localStorage + callbacks
let state: AuthState = {
  token: localStorage.getItem('arbor_token'),
  user: null,
}

const listeners: Array<() => void> = []

function notify() {
  listeners.forEach((fn) => fn())
}

export const authStore = {
  subscribe(fn: () => void) {
    listeners.push(fn)
    return () => {
      const idx = listeners.indexOf(fn)
      if (idx >= 0) listeners.splice(idx, 1)
    }
  },

  getState(): AuthState {
    return state
  },

  isAuthenticated(): boolean {
    return !!state.token
  },

  async login(email: string, password: string): Promise<void> {
    const tokens = await api.login(email, password)
    api.setToken(tokens.access_token)
    localStorage.setItem('arbor_refresh', tokens.refresh_token)
    state = { ...state, token: tokens.access_token }
    // Charger le profil
    const user = await api.getMe()
    state = { ...state, user }
    notify()
  },

  logout() {
    api.clearToken()
    localStorage.removeItem('arbor_refresh')
    state = { token: null, user: null }
    notify()
  },

  async loadUser(): Promise<void> {
    if (!state.token) return
    try {
      const user = await api.getMe()
      state = { ...state, user }
      notify()
    } catch {
      this.logout()
    }
  },
}
