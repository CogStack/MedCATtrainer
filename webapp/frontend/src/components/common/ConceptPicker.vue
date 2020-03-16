<template>
  <v-select v-model="selectedCUI" @search="searchCUI"
            :inputId="'searchBox'"
            :clearSearchOnSelect="false"
            :filterable="false"
            :options="searchResults">
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
    }, 50)
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
          tui: r.tui,
          type: r.type,
          desc: r.desc,
          icd10: r.icd10,
          opcs4: r.opcs4,
          semantic_type: r.semantic_type,
          synonyms: _.replace(r.synonyms, new RegExp(',', 'g'), ', ')
        }
      }

      const mapCuiInfoResult = function (infoResults, idsToConcepts, selectedCodeParam) {
        return _.orderBy(_.flatten(infoResults.map(cuiInfo => {
          return cuiInfo['concept'].map(conceptId => {
            const concept = idsToConcepts[conceptId]
            if (!concept) {
              // too many concepts to load return null here then filter out of final result.
              return null
            }
            const codeSearchResult = {
              name: `${cuiInfo.code} | ${cuiInfo.desc}\n${concept.cui} | ${concept.pretty_name}`,
              orderKey: cuiInfo.code,
              cui: concept.cui,
              tui: concept.tui,
              desc: concept.desc,
              icd10: concept.icd10,
              opcs4: concept.opcs4,
              semantic_type: concept.semantic_type,
              synonyms: _.replace(concept.synonyms, new RegExp(',', 'g'), ', ')
            }
            codeSearchResult[selectedCodeParam] = cuiInfo.id
            return codeSearchResult
          }).filter(i => i !== null)
        })), ['orderKey'], ['asc'])
      }

      const that = this
      const conceptDbs = this.project.cdb_search_filter.concat(this.project.concept_db).join(',')
      const searchByTerm = function () {
        let searchConceptsQueryParams = `search=${term}&cdb__in=${conceptDbs}`
        that.$http.get(`/api/search-concepts/?${searchConceptsQueryParams}`).then(resp => {
          that.searchResults = resp.data.results.map(res => mapResult(res, resp.data.results))
          loading(false)
        })
      }

      if (term.match(/^(?:c)\d{7}|s-\d*/gmi)) {
        this.$http.get(`/api/concepts/?cui=${term}`).then(resp => {
          if (resp.data.results.length > 0) {
            loading(false)
            this.searchResults = resp.data.results.map(res => mapResult(res, resp.data.results))
          }
        })
      } else if (term.match(/^\w\d\d.*/i)) {
        let searchCdbInfosQueryParams = `code=${term}&cdb=${conceptDbs}`
        this.$http.get(`/api/search-concept-infos/?${searchCdbInfosQueryParams}`).then(infoResp => {
          let conceptIds = new Set(_.flatten((infoResp.data['icd_codes'] || []).map(r => r.concept)))
          _.flatten((infoResp.data['opcs_codes'] || []).map(r => r.concept)).forEach(item => conceptIds.add(item))
          if (conceptIds > 80) {
            // only get the first 80...
            conceptIds = conceptIds.slice(80)
          }
          this.$http.get(`/api/concepts/?id__in=${[...conceptIds].join(',')}`).then(resp => {
            const idsToConcepts = {}
            for (const r of resp.data.results) {
              idsToConcepts[r.id] = r
            }
            let results = []
            results = results.concat(mapCuiInfoResult(infoResp.data['icd_codes'] || [],
              idsToConcepts, 'icdCode'))
            results = results.concat(mapCuiInfoResult(infoResp.data['opcs_codes'] || [],
              idsToConcepts, 'opcsCode'))
            this.searchResults = results
            loading(false)
          })
        })
      } else {
        searchByTerm()
      }
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
