import { create } from 'zustand'

const useAuthStore = create((set) => ({
  user: null,
  accessToken: null,
  refreshToken: localStorage.getItem('refreshToken'),
  isLoggedIn: !!localStorage.getItem('refreshToken'),

  login: (tokens, user) => {
    localStorage.setItem('refreshToken', tokens.refresh_token)
    set({
      user,
      accessToken: tokens.access_token,
      refreshToken: tokens.refresh_token,
      isLoggedIn: true,
    })
  },

  logout: () => {
    localStorage.removeItem('refreshToken')
    set({ user: null, accessToken: null, refreshToken: null, isLoggedIn: false })
  },

  setAccessToken: (token) => set({ accessToken: token }),

  setUser: (user) => set({ user }),
}))

export default useAuthStore
