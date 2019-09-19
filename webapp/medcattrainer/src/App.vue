<template>
  <div @login:success="loginSuccessful">
    <nav class="navbar navbar-expand-lg navbar-light bg-light">
      <router-link class="navbar-brand" to="/">Med<img class="icon" src="./assets/cat-logo.png" >AT</router-link>
      <!--<router-link class="navbar-brand" to="/demo">Test</router-link>-->
      <a class="navbar-brand ml-auto small" @click="loginModal = true">
        <span v-if="!uname">Login</span>
        <span v-if="uname">
          ({{uname}})
          <font-awesome-icon icon="user"></font-awesome-icon>
        </span>
      </a>
    </nav>
    <router-view/>
    <login v-if="loginModal" @login:success="loginSuccessful()"
           :closable="true" @login:close="loginModal=false"></login>
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
      loginModal: false,
      uname: this.$cookie.get('username') || null
    }
  },
  methods: {
    loginSuccessful: function() {
      this.login = false;
      this.uname = this.$cookie('uname');
      location.reload()
    }
  }
}
</script>

<style scoped lang="scss">
.right {
  float: right;
}

.small {
  font-size: 14px;
}

.icon {
  height: 18px;
  position: relative;
  bottom: 3px;
}
</style>
