<template>
  <v-select v-model="selectedCUI" @search="searchCUI"
            :inputId="'searchBox'"
            :clearSearchOnSelect="true"
            :filterable="false"
            :appendToBody="true"
            :options="searchResults"
            label="cui">
    <template v-slot:option="option">
      <span class="select-option">{{option.name}}</span>
    </template>
  </v-select>
</template>

<script>
import vSelect from 'vue-select'
import _ from 'lodash'

export default {
  name: 'ConceptPicker',
  components: {
    vSelect
  },
  props: {
    project: Object,
    selection: String
  },
  created () {
    let that = this
    window.setTimeout(function () {
      const el = document.getElementById('searchBox')
      el.focus()
      el.value = that.selection
      that.searchCUI(that.selection, () => true)
    }, 500)
  },
  data () {
    return {
      selectedCUI: null,
      searchResults: []
    }
  },
  watch: {
    'selectedCUI' (newVal) {
      this.$emit('pickedResult:concept', newVal)
    },
    'selection': 'selectionChange'
  },
  methods: {
    searchCUI: _.debounce(function (term, loading) {
      loading(true)

      if (!term) {
        return
      }

      const mapResult = function (r, allResults) {
        const isDupName = allResults.filter(res => res.pretty_name === r.pretty_name).length > 1
        return {
          name: isDupName ? `${r.pretty_name} : ${r.cui}` : r.pretty_name,
          cui: r.cui,
          type_ids: r.type_ids,
          desc: r.desc,
          icd10: r.icd10,
          opcs4: r.opcs4,
          semantic_type: r.semantic_type,
          synonyms: _.replace(r.synonyms, new RegExp(',', 'g'), ', ')
        }
      }

      const that = this
      const conceptDbs = Array.from(new Set(this.project.cdb_search_filter.concat(this.project.concept_db))).join(',')
      const searchByTerm = function () {
        let searchConceptsQueryParams = `search=${term}&cdbs=${conceptDbs}`
        that.$http.get(`/api/search-concepts/?${searchConceptsQueryParams}`).then(resp => {
          that.searchResults = filterResults(that.project,
            resp.data.results.map(res => mapResult(res, resp.data.results)))
          loading(false)
        })
      }
      const filterResults = function (project, results) {
        if (project.restrict_concept_lookup) {
          if (project.cuis) {
            let cuis = project.cuis.split(',').map(c => c.trim())
            results = results.filter(r => cuis.indexOf(r.cui) !== -1)
          }
        }
        return results
      }
      searchByTerm()
    }, 400)
  }
}
</script>

<style scoped lang="scss">
.select-option {
  white-space: pre-wrap;
  padding: 3px 0;
}
</style>
