<template>
  <div class="sidebar">
    <div class="title">Concept Summary</div>
    <div class="summary">
      <div class="ent-name">
        {{selectedEnt !== null ? selectedEnt.value : ''}}
      </div>
      <table class="concept-detail-table">
        <tbody>
        <tr>
          <td>Name</td>
          <td>{{conceptSummary ? conceptSummary['Name'] : 'n/a'}}</td>
        </tr>
        <tr>
          <td>Description</td>
          <td v-html="conceptSummary.Description === 'nan' ? 'n/a' : conceptSummary.Description || 'n/a'"></td>
        </tr>
        <tr>
          <td>Term ID</td>
          <td>{{conceptSummary ? conceptSummary['Term ID'] : 'n/a'}}</td>
        </tr>
        <tr>
          <td>Concept ID</td>
          <td >{{conceptSummary['Concept ID']}}</td>
        </tr>
        <tr>
          <td>Accuracy</td>
          <td >{{conceptSummary['Accuracy'] ?  conceptSummary['Accuracy'].toFixed(2) : 'n/a'}}</td>
        </tr>
        <tr v-for="(taskKey, index) of Object.keys(this.selectedEnt ? this.selectedEnt.assignedValues : {})" :key="index">
          <td>{{taskKey}}</td>
          <td>{{conceptSummary[taskKey] || 'n/a'}}</td>
        </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
const HIDDEN_PROPS = [
  'value', 'project', 'document', 'start_ind', 'end_ind',
  'entity', 'assignedValues', 'id', 'user', 'deleted'
]

const PROP_MAP = {
  'acc': 'Accuracy',
  'desc': 'Description',
  'tui': 'Term ID',
  'cui': 'Concept ID',
  'pretty_name': 'Name'
}

const CONST_PROPS_ORDER = [
  'Name', 'Description', 'Term ID', 'Concept ID', 'Accuracy'
]

export default {
  name: 'ConceptSummary',
  props: {
    selectedEnt: Object
  },
  data: function () {
    return {
      conceptSummary: {},
      priorSummary: null
    }
  },
  methods: {
    cleanProps: function () {
      this.conceptSummary = []
      if (this.selectedEnt !== null) {
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
      if (this.selectedEnt !== null) {
        this.$http.get(`/api/entities/${this.selectedEnt.entity}/`).then(resp => {
          this.selectedEnt.cui = resp.data.label
          this.$http.get(`/api/concepts/?cui=${this.selectedEnt.cui}`).then(resp => {
            this.selectedEnt.desc = resp.data.results[0].desc
            this.selectedEnt.tui = resp.data.results[0].tui
            this.selectedEnt.pretty_name = resp.data.results[0].pretty_name
            this.cleanProps()
          })
        })
      }
    }
  },
  mounted: function () {
    this.fetchDetail()
  },
  watch: {
    'selectedEnt': 'fetchDetail',
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

</style>
