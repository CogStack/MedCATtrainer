<template>
  <div class="container-fluid app-container">
    <div class="app-header">
      <div class="project-name">
        <span>Train Annotations:
          <h4>{{ project === null ? '' : project.name }}</h4>
        </span>
      </div>

      <div class="meta">
        <h5 class="file-name-heading" v-if="((docs || {}).length || 0) > 0">
          <span class="file-name">{{(currentDoc || {}).name}}</span>
          <span class="divider">|</span>
          <span class="files-remaining">{{ totalDocs - (project !== null ? project.validated_documents.length : 0)}} Remaining</span>
        </h5>
        <button class="help btn btn-default" @click="helpModal = true">
          <font-awesome-icon icon="question-circle"></font-awesome-icon>
        </button>
      </div>
    </div>

    <multipane class="viewport-container">
      <div class="full-height">
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
                        :submitLocked="docToSubmit !== null" @select:remove="markRemove" @select:correct="markCorrect"
                        @select:kill="markKill" @select:alternative="toggleAltSearch" @submit="submitDoc"></task-bar>
            </div>
          </div>
        </div>
      </div>
      <multipane-resizer></multipane-resizer>
      <div :style="{ flexGrow: 1, width: '300px', maxWidth: '1000px' }">
        <div class="sidebar-container">
          <transition name="slide-left">
            <concept-summary v-if="!conceptSynonymSelection" :selectedEnt="currentEnt" :altSearch="altSearch"
                             :project="project" :class="{'half-height': metaAnnotate}"
                             @select:altConcept="markAlternative" @select:alternative="toggleAltSearch"
                             class="concept-summary"></concept-summary>
          </transition>
          <transition name="slide-left">
            <meta-annotation-task-container v-if="metaAnnotate" :taskIDs="(project || {}).tasks || []"
                                            :selectedEnt="currentEnt"></meta-annotation-task-container>
          </transition>
          <transition name="slide-left">
            <add-synonym v-if="conceptSynonymSelection" :selection="conceptSynonymSelection"
                         :project="project" :documentId="currentDoc.id"
                         @request:addAnnotationComplete="addAnnotationComplete" class="add-synonym"></add-synonym>
          </transition>
        </div>
      </div>
    </multipane>

    <modal v-if="helpModal" class="help-modal" @modal:close="helpModal = false">
      <h3 slot="header">{{ project.name }} Annotation Help</h3>
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
        <button class="btn btn-primary" :disabled="submitConfirmedLoading" @click="submitConfirmed()">
          <span v-if="!submitConfirmedLoading">Confirm</span>
          <span v-if="submitConfirmedLoading">
            <font-awesome-icon icon="spinner" spin></font-awesome-icon>
          </span>
        </button>
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
import MetaAnnotationTaskContainer from '@/components/usecases/MetaAnnotationTaskContainer.vue'
import { Multipane, MultipaneResizer } from 'vue-multipane'

const TASK_NAME = 'Concept Annotation'
const CONCEPT_CORRECT = 'Correct'
const CONCEPT_REMOVED = 'Deleted'
const CONCEPT_KILLED = 'Killed'
const CONCEPT_ALTERNATIVE = 'Alternative'

const TASK_VALUES = [CONCEPT_CORRECT, CONCEPT_REMOVED, CONCEPT_KILLED, CONCEPT_ALTERNATIVE]

