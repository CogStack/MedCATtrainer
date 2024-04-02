<template>
  <div class="metrics-view">
    <div class="metrics-header">
      <div class="title">Metrics Report:
        <span v-if="!editingName">
          <span v-if="!reportName" class="no-report-name">n/a</span>
          <span v-if="reportName" class="completed-report-name">{{reportName}}</span>
          <font-awesome-icon icon="pencil" class="edit-name-icon" @click="editingName = true"></font-awesome-icon>
        </span>
        <span class="report-name-input" v-if="editingName">
          <b-form-input placeholder="Report name" type="text" v-model="editedReportName"></b-form-input>
        </span>
      </div>

    </div>
    <div class="viewport-full-height">
      <loading-overlay :loading="loading">
        <span slot="message">Loading metrics report...</span>
      </loading-overlay>
      <b-tabs class="viewport">
        <b-tab title="User Stats" class="user-stats">
          <b-table striped hover small :items="userStats.items" :fields="userStats.fields"></b-table>
        </b-tab>
        <b-tab title="Annotations" class="anno-summary">
          <b-table striped hover small :items="annoSummary.items" :fields="annoSummary.fields">
            <template #cell(status)="data">
              <div id="status" :class="textColorClass(data.item.status)">
                {{data.item.status}}
                <font-awesome-icon icon="check-circle" v-if="['Correct', 'Manually Added', 'Alternative'].includes(data.item.status)"></font-awesome-icon>
                <font-awesome-icon icon="times-circle" v-if="['Incorrect', 'Terminated', 'Irrelevant'].includes(data.item.status)"></font-awesome-icon>
              </div>
            </template>
          </b-table>
        </b-tab>
        <b-tab title="Concept Summary" class="concept-summary">
          <b-table striped hover small :items="conceptSummary.items" :fields="conceptSummary.fields" id="concepts-sum-tbl">
            <template #head(concept)="data">
              <div id="concept-head">Concept</div>
              <b-tooltip target="concept-head"
                         triggers="hover"
                         container="concepts-sum-tbl"
                         title=""></b-tooltip>
            </template>
            <template #head(concept_count)="data">
              <div id="concept-count-head">Concept Count</div>
              <b-tooltip target="concept-count-head"
                         triggers="hover"
                         container="concepts-sum-tbl"
                         title="Number of occurrences across the projects"></b-tooltip>
            </template>
            <template #head(variations)="data">
              <div id="variations-head"># Vars</div>
              <b-tooltip target="variations-head"
                         triggers="hover"
                         container="concepts-sum-tbl"
                         title="The count of unique variations for a concept"></b-tooltip>
            </template>
            <template #head(variation_values)="data">
              <div id="variations-values-head">Variations</div>
              <b-tooltip target="variations-values-head"
                         triggers="hover"
                         container="concepts-sum-tbl"
                         title="The unique set of variations for a concept"></b-tooltip>
            </template>
            <template #head(count_variations_ratio)="data">
              <div id="variations-ratio-head">Variations Ratio</div>
              <b-tooltip target="variations-ratio-head"
                         triggers="hover"
                         container="concepts-sum-tbl"
                         title="The ratio of number of annotations and the number of variations of a concept"></b-tooltip>
            </template>
            <template #head(cui)="data">
              <div id="cui-head">CUI</div>
              <b-tooltip target="cui-head"
                         triggers="hover"
                         container="concepts-sum-tbl"
                         title="The Concept Unique Identifier"></b-tooltip>
            </template>
            <template #head(cui_f1)="data">
              <div id="cui-f1-head">F1</div>
              <b-tooltip target="cui-f1-head"
                         triggers="hover"
                         container="concepts-sum-tbl"
                         title="The harmonic mean of the recall and precision scores"></b-tooltip>
            </template>
            <template #head(cui_prec)="data">
              <div id="cui-prec-head">Prec</div>
              <b-tooltip target="cui-prec-head"
                         triggers="hover"
                         container="concepts-sum-tbl"
                         title="The precision scores of a concept."></b-tooltip>
            </template>
            <template #head(cui_rec)="data">
              <div id="cui-rec-head">Rec</div>
              <b-tooltip target="cui-rec-head"
                         triggers="hover"
                         container="concepts-sum-tbl"
                         title="The recall scores of a concept."></b-tooltip>
            </template>
            <template #head(tps)="data">
              <div id="tps-head">TPs</div>
              <b-tooltip target="tps-head"
                         triggers="hover"
                         container="concepts-sum-tbl"
                         title="True positives - concept examples that are annotated and predicted by the model"></b-tooltip>
            </template>
            <template #head(fns)="data">
              <div id="fns-head">FNs</div>
              <b-tooltip target="fns-head"
                         triggers="hover"
                         container="concepts-sum-tbl"
                         title="False negatives - concept examples that annotated but not predicted by the model"></b-tooltip>
            </template>
            <template #head(fps)="data">
              <div id="fps-head">FPs</div>
              <b-tooltip target="fps-head"
                         triggers="hover"
                         container="concepts-sum-tbl"
                         title="False positives - concept examples that are predicted but not annotated"></b-tooltip>
            </template>
            <template #cell(variation_values)="data">
              <div>{{data.item.value.join(', ')}}</div>
            </template>
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
              <button class="btn btn-outline-success res-btn" :disabled="data.item.tps === 0"
                      @click="openExamples('tp_examples', data.item)">
                {{data.item.tps}}
              </button>
            </template>
            <template #cell(fns)="data">
              <button class="btn btn-outline-warning res-btn" :disabled="data.item.fns === 0"
                      @click="openExamples('fn_examples', data.item)">
                {{data.item.fns}}
              </button>
            </template>
            <template #cell(fps)="data">
              <button class="btn btn-outline-danger res-btn" :disabled="data.item.fps === 0" @click="openExamples('fp_examples', data.item)">
                {{data.item.fps}}
              </button>
            </template>
          </b-table>
        </b-tab>
        <b-tab v-if="metaAnnsSummary.items" name="Meta Anns">
          <b-table striped hover small :items="metaAnnsSummary.items" :fields="metaAnnsSummary.fields" class="meta-anno-summary"></b-table>
        </b-tab>
      </b-tabs>
    </div>
    <modal class="summary-modal" v-if="modalData.results" :closable="true" @modal:close="clearModalData">
      <h3 slot="header">{{modalData.title}}</h3>
      <div slot="body">
        <div v-if="modalData.type === 'fp'">
          <p>False positive model predictions can be the result of:</p>
          <ul>
            <li>Alternative model predictions that are overlapping with other concepts</li>
            <li>Genuine missed annotations by an annotator.</li>
          </ul>
          <p>Clicking through these annotations will not highlight this annotation as it doesn't exist in the dataset </p>
        </div>
        <div v-if="modalData.type === 'fn'">
          <p>False negative model predictions can be the result of:</p>
          <ul>
            <li>An model mistake that marked an annotation 'correct' where it should be incorrect</li>
            <li>An annotator mistake that marked an annotation 'correct' where it should be incorrect</li>
          </ul>
        </div>
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
            <anno-result v-for="(res, key) of modalData.results" :key="key" :result="res" :type="modalData.type"></anno-result>
          </tbody>
        </table>
      </div>
    </modal>
  </div>
