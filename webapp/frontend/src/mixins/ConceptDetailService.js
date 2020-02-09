import _ from 'lodash'

export default {
  name: 'ConceptDetailService',
  methods: {
    fetchDetail (selectedEnt, callback) {
      if (selectedEnt && Object.keys(selectedEnt).length) {
        const queryEntId = selectedEnt.id
        this.$http.get(`/api/entities/${selectedEnt.entity}/`).then(resp => {
          if (selectedEnt && queryEntId === selectedEnt.id) {
            selectedEnt.cui = resp.data.label
            this.fetchConcept(selectedEnt, callback)
          }
        })
      } else {
        if (this.conceptSummary) {
          this.conceptSummary = {}
        }
      }
    },
    fetchConcept (selectedEnt, callback) {
      this.$http.get(`/api/concepts/?cui=${selectedEnt.cui}`).then(resp => {
        if (selectedEnt && resp.data.results.length > 0) {
          selectedEnt.desc = resp.data.results[0].desc
          selectedEnt.tui = resp.data.results[0].tui
          selectedEnt.pretty_name = resp.data.results[0].pretty_name
          selectedEnt.semantic_type = resp.data.results[0].semantic_type
          if (resp.data.results[0].icd10.length > 0) {
            selectedEnt.icd10 = []
            let that = this
            let getCodes = function (url) {
              that.$http.get(url).then(resp => {
                selectedEnt.icd10.push(...resp.data.results)
                if (resp.data.next) {
                  getCodes(`/api/${resp.data.next.split('/api/')[1]}`)
                } else if (callback) {
                  selectedEnt.icd10 = _.orderBy(selectedEnt.icd10, ['code'], ['asc'])
                  callback()
                }
              })
            }
            getCodes(`/api/icd-codes/?id__in=${resp.data.results[0].icd10.join(',')}`)
          } else {
            selectedEnt.icd10 = []
          }
          if (resp.data.results[0].opcs4.length > 0) {
            selectedEnt.opcs4 = []
            let that = this
            let getCodes = function (url) {
              that.$http.get(url).then(resp => {
                selectedEnt.opcs4.push(...resp.data.results)
                if (resp.data.next) {
                  getCodes(`/api/${resp.data.next.split('/api/')[1]}`)
                } else if (callback) {
                  selectedEnt.opcs4 = _.orderBy(selectedEnt.opcs4, ['code'], ['asc'])
                  callback()
                }
              })
            }
            getCodes(`/api/opcs-codes/?id__in=${resp.data.results[0].opcs4.join(',')}`)
          } else {
            selectedEnt.opcs4 = []
          }
        }
        if (callback) {
          callback()
        }
      })
    }
  }
}
