<template>
  <div class="task-bar">
    <button :disabled="!(this.projectId && this.documentId)" @click="submit()" class="btn btn-outline-primary mb-2 submit-btn submit"
            type="button">Submit</button>
  </div>
</template>

<script>
export default {
  name: 'TaskBar',
  props: {
    projectId: null,
    documentId: null
  },
  methods: {
    submit () {
      const payload = {
        project_id: this.projectId,
        document_id: this.documentId
      }
      this.$http.post('/api/submit-doc-anno-document/', payload).then(_ => {
        this.$emit('submit:successful')
      })
    },
    keyup  (e) {
      if (e.keyCode === 13) {
        this.submit()
      }
    },
    listenSubmit () {
      window.addEventListener('keyup', this.keyup)
    },
    ignoreSubmit () {
      window.removeEventListener('keyup', this.keyup)
    }
  },
  mounted () {
    this.listenSubmit()
  },
  beforeDestroy () {
    this.ignoreSubmit()
  }
}
</script>

<style scoped lang="scss">
.task-bar {
  width: 100%;
  display: inline-block;
  padding: 10px 0;
  background-color: $background;
  color: $text;
  text-align: center;

  .submit {
    float: right;
    width: 100px;
    margin-bottom: 0 !important;
  }
}

</style>
