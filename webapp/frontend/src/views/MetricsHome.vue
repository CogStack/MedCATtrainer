<template>
  <div class="full-height metrics-reports-table">
    <loading-overlay :loading="loadingReports">
      <p slot="message">Loading Metrics Reports...</p>
    </loading-overlay>
    <b-table id="metrics-jobs-table" hover small selectable
             :items="reports.items"
             :fields="reports.fields"
             :select-mode="'single'"
             @row-selected="loadMetrics">
      <template #cell(projects)="data">
        <v-runtime-template :template="data.value"></v-runtime-template>
      </template>

      <template #cell(status)="data">
        <span v-if="data.item.status == 'pending'">Pending
          <font-awesome-icon icon="fa-regular fa-clock" class="status-icon"></font-awesome-icon>
        </span>
        <span v-if="data.item.status == 'running'">Running
          <font-awesome-icon icon="spinner" spin class="status-icon"></font-awesome-icon>
        </span>
        <span v-if="data.item.status == 'complete'">Complete
          <font-awesome-icon icon="check" class="status-icon success"></font-awesome-icon>
        </span>
      </template>
      <template #cell(cleanup)="data">
        <button class="btn btn-outline-danger" @click="confDeleteReportModal = data.item">
          <font-awesome-icon icon="times"></font-awesome-icon>
        </button>
      </template>
    </b-table>
    <modal v-if="confDeleteReportModal" :closable="true" @modal:close="confDeleteReportModal = null">
      <h3 slot="header">Confirm Delete Metrics Report</h3>
      <div slot="body">
        <div v-if="confDeleteReportModal.status == 'running'">
          Metrics report still running, this will cancel the running metrics report running job
        </div>
        <div v-if="confDeleteReportModal.status == 'complete'">
          Confirm complete metrics report deletion. To regenerate the report reselect the projects on the
          home screen and select metrics.
        </div>
      </div>
      <div slot="footer">
        <button class="btn btn-danger" @click="confRemoval">Confirm</button>
      </div>
    </modal>
  </div>
</template>

<script>
import VRuntimeTemplate from 'v-runtime-template'
import LoadingOverlay from '@/components/common/LoadingOverlay.vue'
import Modal from '@/components/common/Modal.vue'

export default {
  name: "MetricsHome",
  components: {Modal, LoadingOverlay, VRuntimeTemplate,},
  props: {
  },
  data () {
    return {
      loadingReports: false,
      confDeleteReportModal: null,
      projects: {},
      reports: {
        items: [],
        fields: [
          { key: 'report_id', label: 'ID' },
          { key: 'report_name', label: 'Report Name' },
          { key: 'created_user', label: 'Created User' },
          { key: 'create_time', label: 'Create Time' },
          { key: 'projects', label: 'Projects', formatter: this.projectsFormatter },
          { key: 'status', label: 'Status' },
          { key: 'cleanup', label: 'Remove' }
        ]
      }
    }
  },
  created () {
    this.loadingReports = true
    this.pollReportStatus()
  },
  methods: {
    pollReportStatus () {
      this.$http.get('/api/metrics-job/').then(resp => {
        this.loadingReports = false
        this.reports.items = resp.data.reports.map(i => {
          const item = {...i}
          item.report_name = item.report_name || item.report_name_generated
          return item
        })
        this.fetchProjects()
        setTimeout(this.pollReportStatus, 5000)
      })
    },
    fetchProjects () {
      this.reports.items.forEach(item => {
        item.projects.forEach(projId => {
          if (!Object.keys(this.projects).includes(projId)) {
            this.$http.get(`/api/project-annotate-entities/${projId}/`).then(resp => {
              this.projects[projId] = resp.data
            })
          }
        })
      })
    },
    loadMetrics (rows) {
      this.$router.push({
        name: 'metrics',
        params: {
          reportId: rows[0].report_id
        }
      })
    },
    confRemoval () {
      const item = this.confDeleteReportModal
      this.$http.delete(`/api/metrics-job/${this.confDeleteReportModal.report_id}/`).then(_ => {
        this.confDeleteReportModal = null
        this.reports.items.splice(item)
      }).finally(err => {
        this.confDeleteReportModal = null
      })
    },
    projectsFormatter (value) {
      let outEl = ''
      value.forEach(i => {
        if (this.projects[i]) {
          outEl += `
          <div>
            <router-link :to="{ name: 'train-annotations', params: { projectId: '${i}' }}">${this.projects[i].name}</router-link>
          </div>`
        } else {
          outEl += `<div>${i}</div>`
        }
      })
      return `<div>${outEl}</div>`
    }
  }
}
</script>

<style scoped lang="scss">
.metrics-reports-table {
  padding: 10px 0;
  width: 95%;
  margin: auto;
  height: calc(100% - 100px);
  overflow-y: auto;
}

.status-icon {
  padding-left: 3px;
}

.project-links {
  color: #005EB8;

  &:hover {
    color: #fff;
    border-bottom: 1px solid #fff;
  }
}

</style>
