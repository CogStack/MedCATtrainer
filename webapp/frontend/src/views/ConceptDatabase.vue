<template>
  <div class="container-fluid cdb-view">
    <div class="l-sidebar">
      <div class="form-group">
        <label>Concept Database Models:</label>
        <select class="form-control" v-model="selectedConceptDB">
          <option :value="cdb" v-for="cdb of cdbs" :key="cdb.id">{{cdb.name}}</option>
        </select>
      </div>
      <div class="form-group">
        <concept-picker :restrict_concept_lookup="false"
                        :cui_filter="''"
                        :cdb_search_filter="[selectedConceptDB.id]"
                        :concept_db="selectedConceptDB.id"
                        :selection="name" @pickedResult:concept="pickedResult">
        </concept-picker>
      </div>
    </div>
    <div class="view-port">
      <concept-database-viz v-if="selectedConceptDB !== null" :cdb="selectedConceptDB"></concept-database-viz>
    </div>
  </div>
</template>

<script>
import ConceptDatabaseViz from '@/components/models/ConceptDatabaseViz'
import ConceptPicker from '@/components/common/ConceptPicker'

export default {
  name: 'ConceptDatabase',
  components: { ConceptPicker, ConceptDatabaseViz },
  data () {
    return {
      cdbs: [],
      selectedConceptDB: null
    }
  },
  created () {
    let cdbList = []
    let that = this
    const baseUrl = '/api/concept-dbs/'
    let getCDBs = function (url) {
      that.$http.get(url).then(resp => {
        if (resp.data.count === (cdbList.length + resp.data.results.length)) {
          that.cdbs = cdbList.concat(resp.data.results)
        } else {
          const nextUrl = `${baseUrl}?${resp.data.next.split('?').slice(-1)}`
          cdbList = cdbList.concat(resp.data.results)
          getCDBs(nextUrl)
        }
      })
    }
    getCDBs(baseUrl)
  },
  methods: {
    pickedResult () {
      //
    }
  }
}
</script>

<style scoped>
.cdb-view {
  height: calc(100% - 71px);
  display: flex;
}

.view-port {
  flex: 1 1 auto;
  display: flex;
}

.l-sidebar {
  flex-direction: column;
  flex: 0 0 400px;
  height: 100%;

  .form-group {
    width: 95%;
  }
}

</style>
