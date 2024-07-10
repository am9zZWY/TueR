import { createRouter, createWebHashHistory } from 'vue-router'
import Search from '../views/Search.vue'

const router = createRouter({
  history: createWebHashHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'search',
      component: Search
    }
  ]
})

export default router
