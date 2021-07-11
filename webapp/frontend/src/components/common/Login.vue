<template>
  <modal :closable="closable" @modal:close="$emit('login:close')">
    <h3 slot="header">Login</h3>
    <div slot="body">
      <form @submit.prevent class="form">
        <label>Username:</label>
        <input v-model="uname" class="form-control" id="uname">
        <label>Password:</label>
        <input v-model="password" class="form-control" type="password" id="password">
      </form>
      <span v-if="failed" class="text-danger">Username and/or password incorrect</span>
      <span v-if="failedAdminStatusCheck" class="text-danger">Cannot determine admin status of username</span>
    </div>
    <div slot="footer">
      <button class="login-submit btn btn-primary" @click="login()">Login</button>
    </div>
  </modal>
</template>

<script>
import Modal from '@/components/common/Modal.vue'
import EventBus from '@/event-bus'

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
      failedAdminStatusCheck: false
    }
  },
  methods: {
    login () {
      let payload = {
        username: this.uname,
        password: this.password
      }
      this.$http.post('/api/api-token-auth/', payload).then(resp => {
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

<style scoped lang="scss">
.login-submit {
  margin-top: 10px;
}
</style>
