<template>
  <div class="border-top border-right border-bottom doc-summary">
    <div v-if="loadingDoc" class="loading-doc"></div>
    <h4 class="title">Document List</h4>
    <table class="table table-hover">
      <tbody>
        <tr v-for="doc of docs" :key="doc.id" class="doc">
          <td :class="{'selected-doc': selectedDocId === doc.id}" class="clickable" @click="loadDoc(doc.id)">
            <font-awesome-icon v-if="validatedDocIds.includes(doc.id)" class="validated-doc" icon="check"></font-awesome-icon>
            {{doc.id}} : {{doc.name}}
          </td>
        </tr>
        <tr class="clickable">
          <td v-if="moreDocs" @click="loadMoreDocs">
            + Load More Docs...
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
export default {
  name: 'DocumentSummary',
  props: {
    docs: Array,
    moreDocs: Boolean,
    selectedDocId: Number,
    loadingDoc: false,
    validatedDocIds: Array,
  },
  methods: {
    loadMoreDocs: function() {
      this.$emit('request:nextDocSet')
    },
    loadDoc: function(docId) {
      this.$emit('request:loadDoc', docId)
    },
    keyup: function(e) {
      if (e.keyCode === 40 && this.selectedDocId !== this.docs.slice(-1).id) {
        //down
        this.$emit('request:loadDoc', this.docs[this.docs.map(d => d.id).indexOf(this.selectedDocId) + 1].id)
      } else if (e.keyCode === 38 && this.selectedDocId !== this.docs[0].id) {
        //up
        this.$emit('request:loadDoc', this.docs[this.docs.map(d => d.id).indexOf(this.selectedDocId) - 1].id)
      }
    }
  },
  mounted: function() {
    window.addEventListener('keyup', this.keyup)
  },
  beforeDestroy: function() {
    window.removeEventListener('keyup', this.keyup)
  }
}
</script>

<style scoped lang="scss">
@import "bootstrap";

.title {
  padding: 5px;
}

.doc-summary {
  flex: 0 0 200px;
  padding: 5px;
  overflow: auto;
  position: relative;
}

.doc {
  padding: 3px;
}

.selected-doc {
  border-left: 3px solid $primary;
}

.validated-doc {
  color: $success
}

.clickable {
  cursor: pointer;
}

.loading-doc {
  position: absolute;
  height: 100%;
  width: 100%;
  background: $loading-background-color;
  opacity: 0.3;
}

</style>
