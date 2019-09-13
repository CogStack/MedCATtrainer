<template>
  <div class="border-left border-bottom sidebar">
    <h4 class="title">Concept Summary</h4>
    <div class="ent-name">{{selectedEnt !== null ? selectedEnt.value : ''}}</div>
    <table class="table table-hover">
      <tbody>
      <tr v-for="nameValue of conceptSummary">
        <td>{{nameValue[0]}}</td>
        <td v-if="nameValue[0] === 'Description'" v-html="nameValue[1] === 'nan' ? 'n/a' : nameValue[1] || 'n/a'"></td>
        <td v-if="nameValue[0] !== 'Description'">{{nameValue[1] || 'n/a'}}</td>
      </tr>
      </tbody>
    </table>
  </div>
</template>

<script>

const HIDDEN_PROPS = [
  'value', 'project', 'document', 'start_ind', 'end_ind',
  'entity', 'assignedValues', 'correct', 'id', 'user',
];

const PROP_MAP = {
  'acc': 'Accuracy',
  'desc': 'Description',
  'tui': 'Term ID',
  'cui': 'Concept ID',
  'pretty_name': 'Name'
};

const CONST_PROPS_ORDER = [
  'Name', 'Description', 'Term ID', 'Concept ID',
];

export default {
  name: 'ConceptSummary',
  props: {
    selectedEnt: Object,
    tasks: Array
  },
  data: function() {
    return {
      conceptSummary: []
    }
  },
  methods: {
    cleanProps: function() {
      this.conceptSummary = [];
      if (this.selectedEnt !== null) {
        // remove props
        let ent = Object.keys(this.selectedEnt)
          .filter(k => !HIDDEN_PROPS.includes(k))
          .reduce((obj, key) => {
            obj[key] = this.selectedEnt[key];
            return obj;
          }, {});

        //flatten task vals
        for (const [k, v] of Object.entries(this.selectedEnt.assignedValues)) {
          ent[k] = v || 'n/a';
        }

        //pretty print props:
        for (const [prop, name] of Object.entries(PROP_MAP)) {
          if (ent[prop])
            ent[name] = ent[prop];
            delete ent[prop]
        }

        //order the keys to tuples.
        let props = CONST_PROPS_ORDER.concat(Object.keys(this.selectedEnt.assignedValues));
        for (let k of props) {
          this.conceptSummary.push([k, ent[k]])
        }
      }
    },
    fetchDetail: function() {
      if (this.selectedEnt !== null) {
        this.$http.get(`/entities/${this.selectedEnt.entity}/`).then(resp => {
          this.selectedEnt.cui = resp.data.label;
          this.$http.get(`/concepts?cui=${this.selectedEnt.cui}`).then(resp => {
            this.selectedEnt.desc = resp.data.results[0].desc;
            this.selectedEnt.tui = resp.data.results[0].tui;
            this.selectedEnt.pretty_name = resp.data.results[0].pretty_name;
            this.cleanProps()
          })
        })
      }
    },
  },
  mounted: function() {
    this.fetchDetail();
  },
  watch: {
    'selectedEnt': 'fetchDetail'
  }
}
</script>

<style scoped lang="scss">
.title {
  padding: 5px;
}

.ent-name {
  padding: 10px;
  font-size: 22px;
}

.sidebar {
  flex: 0 0 300px;
  overflow: auto;
}
</style>
