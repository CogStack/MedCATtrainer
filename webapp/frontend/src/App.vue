<template>
  <div @login:success="loginSuccessful">
    <nav class="navbar">
      <router-link class="navbar-brand app-name" to="/">Med<img class="icon" src="./assets/cat-logo.png" >AT</router-link>
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
import EventBus from '@/event-bus'

export default {
  name: 'App',
  components: {
    Login
  },
  data: function () {
    return {
      loginModal: false,
      uname: this.$cookie.get('username') || null
    }
  },
  methods: {
    loginSuccessful: function () {
      this.loginModal = false
      this.uname = this.$cookie.get('uname')
      if (this.$router.name !== 'home') {
        this.$router.push({ name: 'home' })
      }
    }
  },
  mounted: function () {
    EventBus.$on('login:success', this.loginSuccessful)
  },
  beforeDestroy: function () {
    EventBus.$off('login:success', this.loginSuccessful)
  }
}
</script>

<style scoped lang="scss">
.right {
  float: right;
}

.small {
  font-size: 14px;
  color: #fff !important;
}

.navbar {
   background-color: $navbar-bg;
}

.app-name {
  padding: 5px 0;
  font-size: 2.25rem;
  color: #fff;
  &:hover {
    color: #fff !important;
  }
}

.icon {
  height: 38px;
  position: relative;
  bottom: 7px;
}

</style>
