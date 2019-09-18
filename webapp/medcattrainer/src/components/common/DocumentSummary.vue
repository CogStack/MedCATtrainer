<template>
  <div class="border-top border-right border-bottom doc-summary">
    <div v-if="loadingDoc" class="loading-doc"></div>
    <div v-for="doc of docs" :key="doc.id" class="doc clickable"
         :class="{'selected-doc': selectedDocId === doc.id}" @click="loadDoc(doc.id)">
      <font-awesome-icon v-if="validatedDocIds.includes(doc.id)" class="validated-doc" icon="check"></font-awesome-icon>
      <div class="note-summary">
        {{doc.text}}
      </div>
    </div>
    <div class="clickable">
      <div v-if="moreDocs" @click="loadMoreDocs">
        + Load More Docs...
      </div>
    </div>
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
  flex: 0 0 300px;
  padding: 5px;
  overflow: auto;
  position: relative;
}

.doc {
  padding: 5px 3px;
  border-bottom: 1px solid #F0F0F0;

  &:hover {
    background: #f8f8f8;
  }
}

.selected-doc {
  border-left: 3px solid $primary;
}

.validated-doc {
  float: right;
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

.note-summary {
  white-space: pre-wrap;
  /*padding: 5px;*/
  font-size: 11px;
  overflow: hidden;
  position: relative;
  height: 12em; /* 10 lines */

  &:after {
    content: "";
    text-align: right;
    position: absolute;
    bottom: 0;
    right: 0;
    width: 80%;
    height: 1.2em;
    background: linear-gradient(to right, rgba(255, 255, 255, 0), rgba(255, 255, 255, 1) 50%);
  }
}

</style>
