import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('@/views/Dashboard.vue')
  },
  {
    path: '/repositories',
    name: 'Repositories',
    component: () => import('@/views/RepositoryList.vue')
  },
  {
    path: '/repositories/new',
    name: 'NewRepository',
    component: () => import('@/views/RepositoryForm.vue')
  },
  {
    path: '/repositories/:name',
    name: 'EditRepository',
    component: () => import('@/views/RepositoryForm.vue'),
    props: true
  },
  {
    path: '/keys',
    name: 'Keys',
    component: () => import('@/views/KeyList.vue')
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('@/views/Settings.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
