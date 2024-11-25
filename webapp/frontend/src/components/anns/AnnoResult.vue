<template>
  <tr class="result-container">
    <td class="doc-name">{{result['document name']}}</td>
    <td class="cui">{{result.cui}}</td>
    <td class="source-value">{{result['source value']}}</td>
    <td class="accu">{{Number(result.acc).toFixed(3)}}</td>
    <td class="text">
      <v-runtime-template :template="text"></v-runtime-template>
    </td>
  </tr>
</template>

<script>
import VRuntimeTemplate from 'vue3-runtime-template'

export default {
  name: 'AnnoResult.vue',
  components: { VRuntimeTemplate },
  props: {
    result: Object,
    type: {
      type: String,
      default: 'tp'
    }
  },
  computed: {
    text () {
      if (!this.result || !this.result.text || !this.result['source value']) {
        return ''
      }
      // default to tp
      let highlightClass = 'highlight-task-0'
      if (this.type === 'fp' || this.type === 'fn') {
        highlightClass = 'highlight-task-1'
      }
      const srcVal = this.result['source value']
      const resTxt = this.result.text
      const regexp = RegExp(`${srcVal}`, 'sg')
      const matches = [...resTxt.matchAll(regexp)]
      let outText = '<span>'
      for (let match of matches) {
        if (match.index === 60) {
          // this is the match to use - other matches are spurious, and represent other MedCAT AnnoResults.
          outText = `<span>${resTxt.slice(0, match.index)}`
          outText += `<span class="${highlightClass}" @click="openAnno">${srcVal}</span>`
          outText += `${resTxt.slice(match.index + srcVal.length)}</span>`
        }
      }
      return outText
    }
  },
  methods: {
    openAnno () {
      const routeData = this.$router.resolve(
        {
          path: `/train-annotations/${this.result['project id']}/${this.result['document id']}`,
          query: {
            annoStart: this.result['start'],
            annoEnd: this.result['end']
          }
      })
      window.open(routeData.href, '_blank');
    }
  }
}
</script>

<style scoped lang="scss">
.result-container {
  > td {
    padding: 10px;
  }
}
</style>
