<template>
  <div class="container usecase">
    <login v-if="!loginSuccessful" @login:success="loggedIn()"></login>
    <h3> Welcome to MedCAT</h3>
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
        </tr>
      </thead>
      <tbody>
        <tr v-for="project of projects" :key="project.id" @click="select(project)">
          <td>{{project.id}}</td>
          <td>{{project.name}}</td>
          <td>{{project.description}}</td>
          <td>{{(new Date(project.create_time)).toLocaleDateString()}}</td>
          <td>{{project.cuis}}</td>
          <td>{{project.tuis}}</td>
          <td>{{project.require_entity_validation ? 'Yes' : 'No'}}</td>
        </tr>
      </tbody>
    </table>
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
      loginSuccessful: false
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
      // train annotations for project,

      this.$router.push({
        name: 'train-annotations',
        params: {
          projectId: project.id
        }
      })
    }
  }
}
</script>

<style scoped lang="scss">
h3 {
  margin: 10%
}
.table td {
  cursor: pointer;
}
</style>
