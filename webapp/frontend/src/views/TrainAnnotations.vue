<template>
  <div class="container-fluid app-container">
    <div class="app-header">
      <div class="half-width">
        <span>Train Annotations:
          <h4 class="project-name">{{ project === null ? '' : project.name }}</h4>
        </span>
      </div>

      <div class="half-width meta">
        <h5 class="file-name-heading" v-if="((docs || {}).length || 0) > 0">
          <span class="file-name">{{ currentDoc.name }}</span>
          <span class="divider">|</span>
          <span class="files-remaining">{{ totalDocs - (project !== null ? project.validated_documents.length : 0)}} Remaining</span>
        </h5>
        <button class="help btn btn-default" @click="helpModal = true">
          <font-awesome-icon icon="question-circle"></font-awesome-icon>
        </button>
      </div>
    </div>

    <div class="app-main">
      <document-summary :docs="docs" :moreDocs="nextDocSetUrl !== null"
                        :validatedDocIds="validatedDocuments"
                        :selectedDocId="currentDoc !== null ? currentDoc.id : null" :loadingDoc="loadingDoc"
                        @request:nextDocSet="fetchDocuments()" @request:loadDoc="loadDoc"></document-summary>
      <div class="main-viewport">
        <clinical-text :loading="loadingDoc" :text="currentDoc !== null ? currentDoc.text : null"
                       :currentEnt="currentEnt" :ents="ents" :taskName="taskName" :taskValues="taskValues"
                       @select:concept="selectEntity" @select:addSynonym="addSynonym"></clinical-text>
        <div class="taskbar">
          <nav-bar class="nav" :ents="ents" :currentEnt="currentEnt" @select:next="next" @select:back="back"></nav-bar>
          <task-bar class="tasks" :taskLocked="taskLocked" :ents="ents" :altSearch="altSearch"
                    @select:remove="markRemove" @select:correct="markCorrect" @select:alternative="toggleAltSearch"
                    @submit="submitDoc"></task-bar>
        </div>
      </div>
      <div class="sidebar-container">
        <transition name="slide-left">
          <concept-summary v-if="!conceptSynonymSelection" :selectedEnt="currentEnt" :altSearch="altSearch"
                           :projectTUIs="(project || {}).tuis" @select:altConcept="markAlternative"
                           @select:alternative="toggleAltSearch"
                           class="concept-summary"></concept-summary>
        </transition>
        <transition name="slide-left">
          <add-synonym v-if="conceptSynonymSelection" :selection="conceptSynonymSelection"
                       :projectTUIs="project.tuis" :projectId="project.id" :documentId="currentDoc.id"
                       @request:addAnnotationComplete="addAnnotationComplete" class="add-synonym"></add-synonym>
        </transition>
      </div>
    </div>

    <modal v-if="helpModal" class="help-modal" @modal:close="helpModal = false">
      <h3 slot="header">{{ project.name }} Tagging Help</h3>
      <div slot="body" class="help-modal-body">
        <p>Validate each highlighted concept</p>
        <div>Keyboard Shortcuts</div>
        <table class="table">
          <thead>
            <th>Shortcut Key</th>
            <th>Description</th>
          </thead>
          <tbody>
          <tr>
            <td><font-awesome-icon icon="arrow-up"></font-awesome-icon></td>
            <td>Previous Document</td>
          </tr>
          <tr>
            <td><font-awesome-icon icon="arrow-down"></font-awesome-icon></td>
            <td>Next Document</td>
          </tr>
          <tr>
            <td><font-awesome-icon icon="arrow-left"></font-awesome-icon></td>
            <td>Previous Concept</td>
          </tr>
          <tr>
            <td><font-awesome-icon icon="arrow-right"></font-awesome-icon></td>
            <td>Next Concept</td>
          </tr>
          </tbody>
        </table>
      </div>
      <div slot="footer">
        <button class="btn btn-primary" @click="helpModal = false">Close</button>
      </div>
    </modal>

    <modal v-if="errorModal" @modal:close="errorModal = false">
      <h3 slot="header" class="text-danger">Failed To Load Project</h3>
      <div slot="body">
        <p>No project found for project ID: {{$route.params.projectId}}</p>
      </div>
      <div slot="footer">
        <a href="/"><button class="btn btn-primary">CAT Home</button></a>
      </div>
    </modal>

    <modal v-if="docToSubmit" @modal:close="docToSubmit=null">
      <h3 slot="header">Submit Document</h3>
      <div slot="body">Confirm document is ready for submission</div>
      <!-- TODO: Provide some sort of summary here?? -->
      <div slot="footer">
        <button class="btn btn-primary" @click="submitConfirmed()">Confirm</button>
      </div>
    </modal>
  </div>
