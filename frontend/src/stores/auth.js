import { defineStore } from 'pinia'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('token') || null, // Пытаемся получить токен из localStorage
    user: null, 
  }),

  getters: {
    isAuthenticated: (state) => !!state.token,
    getToken: (state) => state.token,
    getUser: (state) => state.user,
  },

  actions: {
    setToken(token) {
      this.token = token
      // Сохраняем токен в localStorage для сохранения между сессиями
      localStorage.setItem('token', token)
    },

    clearToken() {
      this.token = null
      this.user = null
      // Удаляем токен из localStorage
      localStorage.removeItem('token')
    },
  },
})