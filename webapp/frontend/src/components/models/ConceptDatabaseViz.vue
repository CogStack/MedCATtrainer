<template>
  <div class="mc-tree-container">
    <div class="mc-tree-view">
      <vue-tree
        style="width: 1500px; height: 1000px;"
        :dataset="cdbData"
        :config="treeConfig">
<!--        <template v-slot:node="{ node, collapsed }">-->
<!--          <div @click="getData(node)" class="node" :style="{ border: collapsed ? '2px solid grey' : '' }">-->
<!--            <span style="padding: 4px 0; font-weight: bold;" >{{ node.value }}</span>-->
<!--          </div>-->
<!--        </template>-->
      </vue-tree>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ConceptDatabaseViz',
  props: {
    cdb: Object
  },
  created () {
    // get root term and first layer? of nodes?
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
  data () {
    return {
      CDB: {},
      cdbData: {},
      nodeCuis: [],
      treeConfig: { nodeWidth: 100, nodeHeight: 100, levelHeight: 200 }
    }
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
  width: 100px;
  padding: 3px;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  justify-content: center;
  color: white;
  background-color: #45503B;
  border-radius: 3px;
}
</style>
