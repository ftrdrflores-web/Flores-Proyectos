import { create } from 'zustand'
import clanService from '@services/clanService'

const useClanStore = create((set) => ({
  clan:        null,
  stats:       null,
  members:     [],
  currentWar:  null,
  isLoading:   false,

  fetchClan: async () => {
    set({ isLoading: true })
    try {
      const { data } = await clanService.getClan()
      set({ clan: data, isLoading: false })
    } catch (_) {
      set({ isLoading: false })
    }
  },

  fetchDashboard: async () => {
    set({ isLoading: true })
    try {
      const { data } = await clanService.getDashboard()
      set({
        clan:       data.clan,
        stats:      data.stats,
        currentWar: data.current_war,
        isLoading:  false,
      })
    } catch (_) {
      set({ isLoading: false })
    }
  },

  fetchMembers: async () => {
    const { data } = await clanService.getMembers()
    set({ members: data })
  },
}))

export default useClanStore