<template>
  <div class="full-height project-table">
    <div class="table-container">
      <b-overlay :show="loadingProjects">
        <template #overlay>
          <b-spinner :variant="'primary'"></b-spinner>
          <span class="overlay-message">Loading Projects...</span>
        </template>
      </b-overlay>
      <b-table id="projectTable" hover small :items="projectItems"
               :fields="isAdmin ? projects.fields : projects.fields.filter(f => projects.adminOnlyFields.indexOf(f.key) === -1)"
               :select-mode="'single'"
               selectable
               v-if="!loadingProjects"
               @row-selected="select">
        <template #head(metrics)="data">
          <div id="metrics-head">Metrics</div>
          <b-tooltip target="metrics-head"
                     triggers="hover"
                     container="projectTable"
                     title="Access the metrics view for a single or group of projects"></b-tooltip>
        </template>
        <template #head(cuis)="">
          <div id="cuis-header">Concepts</div>
          <b-tooltip target="cuis-header"
                     triggers="hover"
                     container="projectTable"
                     title="The list of Concept Unique Identifiers (CUIs) to be annotated in a project. 'All' indicates there is no filter"></b-tooltip>
        </template>
        <template #head(status)="">
          <div id="status-header">Project Status</div>
          <b-tooltip target="status-header"
                     triggers="hover"
                     container="projectTable">
            <div>
              <font-awesome-icon class="status-cell" icon="pen"></font-awesome-icon> - project is actively annotating
            </div>
            <div>
              <font-awesome-icon class="status-cell danger" icon="times"></font-awesome-icon> - project marked as discontinued (failed)
            </div>
            <div>
              <font-awesome-icon class="status-cell complete-project success" icon="check"></font-awesome-icon> - project is complete
            </div>
          </b-tooltip>
        </template>
        <template #head(anno_class)="">
          <div id="anno-class-header">Annotation Dataset</div>
          <b-tooltip target="anno-class-header"
                     triggers="hover"
                     container="projectTable">
            Annotation set classification.
            <div>
              <font-awesome-icon class="status-cell" icon="minus"></font-awesome-icon> indicates 'local' annotations are collected specific to this project's use case / clinical area.
            </div>
            <div>
              <font-awesome-icon class="status-cell success" icon="globe"></font-awesome-icon> indicates global annotations are collected suitable for use within a global model.
            </div>
          </b-tooltip>
        </template>

        <template #head(progress)="">
          <div id="progress-header">Progress</div>
          <b-tooltip target="progress-header"
                     triggers="hover"
                     container="projectTable">
            Number of validated documents / total number of documents configured in the project
          </b-tooltip>
        </template>
        <template #cell(locked)="data">
          <font-awesome-icon v-if="data.item.project_locked" class="status-locked" icon="lock"></font-awesome-icon>
          <font-awesome-icon v-if="!data.item.project_locked" class="status-unlocked" icon="lock-open"></font-awesome-icon>
        </template>
        <template #cell(create_time)="data">
          {{new Date(data.item.create_time).toLocaleDateString()}}
        </template>
        <template #cell(last_modified)="data">
          {{new Date(data.item.last_modified).toLocaleString()}}
        </template>
        <template #cell(cuis)="data">
          <div class="term-list">{{data.item.cuis.slice(0, 40) || 'All'}}</div>
        </template>
        <template #cell(require_entity_validation)="data">
          {{data.item.require_entity_validation ? 'Annotate' : 'Validate'}}
        </template>
        <template #cell(status)="data">
          <font-awesome-icon v-if="data.item.project_status === 'A'" class="status-cell" icon="pen"></font-awesome-icon>
          <font-awesome-icon v-if="data.item.project_status === 'D'" class="status-cell danger" icon="times"></font-awesome-icon>
          <font-awesome-icon v-if="data.item.project_status === 'C'" class="status-cell complete-project success" icon="check"></font-awesome-icon>
        </template>
        <template #cell(anno_class)="data">
          <font-awesome-icon v-if="data.item.annotation_classification" class="status-cell success" icon="globe"></font-awesome-icon>
          <font-awesome-icon v-if="!data.item.annotation_classification" class="status-cell" icon="minus"></font-awesome-icon>
        </template>
        <template #cell(cdb_search_filter)="data">
          <font-awesome-icon v-if="cdbSearchIndexStatus[data.item.cdb_search_filter]" icon="check" class="success"></font-awesome-icon>
          <span :id="'concepts-imported-' + data.item.id">
            <font-awesome-icon v-if="!cdbSearchIndexStatus[data.item.cdb_search_filter]" icon="times" class="danger"></font-awesome-icon>
          </span>
          <b-tooltip :target="'concepts-imported-' + data.item.id" :container="'concepts-imported-' + data.item.id"
                     triggers="hover"
                     title="Project concept search not available. Check the project setup 'CDB search filter' option is set and correctly imported."></b-tooltip>
        </template>
        <template #cell(model_loaded)="data">
          <div v-if="cdbLoaded[data.item.id]">
            <button class="btn btn-outline-success model-up">
              <font-awesome-icon icon="times" class="clear-model-cache" @click="clearLoadedModel(data.item.concept_db)"></font-awesome-icon>
              <font-awesome-icon icon="fa-cloud-arrow-up"></font-awesome-icon>
            </button>
          </div>
          <div v-if="!cdbLoaded[data.item.id]">
            <button class="btn btn-outline-secondary" @click="loadProjectCDB(data.item.concept_db)">
              <font-awesome-icon v-if="loadingModel !== data.item.concept_db" icon="fa-cloud-arrow-up"></font-awesome-icon>
              <font-awesome-icon v-if="loadingModel === data.item.concept_db" icon="spinner" spin></font-awesome-icon>
            </button>
          </div>
        </template>
        <template #cell(metrics)="data">
          <button class="btn"
                  :class="{'btn-primary': selectedProjects.indexOf(data.item) !== -1, 'btn-outline-primary': selectedProjects.indexOf(data.item) === -1}"
                  @click="selectProject(data.item)">
            <!--            <font-awesome-icon icon="times" class="selected-project" v-if="selectedProjects.indexOf(data.item) !== -1"></font-awesome-icon>-->
            <font-awesome-icon icon="fa-chart-pie"></font-awesome-icon>
          </button>
        </template>
        <template #cell(save_model)="data">
          <button class="btn btn-outline-primary" :disabled="saving" @click="saveModel(data.item.id)"><font-awesome-icon icon="save"></font-awesome-icon></button>
        </template>
        <template #cell(progress)="data">
          <div v-html="data.value"></div>
        </template>
      </b-table>
    </div>
    <div>
      <transition name="alert"><div class="alert alert-primary" v-if="saving" role="alert">Saving models</div></transition>
      <transition name="alert"><div class="alert alert-primary" v-if="modelSaved" role="alert">Model Successfully saved</div></transition>
      <transition name="alert"><div class="alert alert-danger" v-if="modelSavedError" role="alert">Error saving model</div></transition>
      <transition name="alert"><div class="alert alert-primary" v-if="loadingModel" role="alert">Loading model</div></transition>
      <transition name="alert"><div class="alert alert-danger" v-if="modelCacheLoadError" role="alert">Error loading MedCAT model for project</div></transition>
      <transition name="alert"><div class="alert alert-danger" v-if="projectLockedWarning" role="alert">Unable load a locked project. Contact your CogStack administrator to unlock</div></transition>
      <transition name="alert"><div class="alert alert-info " v-if="metricsJobId">
        Submitted Metrics job {{metricsJobId.metrics_job_id}}. Check the
        <router-link to="metrics-reports/">/metrics-reports/</router-link>
        page for your results</div>
      </transition>
      <transition name="alert"><div class="alert alert-info submit-report-job-alert" v-if="selectedProjects.length > 0">
        Submit metrics report run for selected projects
        <button class="btn btn-outline-primary load-metrics" @click="submitMetricsReportReq">
          <font-awesome-icon icon="chevron-right"></font-awesome-icon>
        </button>
      </div></transition>
    </div>

    <modal v-if="clearModelModal" :closable="true" @modal:close="clearModelModal = false">
      <div slot="header">
        <h3>Confirm Clear Cached Model State</h3>
      </div>
      <div slot="body">
        <p>Confirm clearing cached MedCAT Model for Concept DB {{clearModelModal}} (and any other Projects that use this model). </p>
        <p>
          This will remove any interim training done (if any).
          To recover the cached model, re-open the project(s), and re-submit all documents.
          If you're unsure you should not clear the model state.
        </p>
      </div>
      <div slot="footer">
        <button class="btn btn-primary" @click="confirmClearLoadedModel(clearModelModal)">Confirm</button>
        <button class="btn btn-default" @click="clearModelModal = false">Cancel</button>
      </div>
    </modal>
  </div>
