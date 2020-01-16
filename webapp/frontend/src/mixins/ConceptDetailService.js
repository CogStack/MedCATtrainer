
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
              if (selectedEnt) {
                selectedEnt.desc = resp.data.results[0].desc
                selectedEnt.tui = resp.data.results[0].tui
                selectedEnt.pretty_name = resp.data.results[0].pretty_name
                selectedEnt.semantic_type = resp.data.results[0].semantic_type
                selectedEnt.icd10 = resp.data.results[0].icd10
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
