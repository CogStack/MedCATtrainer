<template>
  <tr class="result-container">
    <td class="doc-name">{{result['document name']}}</td>
    <td class="cui">{{result.cui}}</td>
    <td class="source-value">{{result['source value']}}</td>
    <td class="accu">{{result.acc}}</td>
    <td class="text">
      <v-runtime-template :template="text"></v-runtime-template>
    </td>
  </tr>
</template>

<script>
import VRuntimeTemplate from 'v-runtime-template'

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
        if (outText === '<span>') {
          outText += `${resTxt.slice(0, match.index)}`
        } else {
          outText += `${resTxt.slice(matches[matches.indexOf(match) - 1].index + srcVal.length, match.index)}`
        }
        outText += `<span class="${highlightClass}">${srcVal}</span>`
        if (matches.length === 1 || match === matches[-1]) {
          outText += `${resTxt.slice(match.index + srcVal.length)}</span>`
        }
      }
      return outText
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
