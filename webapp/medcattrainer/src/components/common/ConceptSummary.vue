<template>
  <div class="sidebar">
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
        <td @keyup.stop>
          <span v-if="!pickAltConcept">{{conceptSummary['Concept ID']}}</span>
          <v-select class="picker" v-if="pickAltConcept" v-model="selectedCUI" label="name" @search="searchCUI" :options="searchResults"></v-select>
          <font-awesome-icon class="edit" v-if="!pickAltConcept" icon="edit" @click="pickAltConcept = true"></font-awesome-icon>
          <font-awesome-icon class="cancel" v-if="pickAltConcept" icon="times-circle" @click="cancelReassign"></font-awesome-icon>
        </td>
      </tr>
      <tr v-for="taskKey of Object.keys(this.selectedEnt ? this.selectedEnt.assignedValues : {})">
        <td>{{taskKey}}</td>
        <td>{{conceptSummary[taskKey] || 'n/a'}}</td>
      </tr>
      </tbody>

    </table>
  </div>
</template>

<script>
import vSelect from 'vue-select'

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
  components: {
    vSelect,
  },
  props: {
    selectedEnt: Object,
    tasks: Array
  },
  data: function() {
    return {
      conceptSummary: {},
      priorSummary: null,
      pickAltConcept: false,
      searchResults: [],
      selectedCUI: null,
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
          this.conceptSummary[k] =  ent[k]
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
    selectedCorrectCUI: function(item) {
      if (item) {
        let payload = {'label': item.cui};
        this.$http.put(`/entities/${this.selectedEnt.entity}`, payload).then(resp => {
          this.fetchDetail();
        })
      }
    },
    cancelReassign: function() {
      this.pickAltConcept = false;
      this.searchResults = [];
      this.selectedCUI = null;
    }
  },
  mounted: function() {
    this.fetchDetail();
  },
  watch: {
    'selectedEnt': 'fetchDetail',
    'selectedCUI': 'selectedCorrectCUI'
  }
}
</script>

<style scoped lang="scss">
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

.picker {
   width: calc(100% - 30px);
  display: inline-block;
}
.editing {
  opacity: 0.9;
}

.ent-name {
  padding: 10px;
  font-size: 22px;
}

.sidebar {
  flex: 0 0 300px;
  overflow: auto;
  background: $background;
  color: $text;
}

.concept-detail-table {
  tbody > tr {

    > td {
      border-top: 1px solid $borders;
      padding: 10px 15px;
      vertical-align: top;
    }
  }
}
</style>
