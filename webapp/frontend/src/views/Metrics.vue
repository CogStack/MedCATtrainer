<template>
  <div class="metrics-view">
    <div class="metrics-header">
      <h2>Project Metrics: {{(projectIds && projectIds.join(',')) || $route.query.projectIds}}</h2>
    </div>
    <div class="viewport-full-height">
      <loading-overlay :loading="loading">
        <span>Calculating Metrics...</span>
      </loading-overlay>
      <tabs class="viewport">
        <tab name="User Stats" class="user-stats">
          <b-table striped hover small :items="userStats.items" :fields="userStats.fields"></b-table>
        </tab>
        <tab name="Annotations" class="anno-summary">
          <b-table striped hover small :items="annoSummary.items" :fields="annoSummary.fields"></b-table>
        </tab>
        <tab name="Concept Summary" class="concept-summary">
          <b-table striped hover small :items="conceptSummary.items" :fields="conceptSummary.fields">
            <template #cell(cui_f1)="data">
              <div v-html="data.value"></div>
            </template>
            <template #cell(cui_rec)="data">
              <div v-html="data.value"></div>
            </template>
            <template #cell(cui_prec)="data">
              <div v-html="data.value"></div>
            </template>
            <template #cell(tps)="data">
              <button  class="btn btn-outline-success" @click="openExamples('tp_examples', data.item)">
                {{data.item.tps}}
              </button>
            </template>
            <template #cell(fns)="data">
              <button class="btn btn-outline-warning" @click="openExamples('fn_examples', data.item)">
                {{data.item.fns}}
              </button>
            </template>
            <template #cell(fps)="data">
              <button class="btn btn-outline-danger" @click="openExamples('fp_examples', data.item)">
                {{data.item.fps}}
              </button>
            </template>
          </b-table>
        </tab>
        <tab v-if="metaAnnsSummary.items" name="Meta Anns">
          <b-table striped hover small :items="metaAnnsSummary.items" :fields="metaAnnsSummary.fields" class="meta-anno-summary"></b-table>
        </tab>
      </tabs>
    </div>
    <modal class="summary-modal" v-if="predictedResults" :closable="true" @modal:close="predictedResults = null">
      <h3 slot="header">{{predictionResultsTitle}}</h3>
      <div slot="body">
        <table class="table table-hover">
          <thead>
            <tr>
              <th>Doc Name</th>
              <th>CUI</th>
              <th>Value</th>
              <th>Accuracy</th>
              <th>Text</th>
            </tr>
          </thead>
          <tbody>
            <anno-result v-for="(res, key) of predictedResults" :key="key" :result="res"></anno-result>
          </tbody>
        </table>
      </div>
    </modal>
  </div>
</template>

<script>
import Modal from '@/components/common/Modal'
import AnnoResult from '@/components/anns/AnnoResult'
import LoadingOverlay from '@/components/common/LoadingOverlay.vue'

export default {
  name: 'Metrics.vue',
  components: { AnnoResult, Modal, LoadingOverlay },
  props: {
    projectIds: Array
  },
  created () {
    if (this.projectIds || (this.$route.query && this.$route.query.projectIds)) {
      this.loading = true
      let ids = this.projectIds ? this.projectIds.join(',') : this.$route.query.projectIds
      this.$http.get(`/api/metrics/?projectIds=${ids}`).then(resp => {
        this.loading = false
        this.$set(this.userStats, 'items', resp.data.results.user_stats)
        this.$set(this.conceptSummary, 'items', resp.data.results.concept_summary)
        this.$set(this.annoSummary, 'items', resp.data.results.annotation_summary)
        this.$set(this.metaAnnsSummary, 'items', resp.data.results.meta_anno_summary)
      })
    }
  },
  data () {
    return {
      loading: false,
      userStats: {
        fields: [
          { key: 'user', label: 'User', sortable: true },
          { key: 'count', label: 'Count', sortable: true }
        ]
      },
      annoSummary: {
        fields: [
          { key: 'project', label: 'Project', sortable: true },
          { key: 'document_name', label: 'Doc. Name', sortable: true },
          { key: 'id', label: 'Annotation Id', sortable: true },
          { key: 'user', label: 'User', sortable: true },
          { key: 'cui', label: 'CUI' },
          { key: 'concept_name', label: 'Concept', sortable: true },
          { key: 'value', label: 'text' }
          // more fields for the validated, killed, correct, incorrect etc.
        ]
      },
      conceptSummary: {
        fields: [
          { key: 'concept_count', label: 'Count', sortable: true },
          { key: 'concept_name', label: 'Concept', sortable: true },
          { key: 'count_variations_ratio', label: 'Variation Ratio', sortable: true },
          { key: 'cui', label: 'CUI' },
          { key: 'cui_f1', label: 'F1', sortable: true, formatter: this.perfFormatter },
          { key: 'cui_prec', label: 'Prec.', sortable: true, formatter: this.perfFormatter },
          { key: 'cui_rec', label: 'Rec.', sortable: true, formatter: this.perfFormatter },
          { key: 'tps', label: 'TPs', sortable: true },
          { key: 'fns', label: 'FNs', sortable: true },
          { key: 'fps', label: 'FPs', sortable: true }
        ]
      },
      metaAnnsSummary: {
        fields: []
      },
      predictedResults: null,
      predictionResultsTitle: null
    }
  },
  methods: {
    openExamples (exampleType, item) {
      if (exampleType === 'tp_examples') {
        this.predictionResultsTitle = 'True Positive Model Predictions'
      } else if (exampleType === 'fp_examples') {
        this.predictionResultsTitle = 'False Positive Model Predictions'
      } else {
        this.predictionResultsTitle = 'False Negative Model Predictions'
      }
      const idx = this.conceptSummary.items.indexOf(item)
      this.predictedResults = this.conceptSummary.items[idx][exampleType]
    },
    perfFormatter (value) {
      let txtColorClass = 'good-perf'
      if (Number(value) < 0.45) {
        txtColorClass = 'bad-perf'
      }
      return `
        <div class="gradient-fill ${txtColorClass}" style="width: calc(${Number(value) * 100}%);">
          ${Number(value).toFixed(3)}
        </div>
`
    }
  }
}
</script>

<style lang="scss">
$metrics-header-height: 42px;

.metrics-view {
  // full-height minus app header height
  height: calc(100% - 60px);
}

.metrics-header {
  padding: 10px;
  height: 42px;
}

.viewport-full-height {
  height: calc(100% - #{$metrics-header-height});
  padding: 10px;
}

.viewport {
  height: 100%;
}

.tabs-component-panels {
  height: calc(100% - 60px);
}

.user-stats {
  overflow-y: auto;
  height: 100%
}

.anno-summary {
  overflow-y: auto;
  height: 100%
}

.concept-summary {
  overflow-y: auto;
  height: 100%
}

.meta-anno-summary {
  overflow-y: auto;
  height: 100%
}

.good-perf {
  color: #E5EBEA;
}

.bad-perf {
  color: #45503B;
}

.gradient-fill {
  height: 28px;
  background-image: linear-gradient(to right, #009639, #E8EDEE);
  border: 1px solid #009639;
  box-shadow: 0 5px 5px -5px #009639;
}
</style>