export default {
  name: 'TrainAnnotations',
  components: {
    ConceptSummary,
    DocumentSummary,
    Modal,
    ClinicalText,
    NavBar,
    TaskBar,
    AddSynonym,
    MetaAnnotationTaskContainer,
    Multipane,
    MultipaneResizer
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
      submitConfirmedLoading: false,
      altSearch: false,
      conceptSynonymSelection: null,
      metaAnnotate: false
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
      if (this.$route.params.docId !== docId) {
        this.$router.replace({
          name: this.$route.name,
          params: {
            projectId: this.$route.params.projectId,
            docId: docId
          }
        })
      }
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
            } else if (e.killed) {
              taskVal = CONCEPT_KILLED
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
          this.ents = _.orderBy(this.ents, ['start_ind'], ['asc'])
          this.currentEnt = selectedEntId ? this.ents[this.ents.map(e => e.id).indexOf(selectedEntId)]
            : this.ents[0]
          this.metaAnnotate = this.currentEnt && (this.currentEnt.assignedValues[TASK_NAME] === CONCEPT_ALTERNATIVE ||
            this.currentEnt.assignedValues[TASK_NAME] === CONCEPT_CORRECT)
          this.loadingDoc = false
        }
      })
    },
    selectEntity: function (entIdx) {
      this.currentEnt = this.ents[entIdx]
      this.conceptSynonymSelection = null
      this.metaAnnotate = this.currentEnt.assignedValues[TASK_NAME] === CONCEPT_ALTERNATIVE ||
        this.currentEnt.assignedValues[TASK_NAME] === CONCEPT_CORRECT
    },
    setStatus: function (status) {
      this.currentEnt.validated = 1
      this.currentEnt.correct = 0
      this.currentEnt.killed = 0
      this.currentEnt.alternative = 0
      this.currentEnt.deleted = 0
      this.currentEnt[status] = 1
    },
    markCorrect: function () {
      if (this.currentEnt) {
        this.currentEnt.assignedValues[TASK_NAME] = CONCEPT_CORRECT
        this.setStatus('correct')
        this.markEntity(this.project.tasks.length === 0)
        this.metaAnnotate = this.project.tasks.length > 0
      }
    },
    markEntity: function (moveToNext) {
      if (this.currentEnt) {
        this.taskLocked = true
        this.$http.put(`/api/annotated-entities/${this.currentEnt.id}/`, this.currentEnt).then(resp => {
          if (moveToNext) {
            if (this.ents.slice(-1)[0].id !== this.currentEnt.id) { this.next() } else { this.currentEnt = null }
          }
          this.taskLocked = false
        })
      }
    },
    markRemove: function (kill) {
      if (this.currentEnt) {
        this.currentEnt.assignedValues[TASK_NAME] = kill ? CONCEPT_KILLED : CONCEPT_REMOVED
        if (kill) {
          this.setStatus('killed')
        } else {
          this.setStatus('deleted')
        }
        this.markEntity(true)
        this.metaAnnotate = false
      }
    },
    toggleAltSearch: function (choice) {
      this.altSearch = choice
    },
    markKill: function () {
      this.markRemove(true)
    },
    markAlternative: function (item) {
      this.altSearch = false
      this.taskLocked = true
      this.$http.post(`/api/get-create-entity/`, { label: item.cui }).then(resp => {
        this.currentEnt.assignedValues[TASK_NAME] = CONCEPT_ALTERNATIVE
        this.currentEnt.entity = resp.data.entity_id
        this.setStatus('alternative')
        this.markEntity(this.project.tasks.length === 0)
        this.metaAnnotate = this.project.tasks.length > 0
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
      this.conceptSynonymSelection = null
      let that = this
      window.setTimeout(function () {
        that.conceptSynonymSelection = selection
        that.metaAnnotate = false
      }, 50)
    },
    next: function () {
      this.selectEntity(this.ents.indexOf(this.currentEnt) + 1)
    },
    back: function () {
      this.selectEntity(this.ents.indexOf(this.currentEnt) - 1)
    },
    submitDoc: function (docId) {
      if (this.docToSubmit === null) {
        this.confirmSubmitListenerAdd()
        this.docToSubmit = docId
      }
    },
    submitConfirmed: function () {
      this.confirmSubmitListenerRemove()
      this.submitConfirmedLoading = true
      this.docToSubmit = null
      this.$http.get(`/api/project-annotate-entities/?id=${this.projectId}`).then(resp => {
        // refresh project validated documents as multiple users may be submitting. Mitigates but
        // does not solve a potential inconsistent validated_documents state seen.
        this.project.validated_documents = resp.data.results[0].validated_documents

        if (this.project.validated_documents.indexOf(this.currentDoc.id) === -1) {
          this.project.validated_documents = this.project.validated_documents.concat(this.currentDoc.id)
        }
        this.validatedDocuments = this.project.validated_documents
        this.project.require_entity_validation = this.project.require_entity_validation ? 1 : 0
        this.$http.put(`/api/project-annotate-entities/${this.projectId}/`, this.project).then(() => {
          let payload = {
            project_id: this.project.id,
            document_id: this.currentDoc.id
          }
          this.$http.post(`/api/submit-document/`, payload).then(() => {
            this.submitConfirmedLoading = false
            if (this.currentDoc.id !== this.docs.slice(-1)[0].id ||
              this.validatedDocuments.length !== this.docs.length) {
              let docIds = this.docs.map(d => d.id)
              let newDocId = this.docs[docIds.indexOf(this.currentDoc.id) + 1].id
              while (this.validatedDocuments.indexOf(newDocId) > -1) {
                newDocId = this.docs[docIds.indexOf(newDocId) + 1].id
              }
              this.loadDoc(this.docs[docIds.indexOf(newDocId)].id)
            }
          })
        })
      })
    },
    keyup: function (e) {
      if (e.keyCode === 13 && this.docToSubmit && !this.submitConfirmedLoading) {
        this.submitConfirmed()
      }
    },
    confirmSubmitListenerRemove: function () {
      window.removeEventListener('keyup', this.keyup)
    },
    confirmSubmitListenerAdd: function () {
      window.addEventListener('keyup', this.keyup)
    }
  },
  beforeDestroy: function () {
    this.confirmSubmitListenerRemove()
  }
}
</script>

<style scoped lang="scss">

.app-header {
  display: flex;
  flex-direction: row;
  flex: 0 0 70px;
  line-height: 70px;
  font-size: 25px;
  padding: 0 15px;
}

.Pane {
  position: static !important;
}

.project-name {
  flex: 1 1 auto;
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

.meta {
  flex: 1 1 auto;
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
  height: calc(100% - 71px);
  flex-direction: column;
  padding: 5px;
}

.app-main {
  display: flex;
  flex: 1 1 auto;
  overflow: hidden;
  height: 100%;
}

.viewport-container {
  height: calc(100% - 70px);
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
  width: 95px;
  display: inline-block
}

.tasks {
  width: calc(100% - 95px);
  display: inline-block;
}

.sidebar-container {
  height: 100%;
  display: flex   ;
  flex-direction: column;
  padding: 5px;

  .half-height {
    height: 500px;
  }

  .add-synonym {
    width: 100%;
    flex: 1 1 auto;
  }
}

.slide-left-enter-active {
  transition: all .5s ease;
}

.slide-left-enter, .slide-left-leave-to {
  position: relative;
  transform: translateX(50px);
  transition: all .2s ease;
  opacity: 0;
}

.divider {
  opacity: 0.5;
  padding: 0 5px;
}

.layout-v > .multipane-resizer {
  margin: 0;
  left: 0;
  position: relative;

  &:before {
    display: block;
    content: "";
    width: 5px;
    height: 50px;
    position: absolute;
    top: 50%;
    left: 50%;
    margin-top: -20px;
    margin-left: -1.5px;
    border-left: 1px solid #ccc;
    border-right: 1px solid #ccc;
  }

  &:hover {
    &:before {
      border-color: #999;
    }
  }
}
</style>
