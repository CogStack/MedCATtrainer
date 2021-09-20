import _ from 'lodash'

const LOAD_NUM_DOC_PAGES = 10 // 30 docs per page, 300 documents

export default {
  name: 'DocumentService',
  methods: {
    fetchData (urlPref, loadedDataCallback) {
      this.$http.get(`${urlPref}/?id=${this.projectId}`).then(resp => {
        if (resp.data.count === 0) {
          this.errors.modal = true
          this.errors.message = `No project found for project ID: ${this.$route.params.projectId}`
        } else {
          this.project = resp.data.results[0]
          this.validatedDocuments = this.project.validated_documents
          const loadedDocs = () => {
            this.docIds = this.docs.map(d => d.id)
            this.docIdsToDocs = Object.assign({}, ...this.docs.map(item => ({ [item['id']]: item })))
            const docIdRoute = Number(this.$route.params.docId)
            if (docIdRoute) {
              while (!this.docs.map(d => d.id).includes(docIdRoute)) {
                this.fetchDocuments(0, loadedDocs)
              }
              this.loadDoc(this.docIdsToDocs[docIdRoute])
            } else {
              // find first unvalidated doc.
              const ids = _.difference(this.docIds, this.validatedDocuments)
              if (ids.length > 0) {
                this.loadDoc(this.docIdsToDocs[ids[0]])
              } else {
                // no unvalidated docs and no next doc URL. Go back to first doc
                this.loadDoc(this.docs[0])
              }
            }
            if (loadedDataCallback) {
              loadedDataCallback()
            }
          }
          this.fetchDocuments(0, loadedDocs)
        }
      })
    },
    fetchDocuments (numPagesLoaded, finishedLoading) {
      let params = this.nextDocSetUrl === null ? `?dataset=${this.project.dataset}`
        : `?${this.nextDocSetUrl.split('?').slice(-1)[0]}`

      this.$http.get(`/api/documents/${params}`).then(resp => {
        if (resp.data.results.length > 0) {
          this.docs = resp.data.previous === null ? resp.data.results : this.docs.concat(resp.data.results)
          this.totalDocs = resp.data.count
          this.nextDocSetUrl = resp.data.next

          if (this.nextDocSetUrl && numPagesLoaded < LOAD_NUM_DOC_PAGES) {
            this.fetchDocuments(numPagesLoaded + 1, finishedLoading)
          } else {
            if (finishedLoading) {
              finishedLoading()
            }
          }
        }
      }).catch(err => {
        console.error(err)
        // use error modal to show errors?
      })
      return finishedLoading
    },
    loadDoc (doc) {
      this.currentDoc = doc
      if (String(this.$route.params.docId) !== String(doc.id)) {
        this.$router.replace({
          name: this.$route.name,
          params: {
            projectId: this.$route.params.projectId,
            docId: doc.id
          }
        })
      }
      this.currentEnt = null
      this.prepareDoc()
    }
  }
}
