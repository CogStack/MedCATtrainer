<template>
  <div>
    <div class="main-panel">
      <h4 class="title">Add Annotation</h4>
      <div class="sidebar">
        <table class="add-synonym-table">
          <tbody>
          <tr>
            <td>New Annotation</td>
            <td>{{name}}</td>
          </tr>
          <tr @keyup.stop>
            <td>Concept Lookup</td>
            <td>
              <v-select v-model="selectedCUI" label="name" @search="searchCUI" :options="searchResults"></v-select>
            </td>
          </tr>
          <tr>
            <td>Context</td>
            <td class="context">{{this.prevText}}<span class="highlight">{{this.name}}</span>{{this.nextText}}</td>
          </tr>
          </tbody>
        </table>
        <table class="add-synonym-table" v-if="selectedCUI">
          <tbody>
          <tr>
            <td>Name</td>
            <td>{{selectedCUI.name || 'n/a'}}</td>
          </tr>
          <tr>
            <td>Term ID</td>
            <td>{{selectedCUI.tui || 'n/a'}}</td>
          </tr>
          <tr>
            <td>Semantic Type</td>
            <td>{{selectedCUI.semantic_type || 'n/a'}}</td>
          </tr>
          <tr>
            <td>Concept ID</td>
            <td >{{selectedCUI.cui || 'n/a'}}</td>
          </tr>
          <tr>
            <td>Description</td>
            <td v-html="selectedCUI.desc === 'nan' ? 'n/a' : selectedCUI.desc || 'n/a'"></td>
          </tr>
          <tr>
            <td>Synonyms</td>
            <td>{{selectedCUI.synonyms || 'n/a'}}</td>
          </tr>
          </tbody>
        </table>
      </div>
    </div>
    <div class="action-buttons">
      <button @click="submit()" class="btn task-btn-0">
        <font-awesome-icon icon="plus"></font-awesome-icon>
        Add Synonym
      </button>
      <button @click="cancel()" class="btn task-btn-1">
        <font-awesome-icon icon="times"></font-awesome-icon>
        Cancel
      </button>
    </div>
  </div>
</template>

<script>
import _ from 'lodash'

import vSelect from 'vue-select'

export default {
  name: 'AddSynoym',
  components: {
    vSelect
  },
  props: {
    selection: Object,
    projectTUIs: String,
    projectId: Number,
    documentId: Number
  },
  data: function () {
    return {
      name: this.selection.selStr,
      prevText: this.selection.prevText,
      nextText: this.selection.nextText,
      searchResults: [],
      selectedCUI: null
    }
  },
  watch: {
    'selectedCUI': 'selectedSynonymCUI'
  },
  methods: {
    searchCUI: _.debounce(function (term, loading) {
      loading(true)
      this.$http.get(`/api/search-concepts/?search=${term}&tui__in=${this.projectTUIs}`)
        .then(resp => {
          loading(false)
          this.searchResults = resp.data.results.map(r => {
            return {
              name: r.pretty_name,
              cui: r.cui,
              tui: r.tui,
              type: r.type,
              desc: r.desc,
              semantic_type: r.semantic_type,
              synonyms: _.replace(r.synonyms, new RegExp(',', 'g'), ', ')
            }
          })
        })
    }, 400),
    selectedSynonymCUI: function () {
      this.searchResults = []
    },
    submit: function () {
      const payload = {
        source_value: this.selection.selStr,
        document_id: this.documentId,
        project_id: this.projectId,
        right_context: this.selection.nextText,
        cui: this.selectedCUI.cui
      }
      this.$http.post('/api/add-annotation/', payload).then(resp => {
        this.$emit('request:addAnnotationComplete', resp.data.id)
        this.selectedCUI = null
      })
    },
    cancel: function () {
      this.$emit('request:addAnnotationComplete')
    }
  }
}
</script>

<style scoped lang="scss">
.title {
  padding: 5px 15px;
  font-size: 16pt;
  box-shadow: 0 5px 5px -5px rgba(0,0,0,0.2);
}

.sidebar {
  width: 100%;
  overflow: auto;
}

.context {
  white-space: pre-wrap;
}

.highlight {
  background: lightgrey;
  border: 3px solid lightgrey;
  border-radius: 8px;
}

.action-buttons {
  padding-top: 20px;
  text-align: center;
}

ul.vs__dropdown-menu {
  /*z-index: 100000000 !important;*/
  /*position: absolute !important;*/
}

.add-synonym-table {
  position: relative;
  z-index: 0;
  width: 400px;
  tbody > tr {
    box-shadow: 0 5px 5px -5px rgba(0,0,0,0.2);

    > td {
      padding: 10px 15px;
      vertical-align: top;
      color: $text;
    }
  }
}
</style>
