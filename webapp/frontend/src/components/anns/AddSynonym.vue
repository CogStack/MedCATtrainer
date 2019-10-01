<template>
  <div class="sidebar">
    <div class="title">Add Annotation</div>
    <div class="main-panel">
      <table class="add-synonym-table">
        <tbody>
        <tr>
          <td>New Annotation</td>
          <td class="fit-content">{{name}}</td>
        </tr>
        <tr @keyup.stop>
          <td>Concept Lookup</td>
          <td>
            <v-select v-model="selectedCUI" label="name" @search="searchCUI" :options="searchResults"></v-select>
          </td>
        </tr>
        <tr>
          <td>Context</td>
          <td class="fit-content context">{{this.prevText}}<span class="highlight">{{this.name}}</span>{{this.nextText.slice(0, 15)}}</td>
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
        <tr v-if="selectedCUI.icd10">
          <td>ICD-10</td>
          <td class="icd-10-desc">{{selectedCUI.icd10}}</td>
        </tr>
        <tr>
          <td>Description</td>
          <td class="fit-content" v-html="selectedCUI.desc === 'nan' ? 'n/a' : selectedCUI.desc || 'n/a'"></td>
        </tr>
        <tr>
          <td>Synonyms</td>
          <td class="fit-content">{{selectedCUI.synonyms || 'n/a'}}</td>
        </tr>
        </tbody>
      </table>
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
    project: Object,
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
      let queryParams = `search=${term}&cdb__in=${this.project.cdb_search_filter.join(',')}`
      this.$http.get(`/api/search-concepts/?${queryParams}`)
        .then(resp => {
          loading(false)
          this.searchResults = resp.data.results.map(r => {
            return {
              name: r.pretty_name,
              cui: r.cui,
              tui: r.tui,
              type: r.type,
              desc: r.desc,
              icd10: r.icd10,
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
        project_id: this.project.id,
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
    },
    keyup: function (e) {
      if (e.keyCode === 27) {
        this.cancel()
      }
    }
  },
  mounted: function () {
    window.addEventListener('keyup', this.keyup)
  },
  beforeDestroy: function () {
    window.removeEventListener('keyup', this.keyup)
  }
}
</script>

<style scoped lang="scss">

$title-height: 41px;
$button-height: 50px;

.title {
  padding: 5px 15px;
  font-size: 16pt;
  box-shadow: 0 5px 5px -5px rgba(0,0,0,0.2);
  height: $title-height;
}

.sidebar {
  width: 100%;
  overflow-y: auto;
  height: 100%;
}

.main-panel {
  height: calc(100% - #{$title-height} - #{$button-height});
  overflow-y: auto;
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
  text-align: center;
  height: $button-height;
}

.icd-10-desc {
  white-space: pre-wrap;
}

.add-synonym-table {
  @extend .detail-panel;
  tbody > tr {
    box-shadow: 0 5px 5px -5px rgba(0,0,0,0.2);

    td:first-child {
      width: 100px;
    }

    > td {

      &:first-child {
        width: 100px;
      }

      padding: 10px 15px;
      vertical-align: top;
      color: $text;

      &.fit-content {
        display: inline-block;
        max-height: 150px;
        overflow-y: auto;
      }
    }
  }
}
</style>
