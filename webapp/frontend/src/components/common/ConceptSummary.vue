<template>
  <div class="sidebar">
    <div class="title">Concept Summary</div>
    <div class="summary">
      <table class="concept-detail-table">
        <tbody>
        <tr>
          <td>Annotated Text</td>
          <td class="ent-name">{{selectedEnt !== null ? selectedEnt.value : 'n/a'}}</td>
        </tr>
        <tr>
          <td>Name</td>
          <td>{{conceptSummary['Name'] || 'n/a'}}</td>
        </tr>
        <tr>
          <td>Term ID</td>
          <td>{{conceptSummary['Term ID'] || 'n/a'}}</td>
        </tr>
        <tr>
          <td>Semantic Type</td>
          <td>{{conceptSummary['Type']  || 'n/a'}}</td>
        </tr>
        <tr>
          <td>Concept ID</td>
          <td><span v-if="!altSearch">{{conceptSummary['Concept ID'] || 'n/a'}}</span>
            <span v-if="altSearch" class="alt-concept-picker" @keyup.stop>
              <v-select class="picker" v-model="selectedCUI"
                        label="name" @search="searchCUI" :options="searchResults"
                        :inputId="'pickerID'"></v-select>
              <font-awesome-icon class="cancel" v-if="altSearch" icon="times-circle" @click="cancelReassign"></font-awesome-icon>
            </span>
          </td>
        </tr>
        <tr>
          <td>Accuracy</td>
          <td >{{conceptSummary['Accuracy'] ?  conceptSummary['Accuracy'].toFixed(2) : 'n/a'}}</td>
        </tr>
        <tr v-for="(taskKey, index) of Object.keys(selectedEnt && selectedEnt.length ? selectedEnt.assignedValues : {})" :key="index">
          <td>{{taskKey}}</td>
          <td>{{conceptSummary[taskKey] || 'n/a'}}</td>
        </tr>
        <tr>
          <td>Description</td>
          <td v-html="conceptSummary.Description === 'nan' ? 'n/a' : conceptSummary.Description || 'n/a'"></td>
        </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
import vSelect from 'vue-select'

const HIDDEN_PROPS = [
  'value', 'project', 'document', 'start_ind', 'end_ind',
  'entity', 'assignedValues', 'id', 'user', 'deleted'
]

const PROP_MAP = {
  'acc': 'Accuracy',
  'desc': 'Description',
  'tui': 'Term ID',
  'semantic_type': 'Type',
  'cui': 'Concept ID',
  'pretty_name': 'Name'
}

const CONST_PROPS_ORDER = [
  'Name', 'Description', 'Type', 'Term ID', 'Concept ID', 'Accuracy'
]

export default {
  name: 'ConceptSummary',
  components: {
    vSelect
  },
  props: {
    projectTUIs: String,
    selectedEnt: {
      type: Object,
      default: function () {
        return {}
      }
    },
    altSearch: Boolean
  },
  data: function () {
    return {
      conceptSummary: {},
      searchResults: [],
      selectedCUI: null
    }
  },
  methods: {
    cleanProps: function () {
      this.conceptSummary = {}
      if (this.selectedEnt && Object.keys(this.selectedEnt).length) {
        // remove props
        let ent = Object.keys(this.selectedEnt)
          .filter(k => !HIDDEN_PROPS.includes(k))
          .reduce((obj, key) => {
            obj[key] = this.selectedEnt[key]
            return obj
          }, {})

        // flatten task vals
        for (const [k, v] of Object.entries(this.selectedEnt.assignedValues)) {
          ent[k] = v || 'n/a'
        }

        // pretty print props:
        for (const [prop, name] of Object.entries(PROP_MAP)) {
          if (ent[prop]) { ent[name] = ent[prop] }
          delete ent[prop]
        }

        // order the keys to tuples.
        let props = CONST_PROPS_ORDER.concat(Object.keys(this.selectedEnt.assignedValues))
        for (let k of props) {
          this.conceptSummary[k] = ent[k]
        }
      }
    },
    fetchDetail: function () {
      if (this.selectedEnt && Object.keys(this.selectedEnt).length) {
        this.$http.get(`/api/entities/${this.selectedEnt.entity}/`).then(resp => {
          this.selectedEnt.cui = resp.data.label
          this.$http.get(`/api/concepts/?cui=${this.selectedEnt.cui}`).then(resp => {
            this.selectedEnt.desc = resp.data.results[0].desc
            this.selectedEnt.tui = resp.data.results[0].tui
            this.selectedEnt.pretty_name = resp.data.results[0].pretty_name
            this.selectedEnt.semantic_type = resp.data.results[0].semantic_type
            this.cleanProps()
          })
        })
      } else {
        this.conceptSummary = {}
      }
    },
    searchCUI: _.debounce(function (term, loading) {
      loading(true)
      this.$http.get(`/api/search-concepts/?search=${term}&tui__in=${this.projectTUIs}`)
        .then(resp => {
          loading(false)
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
    selectedCorrectCUI: function (item) {
      if (item) {
        this.$emit('select:altConcept', item)
        this.searchResults = []
        this.selectedCUI = null
      }
    },
    cancelReassign: function () {
      this.$emit('select:alternative', false)
      this.searchResults = []
      this.selectedCUI = null
    }
  },
  mounted: function () {
    this.fetchDetail()
  },
  watch: {
    'selectedEnt': {
      handler: 'fetchDetail',
      deep: true
    },
    'selectedCUI': 'selectedCorrectCUI'
  }
}
</script>

<style scoped lang="scss">
.title {
  padding: 5px 15px;
  font-size: 16pt;
  box-shadow: 0 5px 5px -5px rgba(0,0,0,0.2);
  color: black;
}

.summary {
  height: calc(100% - 41px);
  width: 400px;
  overflow: auto
}

.ent-name {
  padding: 10px;
  font-size: 12pt;
  box-shadow: 0 5px 5px -5px rgba(0,0,0,0.2);
}

.sidebar {
  flex: 0 0 300px;
  overflow: auto;
  background: $background;
  color: $text;
}

.concept-detail-table {
  width: 100%;
  tbody > tr {
    box-shadow: 0 5px 5px -5px rgba(0,0,0,0.2);

    > td {
      padding: 10px 15px;
      vertical-align: top;
    }
  }
}

.picker {
  width: calc(100% - 30px);
  display: inline-block;
}

.cui-btns {
  opacity: 0.7;
  float: right;
  position: relative;

  &:hover {
    opacity: 0.9;
    cursor: pointer;
  }
}

.edit {
  @extend .cui-btns;
  top: 7px;
}

.cancel {
  @extend .cui-btns;
  top: 10px;
}
</style>