</template>

<script>
import Modal from "@/components/common/Modal.vue"

export default {
  name: "ProjectList",
  components: { Modal},
  props: {
    projectItems: Array,
    isAdmin: Boolean,
    cdbSearchIndexStatus: Object,
    cdbLoaded: Object,
  },
  data () {
    return {
      projects: {
        fields: [
          { key: 'locked', label: ''},
          { key: 'id', label: 'ID', sortable: true },
          { key: 'name', label: 'Title', sortable: true },
          { key: 'description', label: 'Description' },
          { key: 'create_time', label: 'Create Time', sortable: true },
          { key: 'last_modified', label: 'Last Modified', sortable: true },
          { key: 'cuis', label: 'Concepts' },
          { key: 'require_entity_validation', label: 'Annotate / Validate' },
          { key: 'status', label: 'Status', sortable: true },
          { key: 'progress', label: 'Progress', formatter: this.progressFormatter },
          { key: 'anno_class', label: 'Annotation Classification', sortable: true },
          { key: 'cdb_search_filter', label: 'Concepts Imported' },
          { key: 'model_loaded', label: 'Model Loaded' },
          { key: 'metrics', label: 'Metrics' },
          { key: 'save_model', label: 'Save Model' }
        ],
        adminOnlyFields: [
          'anno_class',
          'cdb_search_filter',
          'model_loaded',
          'save_model'
        ]
      },
      projectLockedWarning: false,
      modelSaved: false,
      modelSavedError: false,
      loadingModel: false,
      modelCacheLoadError: false,
      metricsJobId: null,
      saving: false,
      clearModelModal: false,
      selectedProjects: [],
      loadingProjects: false
    }
  },
  methods: {
    clearLoadedModel (cdbId) {
      this.clearModelModal = cdbId
    },
    confirmClearLoadedModel (cdbId) {
      this.clearModelModal = false
      this.$http.delete(`/api/cache-model/${cdbId}/`).then(_ => {
        this.fetchCDBsLoaded()
      })
    },
    loadProjectCDB (cdbId) {
      this.loadingModel = cdbId
      this.$http.get(`/api/cache-model/${cdbId}/`).then(_ => {
        this.loadingModel = false
        this.fetchCDBsLoaded()
      }).catch(_ => {
        this.modelCacheLoadError = true
        this.loadingModel = false
        const that = this
        setTimeout(() => {
          that.modelCacheLoadError = false
        }, 5000)
      })
    },
    selectProject (project) {
      if (this.selectedProjects.indexOf(project) !== -1) {
        this.selectedProjects.splice(this.selectedProjects.indexOf(project), 1)
      } else {
        this.selectedProjects.push(project)
      }
    },
    submitMetricsReportReq () {
      const payload = {
        projectIds: this.selectedProjects.map(p => p.id).join(',')
      }
      this.selectedProjects = []
      this.$http.post('/api/metrics-job/', payload).then(resp => {
        this.metricsJobId = resp.data
        setTimeout(() => {
          this.metricsJobId = null
        }, 15000)
      })
    },

    select (projects) {
      let project = projects[0]
      if (!project.project_locked) {
        this.$router.push({
          name: 'train-annotations',
          params: {
            projectId: project.id
          }
        })
      } else {
        this.projectLockedWarning = true
        const that = this
        setTimeout(() => {
          that.projectLockedWarning = false
        }, 5000)
      }
    },
    saveModel (projectId) {
      let payload = {
        project_id: projectId
      }
      this.saving = true
      this.$http.post('/api/save-models/', payload).then(() => {
        this.saving = false
        this.modelSaved = true
        const that = this
        setTimeout(() => {
          that.modelSaved = false
        }, 5000)
      }).catch(() => {
        this.saving = false
        this.modelSavedError = true
        const that = this
        setTimeout(function () {
          that.modelSavedError = false
        }, 5000)
      })
    },
    progressFormatter (value, key, item) {
      let txtColorClass = 'good-perf'
      if (item['percent_progress'] < 80) {
        txtColorClass = 'bad-perf'
      }
      return `
        <div class="progress-container ${txtColorClass}">
            ${value}
            <div class="progress-gradient-fill" style="width: calc(${item['percent_progress']}%);"></div>
        </div>

      `
    }
  }
}
</script>

