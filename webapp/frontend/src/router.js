import Vue from 'vue'
import Router from 'vue-router'
import Home from '@/views/Home.vue'
import EntityAnnotations from '@/views/EntityAnnotations.vue'
import DocAnnotations from '@/views/DocAnnotations'
import Demo from './views/Demo.vue'

Vue.use(Router)

export default new Router({
  mode: 'history',
  base: process.env.BASE_URL,
  routes: [
    {
      path: '/entity-annotations/:projectId/:docId?',
      name: 'entity-annotations',
      component: EntityAnnotations,
      props: true
    },
    {
      path: '/doc-annotations/:projectId/:docId?',
      name: 'doc-annotations',
      component: DocAnnotations,
      props: true
    },
    {
      path: '/demo',
      name: 'demo',
      component: Demo
    },
    {
      path: '*',
      name: 'home',
      component: Home
    }
  ]
})