</template>

<script>
import _ from 'lodash'

import ConceptSummary from '@/components/common/ConceptSummary.vue'
import DocumentSummary from '@/components/common/DocumentSummary.vue'
import Modal from '@/components/common/Modal.vue'
import ClinicalText from '@/components/common/ClinicalText.vue'
import NavBar from '@/components/common/NavBar.vue'
import TaskBar from '@/components/anns/TaskBar.vue'
import AddSynonym from '@/components/anns/AddSynonym.vue'

const TASK_NAME = 'Concept Annotation'
const CONCEPT_CORRECT = 'Correct'
const CONCEPT_REMOVED = 'Deleted'
const CONCEPT_ALTERNATIVE = 'Alternative'

const TASK_VALUES = [CONCEPT_CORRECT, CONCEPT_REMOVED, CONCEPT_ALTERNATIVE]

export default {
  name: 'TrainAnnotations',
  components: {
    ConceptSummary,
    DocumentSummary,
    Modal,
    ClinicalText,
    NavBar,
    TaskBar,
    AddSynonym
  },
  props: {
    projectId: {
      required: true
    },
    docId: {
      required: false
    }
  },
  data: function () {
    return {
      docs: null,
      totalDocs: 0,
      nextDocSetUrl: null,
      nextEntSetUrl: null,
      taskLocked: false,
      taskName: TASK_NAME,
      taskValues: TASK_VALUES,
      project: null,
      validatedDocuments: null,
      ents: null,
      currentDoc: null,
      currentEnt: null,
      loadingDoc: false,
      helpModal: false,
      errorModal: false,
      docToSubmit: null,
      altSearch: false,
      conceptSynonymSelection: null
    }
  },
  created: function () {
    this.fetchData()
  },
  watch: {
    '$route': 'fetchData'
  },
  methods: {
    fetchData: function () {
      this.$http.get(`/api/project-annotate-entities/?id=${this.projectId}`).then(resp => {
        if (resp.data.count === 0) { this.errorModal = true } else {
          this.project = resp.data.results[0]
          this.validatedDocuments = this.project.validated_documents
          this.fetchDocuments()
        }
      })
    },
    fetchDocuments: function () {
      let params = this.nextDocSetUrl === null ? `?dataset=${this.project.dataset}`
        : `?${this.nextDocSetUrl.split('?').slice(-1)[0]}`

      this.$http.get(`/api/documents/${params}`).then(resp => {
        if (resp.data.results.length > 0) {
          this.docs = resp.data.previous === null ? resp.data.results : this.docs.concat(resp.data.results)
          this.totalDocs = resp.data.count
          this.nextDocSetUrl = resp.data.next

          if (this.currentDoc === null) {
            const docIdRoute = Number(this.$route.params.docId)

            if (docIdRoute) {
              // Ideally should only load this page and have load prev docs... meh
              if (this.docs.map(d => d.id).includes(docIdRoute)) { this.loadDoc(docIdRoute) } else { this.fetchDocuments() }
            } else {
              // find first unvalidated doc.
              const ids = _.difference(this.docs.map(d => d.id), this.validatedDocuments)
              if (ids.length !== 0) {
                this.loadDoc(ids[0])
                // load next url worth of docs?
              } else {
                if (this.nextDocSetUrl !== null) {
                  this.fetchDocuments()
                } else {
                  // no unvalidated docs and no next doc URL. Go back to first doc.
                  this.loadDoc(this.docs[0].id)
                }
              }
            }
          }
        }
      }).catch(err => {
        console.error(err)
        // use error modal to show errors?
      })
    },
    loadDoc: function (docId) {
      this.currentDoc = _.find(this.docs, (d) => d.id === docId)
      this.$router.replace({
        name: this.$route.name,
        params: {
          projectId: this.$route.params.projectId,
          docId: docId
        }
      })
      this.currentEnt = null
      this.prepareDoc()
    },
    prepareDoc: function (params) {
      this.loadingDoc = true
      let payload = {
        project_id: this.project.id,
        document_ids: [this.currentDoc.id]
      }
      if (params) {
        payload = Object.assign(payload, params)
      }
      this.$http.post('/api/prepare-documents/', payload).then(resp => {
        // assuming a 200 is fine here.
        this.fetchEntities()
      }).catch(err => {
        console.error(err)
      })
    },
    fetchEntities: function (selectedEntId) {
      let params = this.nextEntSetUrl === null ? `?project=${this.projectId}&document=${this.currentDoc.id}`
        : `?${this.nextEntSetUrl.split('?').slice(-1)[0]}`
      this.$http.get(`/api/annotated-entities/${params}`).then(resp => {
        let useAssignedVal = !this.project.require_entity_validation ||
          this.project.validated_documents.indexOf(this.currentDoc.id) !== -1

        const ents = resp.data.results.map(e => {
          e.assignedValues = {}
          e.assignedValues[TASK_NAME] = null
          if (useAssignedVal || e.validated) {
            let taskVal = CONCEPT_CORRECT
            if (e.deleted) {
              taskVal = CONCEPT_REMOVED
            } else if (e.alternative) {
              taskVal = CONCEPT_ALTERNATIVE
            }
            e.assignedValues[TASK_NAME] = taskVal
          }
          return e
        })
        if (resp.data.previous === null) {
          this.ents = ents
        } else {
          this.ents = this.ents.concat(ents)
        }
        this.nextEntSetUrl = resp.data.next
        if (this.nextEntSetUrl) {
          this.fetchEntities(selectedEntId)
        } else {
          this.currentEnt = selectedEntId ? this.ents[this.ents.map(e => e.id).indexOf(selectedEntId)]
            : this.ents[0]
          this.ents = _.orderBy(this.ents, ['start_ind'], ['asc'])
          this.loadingDoc = false
        }
      })
    },
    selectEntity: function (entIdx) {
      this.currentEnt = this.ents[entIdx]
    },
    markCorrect: function () {
      // note as correct..
      if (this.currentEnt) {
        this.currentEnt.assignedValues[TASK_NAME] = CONCEPT_CORRECT
        this.currentEnt.validated = 1 // correct is just validated so no need to set anything else
        this.markEntity()
      }
    },
    markEntity: function (noMove) {
      if (this.currentEnt) {
        this.taskLocked = true
        this.$http.put(`/api/annotated-entities/${this.currentEnt.id}/`, this.currentEnt).then(resp => {
          if (noMove !== false) {
            if (this.ents.slice(-1)[0].id !== this.currentEnt.id) { this.next() } else { this.currentEnt = null }
          }
          this.taskLocked = false
        })
      }
    },
    markRemove: function () {
      if (this.currentEnt) {
        this.currentEnt.assignedValues[TASK_NAME] = CONCEPT_REMOVED
        this.currentEnt.validated = 1
        this.currentEnt.deleted = 1
        this.markEntity()
      }
    },
    toggleAltSearch: function (choice) {
      this.altSearch = choice
    },
    markAlternative: function (item) {
      this.altSearch = false
      this.taskLocked = true
      this.$http.post(`/api/get-create-entity/`, { label: item.cui }).then(resp => {
        this.currentEnt.assignedValues[TASK_NAME] = CONCEPT_ALTERNATIVE
        this.currentEnt.entity = resp.data.entity_id
        this.currentEnt.validated = 1
        this.currentEnt.alternative = 1
        this.markEntity(false)
        let i = this.ents.indexOf(this.currentEnt)
        this.currentEnt = JSON.parse(JSON.stringify(this.currentEnt))
        this.ents[i] = this.currentEnt
      })
      this.currentEnt.cui = item.cui
    },
    addAnnotationComplete: function (addedAnnotationId) {
      this.conceptSynonymSelection = null
      if (addedAnnotationId) {
        this.$http.get(`/api/annotated-entities/${addedAnnotationId}/`).then(resp => {
          let newEnt = resp.data
          newEnt.assignedValues = {}
          newEnt.assignedValues[TASK_NAME] = CONCEPT_CORRECT
          this.ents = null
          this.currentEnt = null
          this.fetchEntities(newEnt.id)
        })
      }
    },
    addSynonym: function (selection) {
      this.conceptSynonymSelection = selection
    },
    next: function () {
      this.currentEnt = this.ents[this.ents.indexOf(this.currentEnt) + 1]
    },
    back: function () {
      this.currentEnt = this.ents[this.ents.indexOf(this.currentEnt) - 1]
    },
    submitDoc: function (docId) {
      this.docToSubmit = docId
    },
    submitConfirmed: function () {
      this.project.validated_documents = this.project.validated_documents.concat(this.currentDoc.id)
      this.validatedDocuments = this.project.validated_documents
      this.project.require_entity_validation = this.project.require_entity_validation ? 1 : 0
      this.$http.put(`/api/project-annotate-entities/${this.projectId}/`, this.project).then(resp => {
        this.docToSubmit = null
      })

      let payload = {
        project_id: this.project.id,
        document_id: this.currentDoc.id
      }
      this.$http.post(`/api/submit-document/`, payload).then(() => {
        if (this.currentDoc !== this.docs.slice(-1)[0]) {
          this.loadDoc(_.findIndex(this.docs, d => d.id === this.currentDoc.id) + 1)
        }
      })
    },
    keydown: function (e) {
      if (e.keyCode === 13 && this.docToSubmit) {
        this.submitConfirmed()
      }
    }
  },
  mounted: function () {
    window.addEventListener('keydown', this.keydown)
  },
  beforeDestroy: function () {
    window.removeEventListener('keydown', this.keydown)
  }
}
</script>

