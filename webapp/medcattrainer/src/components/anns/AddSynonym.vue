<template>
  <div>
    <div class="main-panel">
      <h4 class="title">Add Synonym</h4>
      <div class="sidebar">
        <table class="add-synonym-table">
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
            <td class="context">{{this.prevText}}<span class="highlight">{{this.name}}</span>{{this.nextText}}</td>
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
    selection: Object,
    projectId: String,
  },
  data: function() {
    return {
      name: this.selection.selStr,
      prevText: this.selection.prevText,
      nextText: this.selection.nextText,
      CUI: '',
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
      this.$http.get(`/search-concepts?search=${term}&projectId=${this.projectId}`)
        .then(resp => {
        loading(false);
        this.searchResults = resp.data.results.map(r => {
          return {
            name: r.pretty_name,
            cui: r.cui,
            desc: r.desc,
            synonyms: _.replace(r.synonyms, new RegExp(',', 'g'), ', ')
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
        context: `${this.selection.priorText}${this.selection.selStr}${this.selection.nextText}`,
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
  text-align: center;
}

.add-synonym-table {
  tbody > tr {
    box-shadow: 0 5px 5px -5px rgba(0,0,0,0.2);

    > td {
      //border-top: 1px solid $borders;
      padding: 10px 15px;
      vertical-align: top;
      color: $text;
    }
  }
}
</style>
