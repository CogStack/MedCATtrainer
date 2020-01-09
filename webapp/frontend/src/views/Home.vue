<template>
  <div class="container full-height">
    <login v-if="!loginSuccessful" @login:success="loggedIn()"></login>
    <h3>Welcome to MedCAT</h3>
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
          <th>Terms</th>
          <th>Annotate / Validate</th>
          <th>Save Model</th>
          <th>Complete</th>
        </tr>
        </thead>
        <tbody>
        <tr v-for="project of projects" :key="project.id" @click="select(project)">
          <td>{{project.id}}</td>
          <td>{{project.name}}</td>
          <td>{{project.description}}</td>
          <td>{{(new Date(project.create_time)).toLocaleDateString()}}</td>
          <td><span class="term-list">{{project.cuis || 'All'}}</span></td>
          <td><span class="term-list">{{project.tuis || 'All'}}</span></td>
          <td>{{project.require_entity_validation ? 'Annotate' : 'Validate'}}</td>
          <td @click.stop><button class="btn btn-outline-primary" @click="saveModel(project.id)"><font-awesome-icon icon="save"></font-awesome-icon></button></td>
          <td>
            <font-awesome-icon v-if="project.complete" class="complete-project" icon="check"></font-awesome-icon>
          </td>
        </tr>
        </tbody>
      </table>
    </div>
    <transition name="alert"><div class="alert alert-info" v-if="saving" role="alert">Saving models</div></transition>
    <transition name="alert"><div class="alert alert-primary" v-if="modelSaved" role="alert">Model Successfully saved</div></transition>
    <transition name="alert"><div class="alert alert-danger" v-if="modelSavedError" role="alert">Error saving model</div></transition>
  </div>
</template>
<script>
import _ from 'lodash'

import Login from '@/components/common/Login.vue'
import EventBus from '@/event-bus'
import LoadingOverlay from '@/components/common/LoadingOverlay.vue'

export default {
  name: 'Home',
  components: {
    LoadingOverlay,
    Login
  },
  data: function () {
    let data = {
      projects: [],
      next: null,
      previous: null,
      loginSuccessful: false,
      loadingProjects: false,
      modelSaved: false,
      modelSavedError: false,
      saving: false
    }

    if (this.$cookie.apiToken) {
      data.loginSuccessful = true
    }
    return data
  },
  created: function () {
    this.loggedIn()
  },
  watch: {
    '$route': 'loggedIn'
  },
  mounted: function () {
    EventBus.$on('login:success', this.loggedIn)
  },
  beforeDestroy: function () {
    EventBus.$off('login:success', this.loggedIn)
  },
  methods: {
    loggedIn: function () {
      if (this.$cookie.get('api-token')) {
        this.loginSuccessful = true
        this.fetchProjects()
      }
    },
    fetchProjects: function () {
      this.loadingProjects = true
      if (this.loginSuccessful) {
        this.$http.get('/api/project-annotate-entities/').then(resp => {
          this.projects = resp.data.results
          if (resp.data.next) {
            this.fetchPage(resp.data.next)
          } else {
            this.fetchCompletionStatus()
            this.loadingProjects = false
          }
        })
      }
    },
    fetchPage: function (pageUrl) {
      this.$http.get('/' + pageUrl.split('/').slice(-3).join('/')).then(resp => {
        this.projects = this.projects.concat(resp.data.results)
        if (resp.data.next) {
          this.fetchPage(resp.data.next)
        } else {
          this.fetchCompletionStatus()
        }
      })
    },
    fetchCompletionStatus: function () {
      this.$http.get(`/api/complete-projects/?projects=${this.projects.map(p => p.id).join(',')}`)
        .then(resp => {
          Object.entries(resp.data.validated_projects).forEach((entry) => {
            this.$set(_.find(this.projects, proj => proj.id === Number(entry[0])), 'complete', entry[1])
          })

          this.loadingProjects = false
        })
    },
    select: function (project) {
      this.$router.push({
        name: 'train-annotations',
        params: {
          projectId: project.id
        }
      })
    },
    saveModel: function (projectId) {
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
  height: calc(100% - 400px);
  overflow-y: auto;
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

.complete-project {
  color: $success;
}

.alert-enter-active, .alert-leave-active {
  transition: opacity .5s;
}

.alert-enter, .alert-leave-to {
  opacity: 0;
}
</style>
