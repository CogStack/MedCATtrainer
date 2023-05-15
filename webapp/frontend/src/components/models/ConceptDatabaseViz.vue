<template>
  <div class="mc-tree-container">
    <div class="zoom-controls">
      <button class="btn btn-default" @click="zoomIn"><font-awesome-icon icon="plus"></font-awesome-icon></button>
      <button  class="btn btn-default" @click="zoomOut"><font-awesome-icon icon="minus"></font-awesome-icon></button>
      <button class="btn btn-default" @click="resetZoom">1:1</button>
    </div>
    <loading-overlay :loading="loading">
      <div slot="message">Retrieving Concept Tree...</div>
    </loading-overlay>
    <div class="mc-tree-view">
      <vue-tree
        style="width: 1500px; height: 1000px;"
        :dataset="cdbData"
        :config="treeConfig"
        :direction="'vertical'"
        ref="tree">
        <template v-slot:node="{ node, collapsed }">
          <div @click="getData(node)" class="node" :style="{ border: collapsed ? '2px solid grey' : '' }">
            {{ node.pretty_name }} - {{ node.cui }}
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
import _ from 'lodash'

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
      treeConfig: { nodeWidth: 100, nodeHeight: 100, levelHeight: 200 },
      zoomSetting: 0
    }
  },
  created () {
    this.loading = true
    this.$http.get(`api/model-concept-children/${this.cdb.id}/`).then(resp => {
      const rootTerm = resp.data.results[0]
      this.cdbData = {
        pretty_name: rootTerm.pretty_name,
        cui: rootTerm.cui,
        _key: rootTerm.cui
      }
      this.getData(this.cdbData)
    })
  },
  mounted () {
    this.debouncedScroll = _.debounce(this.onScroll, 100)
    window.addEventListener('scroll', this.debouncedScroll)
  },
  beforeDestroy () {
    window.removeEventListener('scroll', this.debouncedScroll)
  },
  methods: {
    getData (node) {
      if (this.nodeCuis.indexOf(node.cui) === -1 || node.complete) {
        this.$http.get(`api/model-concept-children/${this.cdb.id}/?parent_cui=${node.cui}`).then(resp => {
          this.$set(node, 'children', resp.data.results.map(r => {
            return {
              pretty_name: r.pretty_name,
              cui: r.cui,
              _key: r.cui
            }
          }))
          this.nodeCuis.push(node.cui)
          this.loading = false
        })
      }
    },
    toggleNodeCheck (node) {
      this.$emit('change:checkedNodes', node)
    },
    onScroll (e) {
      if (this.zoomSetting < e.scrollY) {
        this.zoomOut()
      } else {
        this.zoomIn()
      }
      this.zoomSetting = e.scrollY
    },
    zoomOut () {
      this.$refs.tree.zoomOut()
    },
    zoomIn () {
      this.$refs.tree.zoomIn()
    },
    resetZoom () {
      this.$refs.tree.restoreScale()
    }
  },
  watch: {
    selectedCui (newVal) {
      if (newVal) {
        this.$http.get(`api/concept-path/?cdb_id=${this.cdb.id}&cui=${newVal}`).then(resp => {
          this.cdbData.children = resp.data.results['node_path'].children
          this.cdbData.links = resp.data.results['links']
          this.identifier = 'cui'
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

.zoom-controls {
  position: absolute;
  right: 0;
}
</style>