<style scoped lang="scss">

.app-header {
  flex: 0 0 70px;
  background-color: $background;
  color: $color-4;
  line-height: 70px;
  font-size: 25px;
  padding: 0 15px;
}

.project-name {
  color: $text-highlight;
}

.help {
  color: $text;
  position: relative;
  top: 10px;
}

.app-header h4 {
  display: inline-block;
}

.half-width {
  display: inline-block;
  width: 50%;
}

.meta {
  text-align: right;
}

.file-name-heading {
  display: inline-block;
  padding-left: 20px;
}

.file-name {
  display: inline-block;
  position: relative;
  top: 5px;
  font-size: 22px;
  max-width: 500px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.files-remaining {
  font-size: 22px;
}

.app-container {
  display: flex;
  height: calc(100% - 80px);
  flex-direction: column;
  padding: 5px;
}

.app-main {
  display: flex;
  flex: 1 1 auto;
  overflow: hidden;
}

.main-viewport {
  display: flex;
  flex-direction: column;
  flex: 1 1 auto;
}

.taskbar {
  flex: 0 0 50px;
}

.nav {
  width: 25%;
  display: inline-block
}

.tasks {
  width: 75%;
  display: inline-block;
}

.sidebar-container {
  @extend .detail-panel;
  display: flex;
  flex-direction: column;
  padding: 5px;

  .concept-summary {
    flex: 1 1 auto;
  }

  .add-synonym {
    flex: 1 1 auto;
  }
}

.slide-left-enter-active {
  transition: all .5s ease;
}

.slide-left-enter, .slide-left-leave-to {
  transform: translateX(50px);
  opacity: 0;
}
.divider {
  opacity: 0.5;
  padding: 0 5px;
}
</style>
