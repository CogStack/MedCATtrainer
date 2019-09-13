import Vue from 'vue'
import axios from 'axios'
import VueCookie from 'vue-cookie'

import App from './App.vue'
import router from './router'

import 'bootstrap'

import 'bootstrap/dist/css/bootstrap.min.css'
import 'vue-simple-context-menu/dist/vue-simple-context-menu.css'
import 'vue-select/dist/vue-select.css'

import '@/plugins/fontawesome'
import '@/assets/main.css'

Vue.use(VueCookie);

Vue.prototype.$http = axios;
Vue.config.productionTip = false;

new Vue({
  router,
  render: h => h(App)
}).$mount('#app');