</template>

<script>
import Modal from '@/components/common/Modal.vue'
import AnnoResult from '@/components/anns/AnnoResult.vue'
import LoadingOverlay from '@/components/common/LoadingOverlay.vue'

export default {
  name: 'Metrics.vue',
  components: { AnnoResult, Modal, LoadingOverlay },
  props: {
    reportId: Number
  },
  created () {
    if (this.reportId || (this.$route.query && this.$route.query.reportId)) {
      this.loading = true
      let reportId = this.reportId ? this.reportId : this.$route.query.reportId
      this.$http.get(`/api/metrics/${reportId}/`).then(resp => {
        this.loading = false
        this.reportName = resp.data.results.report_name || resp.data.results.report_name_generated
        this.$set(this.userStats, 'items', resp.data.results.user_stats)
        this.$set(this.conceptSummary, 'items', resp.data.results.concept_summary)
        let anno_summary = resp.data.results.annotation_summary.map(s => {
          if (s.correct) {
            s.status = 'Correct'
          } else if (s.deleted) {
            s.status = 'Incorrect'
          } else if (s.alternative) {
            s.status = 'Alternative'
          } else if (s.manually_created) {
            s.status = 'Manually Added'
          } else if (s.killed) {
            s.status = 'Terminated'
          } else if (s.irrelevant) {
            s.status = 'Irrelevant'
          }
          return s
        })
        this.$set(this.annoSummary, 'items', anno_summary)
        this.$set(this.metaAnnsSummary, 'items', resp.data.results.meta_anno_summary)
      })
    }
  },
  data () {
    return {
      loading: false,
      reportName: null,
      editingName: false,
      editedReportName: null,
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
          { key: 'cui', label: 'CUI', sortable: true },
          { key: 'concept_name', label: 'Concept', sortable: true },
          { key: 'value', label: 'text', sortable: true },
          { key: 'status', label: 'Status', sortable: true }
        ]
      },
      conceptSummary: {
        fields: [
          { key: 'concept_name', sortable: true },
          { key: 'concept_count', sortable: true },
          { key: 'variations', sortable: true },
          { key: 'variation_values', label: ''},
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
      modalData: {
        results: null,
        title: null,
        type: null
      }
    }
  },
  methods: {
    textColorClass (status) {
      return {
        'task-color-text-0': status === 'Correct' || status === 'Manually Added',
        'task-color-text-1': status === 'Incorrect',
        'task-color-text-2': status === 'Terminated',
        'task-color-text-3': status === 'Alternative',
        'task-color-text-4': status === 'Irrelevant'
      }
    },
    clearModalData () {
      this.modalData = {
        results: null,
        title: null,
        type: null
      }
    },
    openExamples (exampleType, item) {
      if (exampleType === 'tp_examples') {
        this.modalData.title = 'True Positive Model Predictions'
        this.modalData.type = 'tp'
      } else if (exampleType === 'fp_examples') {
        this.modalData.title = 'False Positive Model Predictions'
        this.modalData.type = 'fp'
      } else {
        this.modalData.title = 'False Negative Model Predictions'
        this.modalData.type = 'fn'
      }
      const idx = this.conceptSummary.items.indexOf(item)
      this.modalData.results = this.conceptSummary.items[idx][exampleType]
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
    },
    saveEditedName () {
      if (this.editingName && this.editedReportName !== '') {
        const payload = {
          report_name: this.editedReportName
        }
        this.$http.put(`/api/metrics/${this.reportId}/`, payload).then(_ => {
          this.reportName = this.editedReportName
          this.editingName = false
        })
      }
    },
    keydown (e) {
      if (e.keyCode === 27 && this.editingName) { // esc key
        this.editingName = false
      } else if (e.keyCode === 13 && this.editingName) { // enter key
        this.saveEditedName()
      }
    },
  },
  mounted () {
    window.addEventListener('keydown', this.keydown)
  },
  beforeDestroy () {
    window.removeEventListener('keydown', this.keydown)
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

.no-report-name {
  color: #768692; // NHS Mid Grey
}

.completed-report-name {
  font-style: italic;
}

.report-name-input {
  display: inline-block;
  height: 30px;
}

.viewport {
  height: 100%;

  .tab-content {
    height: 100%;

    .tab-pane {
      height: calc(100% - 30px);
    }
  }
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
  height: 25px;
  padding: 0 1px;
  background-image: linear-gradient(to right, #32ab60, #E8EDEE);
  box-shadow: 0 5px 5px -5px #32ab60;
}

.edit-name-icon {
  height: 11px;
  margin-bottom: 15px;
  opacity: 0.5;
}

.res-btn {
  height: 25px;
  padding: 3px 10px !important;
  border: 0 !important;
}
</style>
