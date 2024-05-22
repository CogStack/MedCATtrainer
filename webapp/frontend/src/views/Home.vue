<template>
  <div class="full-height">
    <login v-if="!loginSuccessful" @login:success="loggedIn()"></login>
    <transition name="alert"><div class="alert alert-danger" v-if="routeAlert" role="alert">{{routeAlert}}</div></transition>
    <div class="view-bar" v-if="isAdmin">
      <button class="btn btn-outline-primary" @click="projectGroupView = !projectGroupView">
        <span v-if="projectGroupView">Single Projects</span>
        <span v-if="!projectGroupView">Project Groups</span>
      </button>
    </div>
    <div v-if="projectGroupView" class="full-height project-group-table">
      <b-table id="projectGroupTable" hover :items="projectGroups.items"
               :fields="projectGroups.fields" :select-mode="'single'"
               selectable @row-selected="selectProjectGroup"
               v-if="!loadingProjects">
        <template #cell(last_modified)="data">
          {{new Date(data.item.last_modified).toLocaleString()}}
        </template>
      </b-table>
      <modal v-if="selectedProjectGroup" :closable="true" @modal:close="selectedProjectGroup = null" class="summary-modal">
        <div slot="header">
          <h3>Project Group: {{selectedProjectGroup.name}}</h3>
          <br>
          <p>{{selectedProjectGroup.description}}</p>
        </div>
        <div slot="body">
          <project-list :project-items="selectedProjectGroup.items" :is-admin="isAdmin"></project-list>
        </div>
      </modal>
    </div>
    <project-list v-if="!projectGroupView" :project-items="projects.items" :is-admin="isAdmin"></project-list>
  </div>

</template>
<script>
import _ from 'lodash'

import Modal from '@/components/common/Modal.vue'
import Login from '@/components/common/Login.vue'
import EventBus from '@/event-bus'
import LoadingOverlay from '@/components/common/LoadingOverlay.vue'
import ProjectList from "@/components/common/ProjectList.vue"


export default {
  name: 'Home',
  components: {
    ProjectList,
    LoadingOverlay,
    Login,
    Modal
  },
  data () {
    return {
      projectGroupView: false,
      projectGroups: {
        items: [],
        fields: [
          { key: 'name', label: 'Name', sortable: true },
          { key: 'description', label: 'Description' },
          { key: 'last_modified', label: 'Last Modified', sortable: true }
        ]
      },
      projects: {
        items: []
      },
      routeAlert: false,
      loginSuccessful: false,
      loadingProjects: false,
      isAdmin: false,
      selectedProjectGroup: null,
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
    fetchProjectGroups () {
      const projectGroupIds = new Set(this.projects.items.filter(p => p.group !== null).map(p => p.group))
      this.$http.get(`/api/project-groups/?id__in=${Array.from(projectGroupIds).join(',')}`).then(resp => {
        this.projectGroups.items = resp.data.results
      })
    },
    fetchProjects () {
      this.loadingProjects = true
      if (this.loginSuccessful) {
        this.$http.get('/api/project-annotate-entities/').then(resp => {
          this.projects.items = resp.data.results
          if (resp.data.next) {
            this.fetchPage(resp.data.next)
          } else {
            this.postLoadedProjects()
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
        this.projects.items = this.projects.items.concat(resp.data.results)
        if (resp.data.next) {
          this.fetchPage(resp.data.next)
        } else {
          this.postLoadedProjects()
        }
      })
    },
    postLoadedProjects () {
      this.fetchCDBsLoaded()
      this.fetchSearchIndexStatus()
      this.fetchProjectProgress()
      this.fetchProjectGroups()
      this.loadingProjects = false
    },
    fetchCDBsLoaded () {
      this.$http.get('/api/model-loaded/').then(resp => {
        this.cdbLoaded = resp.data
      })
    },
    fetchSearchIndexStatus () {
      const cdbIds = _.uniq(this.projects.items.map(p => p.cdb_search_filter[0]))
      this.$http.get(`/api/concept-db-search-index-created/?cdbs=${cdbIds.join(',')}`).then(resp => {
        this.cdbSearchIndexStatus = resp.data.results
      }).catch(err => {
        console.log(err)
      })
    },
    fetchProjectProgress () {
      const projectIds = this.projects.items.map(p => p.id)
      this.$http.get(`/api/project-progress/?projects=${projectIds}`).then(resp => {
        this.projects.items = this.projects.items.map(item => {
          item['progress'] = `${resp.data[item.id].validated_count} / ${resp.data[item.id].dataset_count}`
          item['percent_progress'] = Math.ceil((resp.data[item.id].validated_count / resp.data[item.id].dataset_count) * 100)
          return item
        })
      })
    },
    selectProjectGroup(projectGroups) {
      if (projectGroups.length > 0 && projectGroups[0]) {
        this.selectedProjectGroup = projectGroups[0]
        this.selectedProjectGroup.items = this.projects.items.filter(p => p.group === this.selectedProjectGroup.id)
      }
    },
  }
}
</script>

<style lang="scss">
h3 {
  margin: 10%
}

.view-bar {
  height: 30px;
  padding: 5px 0;
  width: 95%;
  margin: auto;
}

.project-group-table {
  height: calc(100% - 30px);
  padding: 10px 0;
  width: 95%;
  margin: auto;
}


.home-title {
  font-size: 23px;
  padding: 30px 0;
}



</style>
