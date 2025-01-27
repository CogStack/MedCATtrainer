<template>
  <div class="metrics-view">
    <div class="metrics-header">
      <v-row class="header-row">
        <div class="report-name-label">
          Metrics Report:
        </div>
        <span v-if="!editingName">
          <span v-if="!reportName" class="no-report-name">n/a</span>
          <span v-if="reportName" class="completed-report-name">{{ reportName }}</span>
          <font-awesome-icon icon="pencil" class="edit-name-icon" @click="editingName = true"></font-awesome-icon>
        </span>
        <span class="report-name-input" v-if="editingName">
          <v-text-field placeholder="Report name"
                        class="report-name-input"
                        variant="underlined"
                        @update:focused="updateName($event)"
                        v-model="editedReportName"></v-text-field>
        </span>
      </v-row>


    </div>
    <div class="viewport-full-height">
      <v-overlay :model-value="loading"
                 class="align-center justify-center"
                 color="primary"
                 activator="parent"
                 :disabled="true"
                 :persistent="true">
        <v-progress-circular color="primary" indeterminate></v-progress-circular>
        <span class="overlay-message">Loading metrics report...</span>
      </v-overlay>

      <div class="viewport">
        <v-tabs v-model="tab">
          <v-tab :value="'user_stats'">User Stats</v-tab>
          <v-tab :value="'annotations'">Annotations</v-tab>
          <v-tab :value="'concept_summary'">Concept Summary</v-tab>
          <v-tab :value="'meta_anns'" v-if="metaAnnsSummary.items">Meta Annotations</v-tab>
        </v-tabs>

        <div class="tab-pane">
          <KeepAlive>
            <div v-if="tab === 'user_stats'">
              <v-data-table :items="userStats.items" :headers="userStats.headers" :hover="true" hide-default-footer
                            :items-per-page="-1"></v-data-table>
            </div>
          </KeepAlive>

          <KeepAlive>
            <div v-if="tab === 'annotations'">
                <v-data-table :items="annoSummary.items" :headers="annoSummary.headers" :hover="true" hide-default-footer
                              :items-per-page="-1">
                    <template #item.status="{ item }">
                        <div id="status" :class="textColorClass(item.status)">
                            {{ item.status }}
                            <font-awesome-icon
                                    icon="check-circle" v-if="['Correct', 'Manually Added', 'Alternative'].includes(item.status)">
                            </font-awesome-icon>
                            <font-awesome-icon
                                    icon="times-circle" v-if="['Incorrect', 'Terminated', 'Irrelevant'].includes(item.status)">
                            </font-awesome-icon>
                        </div>
                    </template>
                </v-data-table>
            </div>
          </KeepAlive>

          <KeepAlive>
            <div v-if="tab === 'concept_summary'">
              <v-data-table :items="conceptSummary.items" :headers="conceptSummary.headers" hide-default-footer
                            :items-per-page="-1">
                <template #header.concept>
                  <div>Concept</div>
                  <v-tooltip></v-tooltip>
                </template>
                <template #header.concept_count>
                  Concept Count
                  <v-tooltip activator="parent">Number of occurrences across the projects</v-tooltip>
                </template>
                <template #header.variations>
                  # Vars
                  <v-tooltip activator="parent">The count of unique variations for a concept</v-tooltip>
                </template>
                <template #header.variation_values>
                  Variations
                  <v-tooltip activator="parent">The unique set of variations for a concept</v-tooltip>
                </template>
                <template #header.count_variations_ratio>
                  Variations Ratio
                  <v-tooltip activator="parent">The ratio of number of annotations and the number of variations of a concept</v-tooltip>
                </template>
                <template #header>
                  CUI
                  <v-tooltip activator="parent">The Concept Unique Identifier</v-tooltip>
                </template>
                <template #header.cui_f1>
                  F1
                  <v-tooltip activator="parent">The harmonic mean of the recall and precision scores</v-tooltip>
                </template>
                <template #header.cui_prec>
                  Prec.
                  <v-tooltip activator="parent">The precision scores of a concept</v-tooltip>
                </template>
                <template #header.cui_rec>
                  Rec
                  <v-tooltip activator="parent">The recall scores of a concept</v-tooltip>
                </template>
                <template #header.tps>
                  TPs
                  <v-tooltip activator="parent">True positives - concept examples that are annotated and predicted by the model</v-tooltip>
                </template>
                <template #header.fns>
                  FNs
                  <v-tooltip activator="parent">False negatives - concept examples that annotated but not predicted by the model</v-tooltip>
                </template>
                <template #header.fps>
                  FPs
                  <v-tooltip activator="parent">False positives - concept examples that are predicted but not annotated</v-tooltip>
                </template>
                <template #item.variation_values="{ item }">
                  <div>{{ item.value.join(', ') }}</div>
                </template>
                <template #item.cui_f1="{ item }">
                  <div class="perf-progress">
                    <v-progress-linear
                        v-model="item.cui_f1"
                        color="#32AB60"
                        background-color="#46B480"
                        height="30px"
                        :max="1.0">
                      <span :class="{'good-perf': item.cui_f1 > 0.4}">{{item.cui_f1.toFixed(1)}}</span>
                    </v-progress-linear>
                  </div>
                </template>
                <template #item.cui_rec="{ item }">
                  <div class="perf-progress">
                    <v-progress-linear
                        v-model="item.cui_rec"
                        color="#32AB60"
                        background-color="#46B480"
                        height="30px"
                        :max="1.0">
                      <span :class="{'good-perf': item.cui_rec > 0.4}">{{item.cui_rec.toFixed(1)}}</span>
                    </v-progress-linear>
                  </div>
                </template>
                <template #item.cui_prec="{ item }">
                  <div class="perf-progress">
                    <v-progress-linear
                        v-model="item.cui_prec"
                        color="#32AB60"
                        background-color="#46B480"
                        height="30px"
                        :max="1.0">
                      <span :class="{'good-perf': item.cui_prec > 0.4}">{{item.cui_prec.toFixed(1)}}</span>
                    </v-progress-linear>
                  </div>
                </template>
                <template #item.tps="{ item }">
                  <button class="btn btn-outline-success res-btn" :disabled="item.tps === 0"
                          @click="openExamples('tp_examples', item)">
                    {{ item.tps }}
                  </button>
                </template>
                <template #item.fns="{ item }">
                  <button class="btn btn-outline-warning res-btn" :disabled="item.fns === 0"
                          @click="openExamples('fn_examples', item)">
                    {{ item.fns }}
                  </button>
                </template>
                <template #item.fps="{ item }">
                  <button class="btn btn-outline-danger res-btn" :disabled="item.fps === 0"
                          @click="openExamples('fp_examples', item)">
                    {{ item.fps }}
                  </button>
                </template>
              </v-data-table>
            </div>
          </KeepAlive>

          <KeepAlive>
            <div v-if="tab === 'meta_anns'">
              <v-data-table :items="metaAnnsSummary.items"
                            :headers="metaAnnsSummary.headers"
                            :hover="true"
                            class="meta-anno-summary"
                            hide-default-footer
                            :items-per-page="-1">
              </v-data-table>
            </div>
          </KeepAlive>
        </div>
      </div>

    </div>
    <modal class="summary-modal" v-if="modalData.results" :closable="true" @modal:close="clearModalData">
      <template #header>
        <h3>{{ modalData.title }}</h3>
      </template>
      <template #body>
        <div>
          <div v-if="modalData.type === 'fp'">
            <p>False positive model predictions can be the result of:</p>
            <ul>
              <li>Alternative model predictions that are overlapping with other concepts</li>
              <li>Genuine missed annotations by an annotator.</li>
            </ul>
            <p>Clicking through these annotations will not highlight this annotation as it doesn't exist in the
              dataset </p>
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
            <anno-result v-for="(res, key) of modalData.results" :key="key" :result="res"
                         :type="modalData.type"></anno-result>
            </tbody>
          </table>
        </div>
      </template>
    </modal>
  </div>
