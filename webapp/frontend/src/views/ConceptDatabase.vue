<template>
  <div class="container-fluid cdb-view">
    <div class="l-sidebar">
      <div class="form-group">
        <label class="title">Concept Database Models</label>
        <select class="form-control" v-model="selectedConceptDB">
          <option :value="cdb" v-for="cdb of cdbs" :key="cdb.id">{{cdb.name}}</option>
        </select>
      </div>
      <div v-if="selectedConceptDB" class="form-group concept-search">
        <concept-picker :restrict_concept_lookup="false"
                        :cui_filter="[]"
                        :cdb_search_filter="[selectedConceptDB.id]"
                        :concept_db="selectedConceptDB.id"
                        @pickedResult:concept="pickedResult">
        </concept-picker>
      </div>
      <div class="title">Concept Filter</div>
      <div class="filter-desc">Selected Nodes:</div>
      <div class="selected-nodes">
        <div class="filter-desc" v-for="node of checkedNodes" :key="node.name">
          <div class="selected-node">{{node.pretty_name}} - {{node.cui}}</div>
          <font-awesome-icon icon="times" class="remove-selected-node" @click="removeNode(node)"></font-awesome-icon>
        </div>
      </div>
      <div id="concept-filter" class="concept-filter-footer">
        <button id="export-filter-btn" class="btn btn-primary export-filter" @click="exportFilter">Export Filter</button>
        <b-tooltip target="export-filter-btn" triggers="hover" container="concept-filter"
                   title="Calculate all child concepts and download as a .json file - to upload into a Trainer project"></b-tooltip>
      </div>
    </div>
    <div class="view-port">
      <concept-database-viz v-if="selectedConceptDB !== null" :cdb="selectedConceptDB"
                            :checkedNodes="checkedNodes"
                            :selectedCui="selectedCui"
                            @select:node="selectNode">
      </concept-database-viz>
    </div>
  </div>
</template>

<script>
import _ from "lodash"
import ConceptDatabaseViz from '@/components/models/ConceptDatabaseViz.vue'
import ConceptPicker from '@/components/common/ConceptPicker.vue'

export default {
  name: 'ConceptDatabase',
  components: { ConceptPicker, ConceptDatabaseViz },
  data () {
    return {
      cdbs: [],
      selectedConceptDB: null,
      checkedNodes: [],
      selectedCui: ''
    }
  },
  created () {
    let cdbList = []
    let that = this
    const baseUrl = '/api/concept-dbs/'
    let getCDBs = function (url) {
      that.$http.get(url).then(resp => {
        if (!resp.data.next) {
          that.cdbs = cdbList.concat(_.uniqBy(resp.data.results, r => r.id))
        } else {
          const nextUrl = `${baseUrl}?${resp.data.next.split('?').slice(-1)}`
          cdbList = cdbList.concat(_.uniqBy(resp.data.results, r => r.id))
          getCDBs(nextUrl)
        }
      })
    }
    getCDBs(baseUrl)
  },
  methods: {
    pickedResult (res) {
      // picked result is used to search upwards to find path to root. via backend...
      this.selectedCui = res.cui
    },
    selectNode (node) {
      const idxOf = this.checkedNodes.indexOf(node)
      if (idxOf === -1) {
        this.checkedNodes.push(node)
      }
    },
    removeNode (nodeToggled) {
      const idxOf = this.checkedNodes.indexOf(nodeToggled)
      this.checkedNodes.splice(idxOf, 1)
    },
    exportFilter () {
      const payload = this.checkedNodes.map(r => r.cui)
      this.$http.post('/api/generate-concept-filter/',
        { 'cuis': payload, 'cdb_id': this.selectedConceptDB.id }).then(resp => {
        const url = window.URL.createObjectURL(new Blob([resp.data]))
        const link = document.createElement('a')
        link.href = url
        link.setAttribute('download',
          resp.headers['content-disposition'].split('=')[1])
        document.body.appendChild(link)
        link.click()
      })
    }
  }
}
</script>

<style scoped lang="scss">
.cdb-view {
  height: calc(100% - 71px);
  display: flex;
}

.filter-desc {
  padding: 5px 5px;
}

.view-port {
  flex: 1 1 auto;
  display: flex;
}

.l-sidebar {
  display: flex;
  flex-direction: column;
  flex: 0 0 400px;
  height: 100%;

  .form-group {
    width: 95%;
  }

  div {
    flex-direction: row;
    flex: 0 0 42px;
  }

  div.selected-nodes {
    flex: 1 1 auto;
    overflow-y: auto;
    box-shadow: 0 5px 5px -5px rgba(0,0,0,0.2);
  }


  .export-filter {
    float: right;
    margin-right: 10px;
    margin-top: 10px;
  }
}

.selected-node {
  display: inline-block;
  width: calc(100% - 20px);
}

.remove-selected-node {
  width: 20px;
  display: inline-block;
  color: $danger;

  &:hover {
    cursor: pointer;
  }
}

</style>
