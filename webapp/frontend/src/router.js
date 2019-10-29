import Vue from 'vue'
import Router from 'vue-router'
import Home from './views/Home.vue'
import TrainAnnotations from './views/TrainAnnotations.vue'
import Demo from './views/Demo.vue'

Vue.use(Router)

export default new Router({
  mode: 'history',
  base: process.env.BASE_URL,
  routes: [
    {
      path: '/',
      name: 'home',
      component: Home
    },
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
    }
  ]
})
