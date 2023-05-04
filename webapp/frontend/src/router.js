import Vue from 'vue'
import Router from 'vue-router'
import Home from './views/Home.vue'
import TrainAnnotations from './views/TrainAnnotations.vue'
import Demo from './views/Demo.vue'
import ConceptDatabase from './views/ConceptDatabase'

Vue.use(Router)

export default new Router({
  mode: 'history',
  base: process.env.BASE_URL,
  routes: [
    {
      path: '/train-annotations/:projectId/:docId?',
      name: 'train-annotations',
      // route level code-splitting
      // this generates a separate chunk (about.[hash].js) for this route
      // which is lazy-loaded when the route is visited.
      component: TrainAnnotations,
      props: true
    },
    {
      path: '/demo',
      name: 'demo',
      component: Demo
    },
    {
      path: '/model-explore',
      name: 'model-explore',
      component: ConceptDatabase
    },
    {
      path: '*',
      name: 'home',
      component: Home
    }
  ]
})
