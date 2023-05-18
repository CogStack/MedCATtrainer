import Vue from 'vue'
import Router from 'vue-router'
import Home from './views/Home.vue'
import TrainAnnotations from './views/TrainAnnotations.vue'
import Demo from './views/Demo.vue'
import ConceptDatabase from './views/ConceptDatabase'
import Metrics from './views/Metrics'

Vue.use(Router)

export default new Router({
  mode: 'history',
  base: process.env.BASE_URL,
  routes: [
    {
      path: '/train-annotations/:projectId/:docId?',
      name: 'train-annotations',
      component: TrainAnnotations,
      props: true
    },
    {
      path: '/metrics/',
      name: 'metrics',
      component: Metrics,
      query: true
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
