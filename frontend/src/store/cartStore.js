import { create } from 'zustand'
import { v4 as uuidv4 } from 'uuid'

const useCartStore = create((set, get) => ({
  sessionKey: localStorage.getItem('sessionKey'),
  itemCount: 0,

  initSessionKey: () => {
    if (!get().sessionKey) {
      const key = uuidv4()
      localStorage.setItem('sessionKey', key)
      set({ sessionKey: key })
    }
  },

  setItemCount: (n) => set({ itemCount: n }),

  clearCart: () => set({ itemCount: 0 }),
}))

export default useCartStore