<style scoped lang="scss">

.status-cell {
  text-align: center;
}

.status-unlocked {
  text-align: center;
  color: $color-1;
  padding: 0 5px;
  opacity: .5;
}

.status-locked {
  @extend .status-unlocked;
  opacity: 1;
  color: $danger;
}

.project-table {
  height: calc(100% - 30px);
  padding: 10px 0;
  width: 95%;
  margin: auto;
}

.table-container {
  height: calc(100% - 125px);
  overflow-y: auto;
}

.complete-project, .success {
  color: $success;
  font-size: 20px;
}

.danger {
  color: $danger;
  font-size: 20px;
}

.model-up {
  position: relative;
  &:hover {
    cursor: initial !important;
  }
}

.clear-model-cache, {
  font-size: 15px;
  color: $task-color-2;
  cursor: pointer;
  position: absolute;
  right: -5px;
  top: -5px;
}

.selected-project {
  font-size: 15px;
  color: green;
  position: relative;
  right: -40px;
  top: -10px;
}

.load-metrics {
  padding: 0 5px;

}

.progress-container {
  position: relative;
  padding-left: 2px;
}

.progress-gradient-fill {
  position: absolute;
  z-index: -1;
  top: 0;
  height: 25px;
  padding: 0 1px;
  background-image: linear-gradient(to right, #32ab60, #E8EDEE);
  box-shadow: 0 5px 5px -5px #32ab60;
}

.good-perf {
  color: #E5EBEA;
}

.bad-perf {
  color: #45503B;
}

.submit-report-job-alert {
  text-align: right;
}

.term-list {
  display: block;
  max-width: 20vw;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}


</style>