</template>

<script>
import Modal from '@/components/common/Modal.vue'
import AnnoResult from '@/components/anns/AnnoResult.vue'

export default {
  name: 'Metrics.vue',
  components: {AnnoResult, Modal},
  props: {
    reportId: Number
  },
  created() {
    if (this.reportId || (this.$route.query && this.$route.query.reportId)) {
      this.loading = true
      let reportId = this.reportId ? this.reportId : this.$route.query.reportId
      this.$http.get(`/api/metrics/${reportId}/`).then(resp => {
        this.loading = false
        this.reportName = resp.data.results.report_name || resp.data.results.report_name_generated
        this.userStats.items = resp.data.results.user_stats
        this.conceptSummary.items = resp.data.results.concept_summary
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
        this.annoSummary.items = anno_summary
        this.metaAnnsSummary.items = resp.data.results.meta_anno_summary
      })
    }
  },
  data() {
    return {
      loading: false,
      tab: null,
      reportName: null,
      editingName: false,
      editedReportName: null,
      userStats: {
        headers: [
          {value: 'user', title: 'User'},
          {value: 'count', title: 'Count'}
        ]
      },
      annoSummary: {
        headers: [
          {value: 'project', title: 'Project'},
          { value: 'document_name', title: 'Doc. Name' },
          { value: 'id', title: 'Annotation Id' },
          { value: 'user', title: 'User' },
          { value: 'cui', title: 'CUI' },
          { value: 'concept_name', title: 'Concept' },
          { value: 'value', title: 'text' },
          { value: 'status', title: 'Status' }
        ]
      },
      conceptSummary: {
        headers: [
          {value: 'concept_name', title: 'Concept Name'},
          { value: 'concept_count' },
          { value: 'variations' },
          { value: 'variation_values', title: ''},
          { value: 'count_variations_ratio', title: 'Variation Ratio' },
          { value: 'cui', title: 'CUI' },
          { value: 'cui_f1', title: 'F1' },
          { value: 'cui_prec', title: 'Prec.' },
          { value: 'cui_rec', title: 'Rec.' },
          { value: 'tps', title: 'TPs' },
          { value: 'fns', title: 'FNs' },
          { value: 'fps', title: 'FPs' }
        ]
      },
      metaAnnsSummary: {
        headers: []
      },
      modalData: {
        results: null,
        title: null,
        type: null
      }
    }
  },
  methods: {
    textColorClass(status) {
      return {
        'task-color-text-0': status === 'Correct' || status === 'Manually Added',
        'task-color-text-1': status === 'Incorrect',
        'task-color-text-2': status === 'Terminated',
        'task-color-text-3': status === 'Alternative',
        'task-color-text-4': status === 'Irrelevant'
      }
    },
    clearModalData() {
      this.modalData = {
        results: null,
        title: null,
        type: null
      }
    },
    openExamples(exampleType, item) {
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
    saveEditedName() {
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
    keydown(e) {
      if (e.keyCode === 27 && this.editingName) { // esc key
        this.editingName = false
      } else if (e.keyCode === 13 && this.editingName) { // enter key
        if (this.editedReportName) {
          this.saveEditedName()
        } else {
          this.editingName = false
        }
      }
    },
    updateName (focused) {
      if (!focused) {
        if (this.editedReportName !== null) {
          this.saveEditedName()
        } else {
          this.editingName = false
        }
      }
    },
  },
  mounted() {
    window.addEventListener('keydown', this.keydown)
  },
  beforeDestroy() {
    window.removeEventListener('keydown', this.keydown)
  }
}
</script>

<style lang="scss">
$metrics-header-height: 50px;

.metrics-view {
  // full-height minus app header height
  height: calc(100% - 60px);
}

.metrics-header {
  @extend .title;
  padding: 10px;
  height: $metrics-header-height;
}

.header-row {
  flex-wrap: nowrap;
  padding: 5px 0;
}

.report-name-label {
  padding: 10px;
  display: inline-block;
}

.viewport-full-height {
  height: calc(100% - #{$metrics-header-height});
  padding: 10px;
}

.no-report-name {
  color: #768692; // NHS Mid Grey
}

.completed-report-name {
  padding: 10px;
  display: inline-block;
  font-style: italic;
}

.report-name-input {
  display: inline-block;
  height: 30px;
  width: 250px;
  padding-left: 5px;
}

.viewport {
  height: 100%;

  .tab-pane {
    height: calc(100% - 48px);
    overflow-y: auto;
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

.perf-progress {
  width: 50px;
}

.edit-name-icon {
  height: 11px;
  margin-bottom: 15px;
  opacity: 0.5;

  &:hover {
    cursor: pointer;
  }
}

.res-btn {
  height: 25px;
  padding: 3px 10px !important;
  border: 0 !important;
  &:hover {
    color: white !important;
  }
}
.v-input--density-default {
  --v-input-control-height: 30px !important;
  --v-input-padding-top: 0px !important;
}

</style>
