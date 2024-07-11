import { createRouter, createWebHashHistory } from 'vue-router'
import SearchView from '../views/SearchView.vue'

const router = createRouter({
  history: createWebHashHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'search',
      component: SearchView
    }
  ]
})

export default router
