<template>
  <div>
    <nav class="navbar navbar-expand-lg navbar-light bg-light">
      <router-link class="navbar-brand" to="/">CAT</router-link>
      <router-link class="navbar-brand" to="/demo">Demo</router-link>
      <!--<div class="">-->
      <a class="navbar-brand ml-auto" @click="login = true">Login</a>
      <!--</div>-->

    </nav>
    <router-view/>
    <login v-if="login" @login:success="loginSuccessful()"
           :closable="true" @login:close="login=false"></login>
  </div>
</template>

<script>
import Login from '@/components/common/Login.vue'

export default {
  name: 'App',
  components: {
    Login
  },
  data: function() {
    return {
      login: false
    }
  },
  methods: {
    loginSuccessful: function() {
      this.login = false;
      location.reload()
    }
  }
}
</script>

<style scoped lang="scss">
.right {
  float: right;
}
</style>
