<template>
  <div @login:success="loginSuccessful">
    <nav class="navbar">
      <router-link class="app-name" to="/">Med<img class="icon" src="./assets/cat-logo.png" >AT</router-link>
      <router-link class="navbar-brand" to="/">Projects</router-link>
      <router-link class="navbar-brand" to="/demo">Demo</router-link>
      <span class="version-id">{{version}}</span>
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
  data () {
    return {
      loginModal: false,
      uname: this.$cookie.get('username') || null,
      version: ''
    }
  },
  methods: {
    loginSuccessful () {
      this.loginModal = false
      this.uname = this.$cookie.get('username')
      if (this.$route.name !== 'home') {
        this.$router.push({ name: 'home' })
      }
    },
    logout () {
      this.$cookie.delete('username')
      this.$cookie.delete('api-token')
      this.$cookie.delete('admin')
      if (this.$route.name !== 'home') {
        this.$router.push({ name: 'home' })
      } else {
        this.$router.go()
      }
    }
  },
  mounted () {
    EventBus.$on('login:success', this.loginSuccessful)
  },
  beforeDestroy () {
    EventBus.$off('login:success', this.loginSuccessful)
  },
  created () {
    this.$http.get('/api/version/').then(resp => {
      this.version = resp.data || ''
    })
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
  height: 60px;
  background-color: $navbar-bg;
}

.app-name {
  padding: 0 10px;
  font-size: 2.25rem;

  color: #fff;
  &:hover {
    color: #fff !important;
    text-decoration: none;
  }
}

.navbar-brand {
  color: #fff;
  border-bottom: 1px solid transparent;
  margin-left: 20px;

  &:hover {
    color: #fff;
    border-bottom: 1px solid #fff;
  }
}

.link {
  display:inline-block;
  height: 25px;
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

.version-id {
  display: inline-block;
  float: right;
  font-size: 10px;
  padding: 0 20px;
  color: $color-2;
}

</style>
