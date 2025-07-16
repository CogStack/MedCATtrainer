<template>
  <div class="container-fluid demo">
    <div class="demo-text">
      <form @submit.prevent>
        <div class="form-group">
          <label>Cached Models:</label>
          <v-select class="form-control"
                    v-model="selectedModel"
                    label="name"
                    :options="cachedModels">
            <template v-slot:option="option">
              <span v-if="option.type === 'cdb'">CDB - </span>
              <span v-else>Model Pack -</span>
                {{option.name}}
              <span v-if="option.cached">
                <v-tooltip activator="parent" text="Model ready">
                  <template v-slot:activator="{ props }">
                    <font-awesome-icon class="model-cached" icon="robot" v-bind="props"></font-awesome-icon>
                  </template>
                </v-tooltip>
              </span>
              <span v-else>
                <v-tooltip activator="parent" text="The model has not been cached">
                  <template v-slot:activator="{ props }">
                    <font-awesome-icon class="model-not-cached" icon="robot" v-bind="props"></font-awesome-icon>
                  </template>
                </v-tooltip>
              </span>
            </template>
          </v-select>

        </div>
        <div class="form-group">
          <label>Text to Annotate:</label>
          <textarea v-model="exampleText" class="form-control" name="text" rows="10"></textarea>
        </div>
        <div class="form-group">
          <label>CUI Filter</label>
          <textarea v-model="cuiFilters" class="form-control" name="cui"
                    rows="3" placeholder="Comma separated list: 91175000, 84757009"></textarea>
        </div>
        <button @click="annotate()" class="btn btn-primary">Annotate</button>
      </form>
    </div>
    <div class="view-port">
      <div class="clinical-text">
        <clinical-text :loading="loadingMsg" :text="annotatedText" :ents="ents"
                       :taskName="task" :taskValues="taskValues" @select:concept="selectEntity"></clinical-text>
      </div>
      <div class="sidebar">
        <concept-summary :selectedEnt="currentEnt" :project="selectedModel"
                         :searchFilterDBIndex="searchFilterDBIndex"></concept-summary>
      </div>
    </div>
  </div>
</template>

<script>
import ClinicalText from '@/components/common/ClinicalText.vue'
import ConceptSummary from '@/components/common/ConceptSummary.vue'

const TASK_NAME = 'Concept Anno'
const VALUES = ['Val']

export default {
  name: 'Demo',
  components: {
    ConceptSummary,
    ClinicalText
  },
  data () {
    return {
      exampleText: '',
      projects: [],
      selectedModel: {},
      cuiFilters: '',
      ents: [],
      currentEnt: {},
      annotatedText: '',
      loadingMsg: null,
      task: TASK_NAME,
      taskValues: VALUES,
      searchFilterDBIndex: null,
      cachedModels: [],
      noModelsError: null
    }
  },
  created () {
    this.$http.get('/api/cache-model/').then(resp => {
      this.cachedModels = resp.data?.cached_models
      if (this.cachedModels?.length == 0) {
        this.noModelsError = true
      } else {
        this.cachedModels = Object.values(this.cachedModels)
      }
    })
  },
  methods: {
    annotate () {
      const payload = {
        model_id: this.selectedModel.cache_id,
        message: this.exampleText,
        cuis: this.cuiFilters,
      }
      this.loadingMsg = 'Annotating Text...'
      this.$http.post('/api/annotate-text/', payload).then(resp => {
        this.loadingMsg = null
        this.ents = resp.data['entities'].map(e => {
          e.assignedValues = {}
          e.assignedValues[this.task] = this.taskValues[0]
          return e
        })
        this.currentEnt = this.ents.length > 0 ? this.ents[0] : null
        this.annotatedText = resp.data['message']
      })
    },
    selectEntity (entIndex) {
      this.currentEnt = this.ents[entIndex]
    },
    fetchCDBSearchIndex () {
      if (this.selectedModel.cdb_search_filter.length > 0) {

        // just select the 'first' cdb_search_filter, as that's likely to be the correct one.
        this.$http.get(`/api/concept-dbs/${this.selectedModel.cdb_search_filter[0]}/`).then(resp => {
          if (resp.data) {
            this.searchFilterDBIndex = `${resp.data.name}_id_${this.selectedModel.cdb_search_filter}`
          }
        })
      }
    }
  },
  watch: {
    'selectedModel': {
      handler () {
        this.fetchCDBSearchIndex()
      }
    }
  }
}
</script>

<style scoped lang="scss">
.demo {
  height: calc(100% - 71px);
  display: flex;
}

.demo-text {
  flex-direction: column;
  flex: 0 0 400px;
  height: 100%;
}

.view-port {
  flex: 1 1 auto;
  display: flex;
}

.clinical-text {
  height:100%;
  flex-direction: column;
  flex: 1 1 auto;
}

.sidebar {
  height:100%;
  flex-direction: column;
  flex: 0 0 350px;
}

form {
  margin: 5%;
}

.model-cached {
  float: right;
  color: $success
}

.model-not-cached {
  float: right;
  opacity: 0.5;
}

</style>
