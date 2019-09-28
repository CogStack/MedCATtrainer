<template>
  <div @login:success="loginSuccessful">
    <nav class="navbar">
      <router-link class="navbar-brand app-name" to="/">Med<img class="icon" src="./assets/cat-logo.png" >AT</router-link>
      <!--<router-link class="navbar-brand" to="/demo">Test</router-link>-->
      <a class="navbar-brand ml-auto small">
        <span @click="loginModal = true">
          <span class="link" v-if="uname === null">Login</span>
          <span class="link" v-if="uname !== null">
            ({{uname}})
            <font-awesome-icon icon="user"></font-awesome-icon>
          </span>
        </span>
        <span v-if="uname !== null" class="link logout" @click="logout">logout</span>
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
      this.uname = this.$cookie.get('username')
      this.goHome()
    },
    logout: function () {
      this.$cookie.delete('username')
      this.$cookie.delete('api-token')
      this.goHome()
    },
    goHome: function () {
      if (this.$route.name !== 'home') {
        this.$router.push({
          name: 'home'
        })
      } else {
        location.reload()
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

.link {
  padding-top: 10px;
  display:inline-block;
  height: 35px;
  cursor: pointer;

  &:hover {
    opacity: 0.6;
  }
}

.logout {
  padding-left: 20px;
}

.icon {
  height: 38px;
  position: relative;
  bottom: 7px;
}

</style>
