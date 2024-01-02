<template>
  <modal class="login" :closable="closable" @modal:close="$emit('login:close')">
    <h3 slot="header">Login</h3>
    <div slot="body">
      <form @submit.prevent class="form">
        <label>Username:</label>
        <input v-model="uname" class="form-control" id="uname">
        <label>Password:</label>
        <input v-model="password" class="form-control" type="password" id="password">
        <div class="forgotten" @click="forgottenPassword = !forgottenPassword">Forgotten Password</div>
      </form>
      <span v-if="failed" class="text-danger">Username and/or password incorrect</span>
      <span v-if="failedAdminStatusCheck" class="text-danger">Cannot determine admin status of username</span>
      <div v-if="forgottenPassword">
        <label>Fill in the the username field above and click the button below to reset your password.</label>
        <button class="login-submit btn btn-primary" @click="reset_password()">E-mail New Password</button>
      </div>
    </div>
    <div slot="footer">
      <button class="login-submit btn btn-primary" @click="login()">Login</button>
    </div>
  </modal>
</template>

<script>
import Modal from '@/components/common/Modal.vue'
import EventBus from '@/event-bus'
import axios from 'axios'

const instance = axios.create({
  baseURL: axios.baseURL,
  headers: {}
})

export default {
  name: 'Login',
  props: {
    closable: Boolean
  },
  components: {
    Modal
  },
  data () {
    return {
      uname: '',
      password: '',
      failed: false,
      failedAdminStatusCheck: false,
      forgottenPassword: false
    }
  },
  methods: {
    login () {
      let payload = {
        username: this.uname,
        password: this.password
      }

      instance.post('/api/api-token-auth/', payload, {}).then(resp => {
        this.$cookie.set('api-token', resp.data.token, { expires: 7 })
        this.$cookie.set('username', this.uname)
        this.$http.defaults.headers.common['Authorization'] = `Token ${this.$cookie.get('api-token')}`
        window.removeEventListener('keyup', this.keyup)
        this.$http.get(`/api/users/?username=${this.uname}`).then(resp => {
          if (resp.data.results.length > 0) {
            const adminState = resp.data.results[0].is_staff || resp.data.results[0].is_superuser
            const userId = resp.data.results[0].id
            this.$cookie.set('admin', adminState)
            this.$cookie.set('user-id', userId)
            EventBus.$emit('login:success')
          } else {
            this.failedAdminStatusCheck = true
            setTimeout(() => {
              this.$cookie.set('admin', false)
              this.$cookie.delete('user-id')
              EventBus.$emit('login:success')
            }, 1000)
          }
        }).catch(() => {
          this.failed = true
        })
      }).catch(() => {
        this.failed = true
      })
    },
    keyup (e) {
      if (e.keyCode === 13 && this.uname.length > 0 && this.password.length > 0) {
        this.login()
      }
    },
    reset_password () {
      let payload = {
        username: this.uname
      }

      instance.post('/api/api-reset-password/', payload, {})
    }
  },
  created () {
    window.addEventListener('keyup', this.keyup)
    this.$nextTick(function () {
      document.getElementById('uname').focus()
    })
  }
}
</script>

<style lang="scss">
.login-submit {
  margin-top: 10px;
}

.login {
  .modal-container {
    width: 400px;
  }
}

.forgotten {
  cursor:pointer;
  color:blue;
  text-decoration:underline;
}

.forgotten:hover {
  cursor:pointer;
}

</style>
