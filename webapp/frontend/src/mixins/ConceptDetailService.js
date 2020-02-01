
export default {
  name: 'ConceptDetailService',
  methods: {
    fetchDetail (selectedEnt, callback) {
      if (selectedEnt && Object.keys(selectedEnt).length) {
        const queryEntId = selectedEnt.id
        this.$http.get(`/api/entities/${selectedEnt.entity}/`).then(resp => {
          if (selectedEnt && queryEntId === selectedEnt.id) {
            selectedEnt.cui = resp.data.label
            this.$http.get(`/api/concepts/?cui=${selectedEnt.cui}`).then(resp => {
              if (selectedEnt && resp.data.results.length > 0) {
                selectedEnt.desc = resp.data.results[0].desc
                selectedEnt.tui = resp.data.results[0].tui
                selectedEnt.pretty_name = resp.data.results[0].pretty_name
                selectedEnt.semantic_type = resp.data.results[0].semantic_type
                if (resp.data.results[0].icd10.length > 0) {
                  this.$http.get(
                    `/api/icd-codes/?id__in=${resp.data.results[0].icd10.join(',')}`).then(resp => {
                    selectedEnt.icd10 = resp.data.results.map(i => `${i['code']} | ${i['desc']}`).join('\n')
                    if (callback) {
                      callback()
                    }
                  })
                } else {
                  selectedEnt.icd10 = ''
                }
                if (resp.data.results[0].opcs4.length > 0) {
                  this.$http.get(
                    `/api/opcs-codes/?id__in=${resp.data.results[0].opcs4.join(',')}`).then(resp => {
                    selectedEnt.opcs4 = resp.data.results.map(i => `${i['code']} | ${i['desc']}`).join('\n')
                    if (callback) {
                      callback()
                    }
                  })
                } else {
                  selectedEnt.opcs4 = ''
                }
              }
              if (callback) {
                callback()
              }
            })
          }
        })
      } else {
        if (this.conceptSummary) {
          this.conceptSummary = {}
        }
      }
    }
  }
}
