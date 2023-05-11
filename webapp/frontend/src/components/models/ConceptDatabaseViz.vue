<template>
  <div class="mc-tree-container">
    <loading-overlay :loading="loading">
      <div slot="message">Retrieving Concept Tree...</div>
    </loading-overlay>
    <div class="mc-tree-view">
      <vue-tree
        style="width: 1500px; height: 1000px;"
        :dataset="cdbData"
        :config="treeConfig"
        :direction="'horizontal'">
        <template v-slot:node="{ node, collapsed }">
          <div @click="getData(node)" class="node" :style="{ border: collapsed ? '2px solid grey' : '' }">
            {{ node.value }}
            <div class="form-check">
              <input type="checkbox" @click="toggleNodeCheck(node)"/>
            </div>
          </div>
        </template>
      </vue-tree>
    </div>
  </div>
</template>

<script>
import LoadingOverlay from '@/components/common/LoadingOverlay.vue'

export default {
  name: 'ConceptDatabaseViz',
  components: { LoadingOverlay },
  props: {
    cdb: Object,
    selectedCui: String
  },
  data () {
    return {
      CDB: {},
      cdbData: {},
      nodeCuis: [],
      loading: false,
      treeConfig: { nodeWidth: 100, nodeHeight: 100, levelHeight: 200 }
    }
  },
  created () {
    this.loading = true
    this.$http.get(`api/model-concept-children/${this.cdb.id}/`).then(resp => {
      const rootTerm = resp.data.results[0]
      this.cdbData = {
        value: `${rootTerm.pretty_name} - ${rootTerm.cui}`,
        name: rootTerm.cui,
        _key: rootTerm.cui
      }
      this.getData(this.cdbData)
    })
  },
  methods: {
    getData (node) {
      if (this.nodeCuis.indexOf(node.name) === -1) {
        this.$http.get(`api/model-concept-children/${this.cdb.id}/?parent_cui=${node.name}`).then(resp => {
          this.$set(node, 'children', resp.data.results.map(r => {
            return {
              value: `${r.pretty_name} - ${r.cui}`,
              name: r.cui,
              _key: r.cui
            }
          }))
        })
      }
      this.nodeCuis.push(node.name)
      this.loading = false
    },
    toggleNodeCheck (node) {
      this.$emit('change:checkedNodes', node)
    }
  },
  watch: {
    selectedCui (newVal) {
      if (newVal) {
        this.$http.get(`api/concept-path/?${newVal}`).then(res => {
          //
        })
      }
    }
  }
}
</script>

<style scoped>
.mc-tree-container {
  flex: 1 1 auto;
  overflow-y: auto;
  background: rgba(0, 114, 206, .2);
  padding: 40px 40px 0 40px;
  border-radius: 10px;
  height: 100%;
}

.mc-tree-view {
  background: white;
  overflow-y: auto;
  height: 100%;
  box-shadow: 0 -2px 3px 2px rgba(0, 0, 0, 0.2);
  padding: 25px;
  white-space: pre-wrap;
}

.node {
  width: 250px;
  padding: 3px;
  display: flex;
  flex-direction: row;
  align-items: flex-start;
  justify-content: center;
  font-size: .8rem;
  color: white;
  background-color: #45503B;
  border-radius: 3px;
  margin: 3px;
}
</style>
