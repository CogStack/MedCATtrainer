<template>
  <div class="full-height project-table">
    <login v-if="!loginSuccessful" @login:success="loggedIn()"></login>
    <transition name="alert"><div class="alert alert-danger" v-if="routeAlert" role="alert">{{routeAlert}}</div></transition>
    <div class="home-title">Available Projects:</div>
    <div class="table-container">
      <loading-overlay :loading="loadingProjects">
        <p slot="message">Loading Projects...</p>
      </loading-overlay>
      <table class="table table-hover" v-if="!loadingProjects">
        <thead>
        <tr>
          <th>ID</th>
          <th>Title</th>
          <th>Description</th>
          <th>Create Time</th>
          <th>Concepts</th>
          <th>Annotate / Validate</th>
          <th>Complete</th>
          <th v-if="isAdmin">Concepts Imported</th>
          <th v-if="isAdmin">Model Loaded</th>
          <th v-if="isAdmin">Save Model</th>
        </tr>
        </thead>
        <tbody>
        <tr v-for="project of projects" :key="project.id" @click="select(project)" :class="{'focus': project.focus || false}">
          <td>{{project.id}}</td>
          <td>{{project.name}}</td>
          <td>{{project.description}}</td>
          <td>{{(new Date(project.create_time)).toLocaleDateString()}}</td>
          <td><span class="term-list">{{project.cuis.slice(0, 40) || 'All'}}</span></td>
          <td>{{project.require_entity_validation ? 'Annotate' : 'Validate'}}</td>
          <td>
            <font-awesome-icon v-if="project.complete" class="complete-project" icon="check"></font-awesome-icon>
          </td>
          <td @click.stop v-if="isAdmin">
            <font-awesome-icon v-if="cdbSearchIndexStatus[project.cdb_search_filter]" icon="check" class="success"></font-awesome-icon>
            <font-awesome-icon v-if="!cdbSearchIndexStatus[project.cdb_search_filter]" icon="times" class="danger"></font-awesome-icon>
          </td>
          <td @click.stop v-if="isAdmin">
            <div v-if="cdbLoaded[project.id]">
              <button class="btn btn-outline-success model-up">
                <font-awesome-icon icon="times" class="clear-model-cache" @click="clearLoadedModel(project.id)"></font-awesome-icon>
                <font-awesome-icon icon="fa-cloud-arrow-up"></font-awesome-icon>
              </button>
            </div>
            <div v-if="!cdbLoaded[project.id]">
              <button class="btn btn-outline-secondary" @click="loadProjectCDB(project.id)">
                <font-awesome-icon v-if="loadingModel !== project.id" icon="fa-cloud-arrow-up"></font-awesome-icon>
                <font-awesome-icon v-if="loadingModel === project.id" icon="spinner" spin></font-awesome-icon>
              </button>
            </div>
          </td>
          <td @click.stop v-if="isAdmin">
            <button class="btn btn-outline-primary" :disabled="saving" @click="saveModel(project.id)"><font-awesome-icon icon="save"></font-awesome-icon></button>
          </td>
        </tr>
        </tbody>
      </table>
    </div>
    <div>
      <transition name="alert"><div class="alert alert-primary" v-if="saving" role="alert">Saving models</div></transition>
      <transition name="alert"><div class="alert alert-primary" v-if="modelSaved" role="alert">Model Successfully saved</div></transition>
      <transition name="alert"><div class="alert alert-danger" v-if="modelSavedError" role="alert">Error saving model</div></transition>
      <transition name="alert"><div class="alert alert-primary" v-if="loadingModel" role="alert">Loading model</div></transition>
      <transition name="alert"><div class="alert alert-danger" v-if="modelCacheLoadError" role="alert">Error loading MedCAT model for project</div></transition>
    </div>
    <modal v-if="clearModelModal" :closable="true" @modal:close="clearModelModal = false">
      <div slot="header">
        <h3>Confirm Clear Cache Model</h3>
      </div>
      <div slot="body">
        Confirm clearing cached MedCAT Model for Project {{clearModelModal}}, this will remove any interim training
        done (if any). To recover the cached model, re-open the project, and re-submit all documents.
      </div>
      <div slot="footer">
        <button class="btn btn-primary" @click="confirmClearLoadedModel(clearModelModal)">Confirm</button>
        <button class="btn btn-default" @click="clearModelModal = false">Cancel</button>
      </div>
    </modal>
  </div>
</template>
<script>
import _ from 'lodash'

import Modal from '@/components/common/Modal.vue'
import Login from '@/components/common/Login.vue'
import EventBus from '@/event-bus'
import LoadingOverlay from '@/components/common/LoadingOverlay.vue'

