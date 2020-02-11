<template>
  <table class="table table-condensed table-hover">
    <thead>
    <th>Annotated Text</th>
    <th>Code</th>
    <th>Code Desc.</th>
    <th>Concept Name</th>
    <th>Concept ID</th>
    </thead>
    <tbody>
      <tr v-for="concept of concepts" :key="concept.id" @click="selectConcept(concept)">
        <td>
          <span>{{leftContext(concept)}}</span>
          <span :class="highlightClass(concept)">
                {{concept.value}}
              </span>
          <span>{{rightContext(concept)}}</span>
        </td>
        <td v-if="codeType === 'icd'">{{(concept.icd10 || []).filter(i => i.id === concept.icd_code)[0].code}}</td>
        <td v-if="codeType === 'icd'">{{(concept.icd10 || []).filter(i => i.id === concept.icd_code)[0].desc}}</td>
        <td v-if="codeType === 'opcs'">{{(concept.opcs4 || []).filter(i => i.id === concept.opcs_code)[0].code}}</td>
        <td v-if="codeType === 'opcs'">{{(concept.opcs4 || []).filter(i => i.id === concept.opcs_code)[0].desc}}</td>
        <td>{{concept.pretty_name}}</td>
        <td>{{concept.cui}}</td>
      </tr>
    </tbody>
  </table>
</template>

<script>
export default {
  name: 'CodingSummaryTable',
  props: {
    concepts: Array,
    leftContext: Function,
    rightContext: Function,
    highlightClass: Function,
    codeType: String
  },
  methods: {
    selectConcept (concept) {
      this.$emit('select:concept', concept)
    }
  }
}
</script>

<style scoped lang="scss">
.pointer {
  cursor: pointer;
}
</style>
