<template>
  <div class="container full-height">
    <login v-if="!loginSuccessful" @login:success="loggedIn()"></login>
    <h3>Welcome to MedCAT</h3>
    <div class="table-container">
      <table class="table table-hover">
        <thead>
        <tr>
          <th>Project ID</th>
          <th>Title</th>
          <th>Description</th>
          <th>Create Time</th>
          <th>UMLS Concepts</th>
          <th>UMLS Terms</th>
          <th>Annotate / Validate</th>
          <th>Save Model</th>
        </tr>
        </thead>
        <tbody>
        <tr v-for="project of projects" :key="project.id" @click="select(project)">
          <td>{{project.id}}</td>
          <td>{{project.name}}</td>
          <td>{{project.description}}</td>
          <td>{{(new Date(project.create_time)).toLocaleDateString()}}</td>
          <td><span class="term-list">{{project.cuis}}</span></td>
          <td><span class="term-list">{{project.tuis}}</span></td>
          <td>{{project.require_entity_validation ? 'Yes' : 'No'}}</td>
          <td @click.stop><button class="btn btn-outline-primary" @click="saveModel(project.id)"><font-awesome-icon icon="save"></font-awesome-icon></button></td>
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
// is this screen even needed?
// Maybe list the the projects that given user has access to ...
import Login from '@/components/common/Login.vue'
import EventBus from '@/event-bus'

export default {
  name: 'Home',
  components: {
    Login
  },
  data: function () {
    let data = {
      projects: [],
      loginSuccessful: false,
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
      if (this.loginSuccessful) {
        this.$http.get('/api/project-annotate-entities/').then((resp) => {
          this.projects = resp.data.results
        })
      }
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
        setTimeout(() => {
          this.modelSaved = false
        }, 5000)
      }).catch(() => {
        this.saving = false
        this.modelSavedError = true
        setTimeout(function () {
          this.modelSavedError = false
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

.alert-enter-active, alert-leave-active {
  transition: opacity .5s;
}

.alert-enter, .alert-leave-to {
  opacity: 0;
}
</style>
