<template>
  <div class="border border-left border-bottom">
    <div class="main-panel">
      <h4 class="title">Add Concept Synonym</h4>
      <div class="sidebar">
        <table class="table">
          <tbody>
          <tr>
            <td>New Synonym</td>
            <td>{{name}}</td>
          </tr>
          <tr>
            <td>Concept Lookup</td>
            <td>
              <v-select v-model="selectedCUI" label="name" @search="searchCUI" :options="searchResults"></v-select>
            </td>
          </tr>
          <tr>
            <td>Context</td>
            <td>{{context}}</td>
          </tr>
          <tr>
            <td>Synonyms</td>
            <td>{{synonyms || 'n/a'}}</td>
          </tr>
          </tbody>
        </table>
      </div>
    </div>
    <div class="action-buttons">
      <button @click="submit()" class="btn btn-primary">
        <font-awesome-icon icon="plus"></font-awesome-icon>
        Add Synonym
      </button>
      <button @click="cancel()" class="btn btn-danger">
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
    vSelect,
  },
  props: {
    selection: Object
  },
  data: function() {
    return {
      name: this.selection.selStr,
      CUI: '',
      context: `${this.selection.priorText}${this.selection.selStr}${this.selection.nextText}`,
      synonyms: null,
      searchResults: [],
      selectedCUI: null,
    }
  },
  watch: {
    'selectedCUI': 'selectedSynonymCUI'
  },
  methods: {
    searchCUI: _.debounce(function(term, loading) {
      loading(true);
      this.$http.get(`/search-concepts?search=${term}`).then(resp => {
        loading(false);
        this.searchResults = resp.data.results.map(r => {
          return {
            name: r.pretty_name,
            cui: r.cui,
            desc: r.desc,
            synonyms: r.synonyms,
          }
        })
      })
    }, 400),
    selectedSynonymCUI: function(item) {
      this.cui = item.cui;
      this.tui = item.tui;
      this.synonyms = item.synonyms;
      this.searchResults = [];
    },
    submit: function() {
      const payload = {
        name: this.name,
        cui: this.cui,
        tui: this.tui,
        context: this.context
      };
      this.$http.post('', payload).then(resp => {
        this.$emit('request:addSynonymComplete')
      })
    },
    cancel: function() {
      this.$emit('request:addSynonymComplete')
    }
  }
}
</script>

<style scoped lang="scss">
.title {
  padding: 5px;
}

.main-panel {
  height: calc(100% - 50px);
}

.sidebar {
  width: 100%;
  overflow: auto;
}

.action-buttons {
  height: 50px;
  text-align: center;
}
</style>
