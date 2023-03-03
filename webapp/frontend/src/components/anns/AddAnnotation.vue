<template>
  <div class="sidebar" @keyup.stop>
    <div class="title">
      Add Term
      <button @click="cancel()" class="btn btn-default close-window" @mousedown.stop>
        <font-awesome-icon icon="times"></font-awesome-icon>
      </button>
    </div>
    <div class="main-panel">
      <table class="add-synonym-table">
        <tbody>
        <tr>
          <td>New Term</td>
          <td class="fit-content">{{name}}</td>
        </tr>
        <tr @keyup.stop>
          <td>Concept Lookup</td>
          <td>
            <concept-picker :project="project" :selection="name" @pickedResult:concept="enrichCUI"
                            @picker:opened="conceptPickerState(true)" @picker:closed="conceptPickerState(false)">
            </concept-picker>
          </td>
        </tr>
        <tr>
          <td>Context</td>
          <td class="fit-content context">
            <span class="context">{{this.prevText}}</span>
            <span class="context highlight">{{this.name}}</span>
            <span class="context">{{this.nextText.slice(0, 15)}}</span>
          </td>
        </tr>
        </tbody>
      </table>
      <table class="add-synonym-table" v-if="selectedCUI">
        <tbody>
        <tr>
          <td>Name</td>
          <td class="cui-mappings">{{selectedCUI.name.split(':')[0] || 'n/a'}}</td>
        </tr>
        <tr v-if="selectedCUI.type_ids !== 'unk' ">
          <td>Type ID</td>
          <td>{{(selectedCUI.type_ids || []).join(', ') || 'n/a'}}</td>
        </tr>
        <tr v-if="selectedCUI.semantic_type">
          <td>Semantic Type</td>
          <td>{{selectedCUI.semantic_type || 'n/a'}}</td>
        </tr>
        <tr>
          <td>Concept ID</td>
          <td >{{selectedCUI.cui || 'n/a'}}</td>
        </tr>
        <tr v-if="(selectedCUI.icd10 || []).length > 0">
          <td>ICD-10</td>
          <td class="fit-content">
            <div v-for="code of selectedCUI.icd10" :key="code.code">{{`${code.code} | ${code.desc}`}}</div>
          </td>
        </tr>
        <tr v-if="(selectedCUI.opcs4 || []).length > 0">
          <td>OPCS-4</td>
          <td class="fit-content">
            <div v-for="code of selectedCUI.opcs4" :key="code.code">{{`${code.code} | ${code.desc}`}}</div>
          </td>
        </tr>
        <tr>
          <td>Description</td>
          <td class="fit-content" v-html="selectedCUI.desc === 'nan' ? 'n/a' : selectedCUI.desc || 'n/a'"></td>
        </tr>
        <tr>
          <td>Synonyms</td>
          <td class="fit-content" v-html="(selectedCUI.synonyms || []).join('<br>') || 'n/a'"></td>
        </tr>
        </tbody>
      </table>
    </div>
    <div v-if="selectedCUI !== null" class="action-buttons">
      <button @click="submit()" class="btn task-btn-0">
        <font-awesome-icon icon="plus"></font-awesome-icon>
        Add Term
      </button>
      <button @click="cancel()" class="btn task-btn-1">
        <font-awesome-icon icon="times"></font-awesome-icon>
        Cancel
      </button>
    </div>
    <add-new-concept class="add-new-concept" v-if="project.add_new_entities" :selection="selection" :project="project" :documentId="documentId"
                     @select:newConcept="newConceptSelected"
                     @request:addConceptComplete="newConceptAddedComplete"></add-new-concept>
  </div>
</template>

<script>
import ConceptDetailService from '@/mixins/ConceptDetailService.js'
import ConceptPicker from '@/components/common/ConceptPicker'
import AddNewConcept from '@/components/common/AddNewConcept'

export default {
  name: 'AddAnnotation',
  components: {
    AddNewConcept,
    ConceptPicker
  },
  mixins: [ConceptDetailService],
  props: {
    selection: Object,
    project: Object,
    documentId: Number,
    searchFilterDBIndex: String
  },
  data () {
    return {
      name: this.selection.selStr,
      prevText: this.selection.prevText,
      nextText: this.selection.nextText,
      selectedCUI: null,
      conceptPickerOpen: false
    }
  },
  methods: {
    enrichCUI (concept) {
      this.selectedCUI = concept
      if (this.selectedCUI.icd10 || this.selectedCUI.opcs4) {
        this.fetchConcept(this.selectedCUI, this.searchFilterDBIndex, () => {
          if (concept.icdCode) {
            this.selectedCUI.icd10 = this.selectedCUI.icd10.filter(i => i.id === concept.icdCode)
          } else if (concept.opcsCode) {
            this.selectedCUI.opcs4 = this.selectedCUI.opcs4.filter(i => i.id === concept.opcsCode)
          }
        })
      }
    },
    submit () {
      const payload = {
        source_value: this.selection.selStr,
        document_id: this.documentId,
        project_id: this.project.id,
        selection_occur_idx: this.selection.selectionOccurrenceIdx,
        cui: this.selectedCUI.cui
      }
      if (this.selectedCUI.icd10 && this.selectedCUI.icd10.length === 1) {
        payload.icd_code = this.selectedCUI.icd10[0].id
      } else if (this.selectedCUI.opcs4 && this.selectedCUI.opcs4.length === 1) {
        payload.opcs_code = this.selectedCUI.opcs4[0].id
      }

      this.$http.post('/api/add-annotation/', payload).then(resp => {
        this.$emit('request:addAnnotationComplete', resp.data.id)
        this.selectedCUI = null
      })
    },
    cancel () {
      this.$emit('request:addAnnotationComplete')
    },
    keyup (e) {
      if (e.keyCode === 27) { // esc key
        this.cancel()
      } else if (e.keyCode === 13 && !this.conceptPickerOpen) { // enter key
        this.submit()
      }
    },
    conceptPickerState (val) {
      const that = this
      window.setTimeout(function () {
        that.conceptPickerOpen = val
      }, 50)
    },
    newConceptSelected () {
      this.selectedCUI = null
    },
    newConceptAddedComplete (annoId) {
      this.$emit('request:addAnnotationComplete', annoId)
    }
  },
  mounted () {
    window.addEventListener('keyup', this.keyup)
  },
  beforeDestroy () {
    window.removeEventListener('keyup', this.keyup)
  }
}
</script>

<style scoped lang="scss">
$button-height: 50px;

.sidebar {
  width: 100%;
  overflow-y: auto;
  height: 100%;
}

.main-panel {
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
  padding-top: 10px;
  height: $button-height;
}

.cui-mappings {
  white-space: pre-wrap;
}

.close-window {
  opacity: 0.5;
  float: right;
  &:hover {
    opacity: 1.0;
  }
}

.add-synonym-table {
  width: 100%;

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
        width: 100%;
      }
    }
  }
}

.add-new-concept {
  padding: 5px 0;
}
</style>
