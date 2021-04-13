<template>
  <div class="sidebar">
    <div class="title">Concept Summary</div>
    <div class="summary">
      <table class="concept-detail-table">
        <tbody>
        <tr>
          <td>Annotated Text</td>
          <td class="fit-content ent-name">{{selectedEnt !== null ? selectedEnt.value : 'n/a'}}</td>
        </tr>
        <tr>
          <td>Name</td>
          <td>
            <span v-if="!altSearch">{{conceptSummary['Name'] || 'n/a'}}</span>
            <span v-if="altSearch" class="alt-concept-picker" @keyup.stop>
              <concept-picker :project="project"  @pickedResult:concept="selectedCorrectCUI"></concept-picker>
              <font-awesome-icon class="cancel" icon="times-circle" @click="cancelReassign"></font-awesome-icon>
            </span>
          </td>
        </tr>
        <tr v-if="conceptSummary['Term ID'] !== 'unk' ">
          <td>Term ID</td>
          <td>{{conceptSummary['Term ID'] || 'n/a'}}</td>
        </tr>
        <tr v-if="conceptSummary['Semantic Type']">
          <td>Semantic Type</td>
          <td>{{conceptSummary['Type']  || 'n/a'}}</td>
        </tr>
        <tr>
          <td>Concept ID</td>
          <td>{{conceptSummary['Concept ID'] || 'n/a'}}</td>
        </tr>
        <tr v-if="(conceptSummary['ICD-10'] || []).length > 0">
          <td>ICD-10</td>
          <td class="fit-content">
            <div class="selectable-code" @click="selectICDCode(code)"
                 v-for="code of conceptSummary['ICD-10']" :key="code.code">
              <font-awesome-icon v-if="selectedEnt.icd_code === code.id" icon="check" class="selected-code"></font-awesome-icon>
              {{`${code.code} | ${code.desc}`}}
            </div>
          </td>
        </tr>
        <tr v-if="(conceptSummary['OPCS-4'] || []).length > 0">
          <td>OPCS-4</td>
          <td class="fit-content">
            <div v-for="code of conceptSummary['OPCS-4']" :key="code.code">{{`${code.code} | ${code.desc}`}}</div>
          </td>
        </tr>
        <tr>
          <td>Accuracy</td>
          <td>{{conceptSummary['Accuracy'] ?  conceptSummary['Accuracy'].toFixed(2) : 'n/a'}}</td>
        </tr>
        <tr v-for="(taskKey, index) of Object.keys(selectedEnt && selectedEnt.length ? selectedEnt.assignedValues : {})" :key="index">
          <td>{{taskKey}}</td>
          <td>{{conceptSummary[taskKey] || 'n/a'}}</td>
        </tr>
        <tr>
          <td>Description</td>
          <td class="fit-content" v-html="conceptSummary.Description === 'nan' ? 'n/a' : conceptSummary.Description || 'n/a'"></td>
        </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
import ConceptDetailService from '@/mixins/ConceptDetailService.js'
import ConceptPicker from '@/components/common/ConceptPicker'

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
  'icd10': 'ICD-10',
  'opcs4': 'OPCS-4',
  'pretty_name': 'Name'
}

const CONST_PROPS_ORDER = [
  'Name', 'Description', 'Type', 'Term ID', 'Concept ID', 'ICD-10', 'OPCS-4', 'Accuracy'
]

export default {
  name: 'ConceptSummary',
  components: {
    ConceptPicker
  },
  props: {
    project: Object,
    selectedEnt: {
      type: Object,
      default () {
        return {}
      }
    },
    altSearch: Boolean
  },
  mixins: [ConceptDetailService],
  data () {
    return {
      conceptSummary: {},
      searchResults: [],
      selectedCUI: null
    }
  },
  methods: {
    cleanProps () {
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

        // show ICD and OPCS lists with special settings for selected ICD/OPCS codes.
      }
    },
    selectedCorrectCUI (item) {
      if (item) {
        this.$emit('select:altConcept', item)
        this.searchResults = []
        this.selectedCUI = null
      }
    },
    cancelReassign () {
      this.$emit('select:alternative', false)
      this.searchResults = []
      this.selectedCUI = null
    },
    keyup (e) {
      if (this.altSearch && e.keyCode === 27) {
        this.cancelReassign()
      }
    },
    selectICDCode (item) {
      this.$emit('select:ICD', item)
    },
    selectOPCSCode (item) {
      this.$emit('select:OPCS', item)
    }
  },
  mounted () {
    const that = this
    this.fetchDetail(this.selectedEnt, () => {
      that.cleanProps()
    })
    window.addEventListener('keyup', this.keyup)
  },
  beforeDestroy () {
    window.removeEventListener('keyup', this.keyup)
  },
  watch: {
    'selectedEnt': {
      handler (newVal) {
        const that = this
        that.fetchDetail(newVal, () => {
          that.cleanProps()
        })
      },
      deep: true
    }
  }
}
</script>

<style scoped lang="scss">
.summary {
  height: calc(100% - 41px);
  overflow-y: auto;
}

.ent-name {
  padding: 10px;
  font-size: 12pt;
}

.sidebar {
  background: $background;
  color: $text;
}

.cui-mappings {
  white-space: pre-wrap;
}

.concept-detail-table {
  width: 100%;
  tbody > tr {
    box-shadow: 0 5px 5px -5px rgba(0,0,0,0.2);

    > td {
      padding: 10px 15px;
      vertical-align: top;

      &:first-child {
        width: 150px;
      }

      &.fit-content {
        display: inline-block;
        max-height: 250px;
        overflow-y: auto;
        width: 100%;
      }
    }
  }
}

.picker {
  width: calc(100% - 30px);
  display: inline-block;
}

.select-option {
  white-space: pre-wrap;
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

.selectable-code {
  padding: 2px 3px;

  &:hover {
    cursor: pointer;
    background-color: $color-2;
  }
}

.selected-code {
  float: right;
  color: $success
}
</style>