export default {
  name: 'Home',
  components: {
    LoadingOverlay,
    Login,
    Modal
  },
  data () {
    return {
      projects: [],
      next: null,
      previous: null,
      loginSuccessful: false,
      loadingProjects: false,
      modelSaved: false,
      modelSavedError: false,
      loadingModel: false,
      modelCacheLoadError: false,
      saving: false,
      routeAlert: false,
      isAdmin: false,
      cdbSearchIndexStatus: {},
      cdbLoaded: {},
      clearModelModal: false
    }
  },
  created () {
    this.loggedIn()
  },
  watch: {
    '$route': 'loggedIn'
  },
  mounted () {
    EventBus.$on('login:success', this.loggedIn)
  },
  beforeDestroy () {
    EventBus.$off('login:success')
  },
  methods: {
    loggedIn () {
      this.$http.get('/api/behind-rp/').then(resp => {
        if (!resp.data && this.$route.path !== '/') {
          this.routeAlert = `Invalid URL: ${this.$route.path}, redirected to the MedCAT Home page.`
          const that = this
          setTimeout(() => {
            that.routeAlert = false
          }, 5000)
        }
      })
      // assume if there's an api-token we've logged in before and will try get projects
      // fallback to logging in otherwise
      if (this.$cookie.get('api-token')) {
        this.loginSuccessful = true
        this.isAdmin = this.$cookie.get('admin') === 'true'
        this.fetchProjects()
      }
    },
    fetchProjects () {
      this.loadingProjects = true
      if (this.loginSuccessful) {
        this.$http.get('/api/project-annotate-entities/').then(resp => {
          this.projects = resp.data.results
          if (resp.data.next) {
            this.fetchPage(resp.data.next)
          } else {
            this.fetchCompletionStatus()
            this.fetchCDBsLoaded()
            this.fetchSearchIndexStatus()
            this.loadingProjects = false
          }
        }).catch(() => {
          this.$cookie.delete('username')
          this.$cookie.delete('api-token')
          this.$cookie.delete('admin')
          this.$cookie.delete('user-id')
          this.loadingProjects = false
          this.loginSuccessful = false
        })
      }
    },
    fetchPage (pageUrl) {
      this.$http.get('/' + pageUrl.split('/').slice(-3).join('/')).then(resp => {
        this.projects = this.projects.concat(resp.data.results)
        if (resp.data.next) {
          this.fetchPage(resp.data.next)
        } else {
          this.fetchCompletionStatus()
          this.fetchCDBsLoaded()
        }
      })
    },
    fetchCompletionStatus () {
      this.$http.get(`/api/complete-projects/?projects=${this.projects.map(p => p.id).join(',')}`)
        .then(resp => {
          Object.entries(resp.data.validated_projects).forEach((entry) => {
            this.$set(_.find(this.projects, proj => proj.id === Number(entry[0])), 'complete', entry[1])
          })
          let focusProject = _.findLastIndex(this.projects, proj => proj.complete)
          if (focusProject !== this.projects.length - 1) {
            focusProject += 1
          }
          this.$set(this.projects[focusProject], 'focus', true)
          this.loadingProjects = false

          this.$nextTick(function () {
            const el = document.getElementsByClassName('focus')
            if (el.length > 0) {
              el[0].scrollIntoView({
                block: 'nearest',
                behavior: 'auto'
              })
            }
          })
        })
    },
    fetchCDBsLoaded () {
      this.$http.get('/api/model-loaded/').then(resp => {
        this.cdbLoaded = resp.data
      })
    },
    clearLoadedModel (projId) {
      this.clearModelModal = projId
    },
    confirmClearLoadedModel (projId) {
      this.clearModelModal = false
      this.$http.delete(`/api/cache-model/${projId}/`).then(_ => {
        this.fetchCDBsLoaded()
      })
    },
    loadProjectCDB (projId) {
      this.loadingModel = projId
      this.$http.post(`api/cache-model/${projId}/`).then(_ => {
        this.loadingModel = false
        this.fetchCDBsLoaded()
      }).catch(_ => {
        this.modelCacheLoadError = true
        const that = this
        setTimeout(() => {
          that.modelCacheLoadError = false
        }, 5000)
      })
    },
    fetchSearchIndexStatus () {
      const cdbIds = this.projects.map(p => p.cdb_search_filter[0])
      this.$http.get(`/api/concept-db-search-index-created/?cdbs=${cdbIds.join(',')}`).then(resp => {
        this.cdbSearchIndexStatus = resp.data.results
      }).catch(err => {
        console.log(err)
      })
    },
    select (project) {
      this.$router.push({
        name: 'train-annotations',
        params: {
          projectId: project.id
        }
      })
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
    }
  }
}
</script>

<style scoped lang="scss">
h3 {
  margin: 10%
}

.table-container {
  height: calc(100% - 250px);
  overflow-y: auto;
}

.project-table {
  width: 90%;
  margin: auto;
}

.table {
  table-layout: fixed;
  tbody {
    td {
      .term-list {
        display: block;
        max-width: 20vw;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }
    }
  }

  td {
    cursor: pointer;
  }
}

.home-title {
  font-size: 23px;
  padding: 30px 0;
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

.clear-model-cache {
  font-size: 15px;
  color: $task-color-2;
  cursor: pointer;
  position: absolute;
  right: -5px;
  top: -5px;
}

</style>
