<template>
  <div class="summary">
    <loading-overlay class="loading-height" :loading="loading"></loading-overlay>
    <div v-if="!loading">
      <h3>Diagnosis - Primary:</h3>
      <coding-summary-table :concepts="primaryDiag"
                            :rightContext="rightContext"
                            :leftContext="leftContext"
                            :highlightClass="highlightClass"
                            :codeType="'icd'"
                            @select:concept="selectConcept"></coding-summary-table>
      <h3>Diagnosis - Secondary:</h3>
      <coding-summary-table :concepts="secondaryDiag"
                            :rightContext="rightContext"
                            :leftContext="leftContext"
                            :highlightClass="highlightClass"
                            :codeType="'icd'"
                            @select:concept="selectConcept"></coding-summary-table>
      <h3>Procedures - Primary:</h3>
      <coding-summary-table :concepts="primaryProc"
                            :rightContext="rightContext"
                            :leftContext="leftContext"
                            :highlightClass="highlightClass"
                            :codeType="'opcs'"
                            @select:concept="selectConcept"></coding-summary-table>
      <h3>Procedures - Secondary:</h3>
      <coding-summary-table :concepts="secondaryProc"
                            :rightContext="rightContext"
                            :leftContext="leftContext"
                            :highlightClass="highlightClass"
                            :codeType="'opcs'"
                            @select:concept="selectConcept"></coding-summary-table>
    </div>
  </div>
</template>

<script>
import SummaryMixin from '@/mixins/SummaryMixin.js'
import CodingSummaryTable from '@/components/cc/CodingSummaryTable.vue'
import LoadingOverlay from '@/components/common/LoadingOverlay.vue'

const PRIORITY_TASK_NAME = 'Priority'
const PRIMARY = 'Primary'
const SECONDARY = 'Secondary'

const ICD_ANN_PROP = 'icd_code'
const OPCS_ANN_PROP = 'opcs_code'

export default {
  name: 'CodingAnnotationSummary',
  components: { LoadingOverlay, CodingSummaryTable },
  mixins: [SummaryMixin],
  props: {
    annos: Array
  },
  computed: {
    corrAnnos () {
      return this.annos.filter(a => a.validated && (a.correct || a.alternative))
    }
  },
  created () {
    this.loading = true
    this.enrichSummary(this.corrAnnos, this.receivedAllMetaAnnotations)
  },
  data () {
    return {
      loading: null,
      primaryDiag: [],
      secondaryDiag: [],
      primaryProc: [],
      secondaryProc: []
    }
  },
  methods: {
    receivedAllMetaAnnotations () {
      this.primaryDiag = this.filterConcepts(PRIORITY_TASK_NAME, PRIMARY, ICD_ANN_PROP)
      this.secondaryDiag = this.filterConcepts(PRIORITY_TASK_NAME, SECONDARY, ICD_ANN_PROP)
      this.primaryProc = this.filterConcepts(PRIORITY_TASK_NAME, PRIMARY, OPCS_ANN_PROP)
      this.secondaryProc = this.filterConcepts(PRIORITY_TASK_NAME, SECONDARY, OPCS_ANN_PROP)
      this.loading = false
    },
    filterConcepts (taskName, taskValue, codeProp) {
      if (this.metaAnnos.length === 0 || !this.tasks.length || this.tasks.length === 0) {
        return []
      }
      let codedConcepts = this.corrAnnos.filter(i => i[codeProp])
      let task = this.tasks.filter(t => t.name === taskName)[0]
      let optionValueId = task.options.filter(o => o.name === taskValue)[0].id
      let concepts = []
      let codedConceptIds = codedConcepts.map(c => c.id)
      for (let [key, val] of Object.entries(this.metaAnnos)) {
        let codeIdx = codedConceptIds.indexOf(Number(key))
        if (codeIdx !== -1) {
          let vals = val.filter(v => v.name === taskName)
          if (vals[0] && vals[0].value === optionValueId) {
            concepts.push(codedConcepts[codeIdx])
          }
        }
      }
      return concepts
    }
  }
}
</script>

<style scoped lang="scss">
.summary {
  height: 700px;
  overflow-y: auto;
}
</style>
