<template>
  <div class="doc-summary">
    <div class="title">Clinical Notes</div>
    <div v-if="loadingDoc" class="loading-doc"></div>
    <div class="doc-list">
      <div v-for="doc of docs" :key="doc.id" class="doc clickable"
           :class="{'selected-doc': selectedDocId === doc.id}" @click="loadDoc(doc.id)">
        <font-awesome-icon v-if="validatedDocIds.includes(doc.id)" class="validated-doc" icon="check"></font-awesome-icon>
        <div class="note-summary">
          {{doc.text === 'nan' ? '' : (doc.text || '') | limitText }}
        </div>
      </div>
      <div class="clickable">
        <div v-if="moreDocs" @click="loadMoreDocs" class="more-docs">
          <font-awesome-icon icon="plus" class="icon"></font-awesome-icon>More Docs
        </div>
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
    loadingDoc: Boolean,
    validatedDocIds: Array
  },
  watch: {
    'selectedDocId': 'scrollSelectedDocId'
  },
  methods: {
    scrollSelectedDocId: function () {
      const el = document.getElementsByClassName('selected-doc')
      if (el.length > 0) {
        el[0].scrollIntoView({
          block: 'center',
          behavior: 'smooth'
        })
      }
    },
    loadMoreDocs: function () {
      this.$emit('request:nextDocSet')
    },
    loadDoc: function (docId) {
      this.$emit('request:loadDoc', docId)
    },
    keyup: function (e) {
      if (!this.loadingDoc && e.keyCode === 40 && this.selectedDocId !== this.docs.slice(-1).id) {
        // down
        this.$emit('request:loadDoc', this.docs[this.docs.map(d => d.id).indexOf(this.selectedDocId) + 1].id)
      } else if (!this.loadingDoc && e.keyCode === 38 && this.selectedDocId !== this.docs[0].id && !this.loadingDoc) {
        // up
        this.$emit('request:loadDoc', this.docs[this.docs.map(d => d.id).indexOf(this.selectedDocId) - 1].id)
      }
    }
  },
  mounted: function () {
    window.addEventListener('keyup', this.keyup)
  },
  beforeDestroy: function () {
    window.removeEventListener('keyup', this.keyup)
  },
  filters: {
    limitText: function (value) {
      let splitText = value.split('\n')
      if (splitText.length > 5) {
        return splitText.slice(0, 5).join('\n')
      }
      return value
    }
  }
}
</script>

<style scoped lang="scss">
@import "bootstrap";

$width: 200px;

.title {
  padding: 5px 15px;
  font-size: 16pt;
  box-shadow: 0 5px 5px -5px rgba(0,0,0,0.2);
}

.doc-summary {
  flex: 0 0 $width;
  padding: 5px;
  position: relative;
  background: $background;
}

.doc-list {
  overflow: auto;
  height: calc(100% - 41px);
  width: $width;
}

.doc {
  padding: 5px 3px;
  border-radius: 5px;
  color: $color-5;
  margin: 15px 15px;
  box-shadow: 2px 1px 4px 3px rgba(0,0,0,0.2);

  &:hover {
    cursor: pointer;
  }
}

.selected-doc {
  border-left: 5px solid $primary;
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

.more-docs {
  color: $primary;
  text-align: center;

  .icon {
    position: relative;
    bottom: 2px;
    padding-right: 3px;
  }
}

.note-summary {
  white-space: pre-wrap;
  font-size: 11px;
  overflow: hidden;
  position: relative;
  height: 6em; /* 5 lines */

  &:after {
    content: "";
    text-align: right;
    position: absolute;
    bottom: 0;
    right: 0;
    width: 80%;
    height: 1.2em;
  }
}

</style>
