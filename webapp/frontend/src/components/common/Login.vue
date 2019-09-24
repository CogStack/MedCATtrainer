<template>
  <modal :closable="closable" @modal:close="$emit('login:close')">
    <h3 slot="header">Login</h3>
    <div slot="body">
      <form @submit.prevent class="form">
        <label>Username:</label>
        <input v-model="uname" class="form-control">
        <label>Password:</label>
        <input v-model="password" class="form-control" type="password">
      </form>
      <span v-if="failed" class="text-danger">Username and/or password incorrect</span>
    </div>
    <div slot="footer">
      <button class="login-submit btn btn-primary" @click="login()">Login</button>
    </div>
  </modal>
</template>

<script>
import Modal from '@/components/common/Modal.vue'

export default {
  name: 'Login',
  props: {
    closable: Boolean
  },
  components: {
    Modal
  },
  data: function () {
    return {
      uname: '',
      password: '',
      failed: false
    }
  },
  methods: {
    login: function () {
      this.$http.post('/api/api-token-auth/', {
        username: this.uname,
        password: this.password
      }).then(resp => {
        this.$cookie.set('api-token', resp.data.token, { expires: 1 })
        this.$cookie.set('username', this.uname)
        this.$http.defaults.headers.common['Authorization'] = `Token ${this.$cookie.get('api-token')}`
        this.$emit('login:success')
      }).catch(() => {
        this.failed = true
      })
    }
  }
}
</script>

<style scoped lang="scss">
.login-submit {
  margin-top: 10px;
}
</style>
