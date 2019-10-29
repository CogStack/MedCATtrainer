<template>
  <div class="container-fluid">
    <form @submit.prevent>
      <div class="form-group">
        <label>Enter some text and click Annotate</label>
        <textarea v-model="exampleText" class="form-control" name="text" rows="15"></textarea>
      </div>
      <button @click="annotate()" class="btn btn-primary">Annotate</button>
    </form>
  </div>
</template>

<script>
export default {
  name: 'Demo',
  components: {

  },
  data: function () {
    return {
      doc_json: null,
      exampleText: ''
    }
  },
  methods: {
    annotate: function () {
      // create a 'TMP' project,
      // upload the document,
      // prepare document
      // get entitites
      // enrich entitites
      // then $router.push to new page.

      this.$http.post('', { text: this.exampleText }).then(resp => {
        this.$router.push({
          name: 'train-annotations',
          params: { text: resp.data.text, entities: resp.data.entities }
        })
      })
    }
  }
}
</script>

<style scoped lang="scss">
  form {
    margin: 5%;
  }
</style>
