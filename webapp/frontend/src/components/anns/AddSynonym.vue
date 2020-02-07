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
            <concept-picker :project="project" :selection="name" @pickedResult:concept="enrichCUI">
            </concept-picker>
          </td>
        </tr>
        <tr>
          <td>Context</td>
          <td class="fit-content context">{{this.prevText}}
            <span class="highlight">{{this.name}}</span>
            {{this.nextText.slice(0, 15)}}
          </td>
        </tr>
        </tbody>
      </table>
      <div class="spacer" v-if="!selectedCUI"></div>
      <table class="add-synonym-table" v-if="selectedCUI">
        <tbody>
        <tr>
          <td>Name</td>
          <td class="cui-mappings">{{selectedCUI.name.split(':')[0] || 'n/a'}}</td>
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
          <td class="cui-mappings">{{selectedCUI.icd10}}</td>
        </tr>
        <tr v-if="selectedCUI.opcs4">
          <td>OPCS-4</td>
          <td class="cui-mappings">{{selectedCUI.opcs4}}</td>
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
import ConceptDetailService from '@/mixins/ConceptDetailService.js'
import ConceptPicker from '@/components/common/ConceptPicker'

export default {
  name: 'AddSynoym',
  components: {
    ConceptPicker
  },
  mixins: [ConceptDetailService],
  props: {
    selection: Object,
    project: Object,
    documentId: Number
  },
  data () {
    return {
      name: this.selection.selStr,
      prevText: this.selection.prevText,
      nextText: this.selection.nextText,
      selectedCUI: null
    }
  },
  created () {
    window.setTimeout(function () {
      // that.selStr = that.selection.selStr
    }, 50)
  },
  methods: {
    enrichCUI (concept) {
      this.selectedCUI = concept
      if (this.selectedCUI.icd10 || this.selectedCUI.opcs4) {
        this.fetchConcept(this.selectedCUI)
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
      this.$http.post('/api/add-annotation/', payload).then(resp => {
        this.$emit('request:addAnnotationComplete', resp.data.id)
        this.selectedCUI = null
      })
    },
    cancel () {
      this.$emit('request:addAnnotationComplete')
    },
    keyup (e) {
      if (e.keyCode === 27) {
        this.cancel()
      }
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

.spacer {
  width: 100%;
  height: 350px;
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
  paddind-top: 10px;
  height: $button-height;
}

.cui-mappings {
  white-space: pre-wrap;
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
      }
    }
  }
}
</style>
