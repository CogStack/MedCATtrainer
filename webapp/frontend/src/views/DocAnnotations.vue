<template>
  <div class="container-fluid app-container">
    <div class="app-header">
      <div class="project-name">
        <span>
          <h4>{{ project === null ? '' : project.name }}</h4>
        </span>
      </div>

      <div class="meta">
        <h5 class="file-name-heading" v-if="((docs || {}).length || 0) > 0">
          <span class="file-name">{{(currentDoc || {}).name}}</span>
          <span class="divider">|</span>
          <span class="files-remaining">{{ totalDocs - (project !== null ? project.validated_documents.length : 0)}} Remaining</span>
        </h5>
        <button class="btn btn-default" @click="helpModal = true">
          <font-awesome-icon icon="question-circle" class="help-icon"></font-awesome-icon>
        </button>
      </div>
    </div>

    <multipane class="viewport-container">
      <div :style="{minWith: '500px'}" class="full-height">
        <div class="app-main">
          <document-summary :docs="docs" :moreDocs="nextDocSetUrl !== null"
                            :validatedDocIds="validatedDocuments"
                            :selectedDocId="currentDoc !== null ? currentDoc.id : null" :loadingDoc="loadingDoc"
                            @request:nextDocSet="fetchDocuments()" @request:loadDoc="loadDoc"></document-summary>
          <div class="main-viewport">
            <clinical-text :loading="loadingDoc" :text="currentDoc !== null ? currentDoc.text : null"
                           :task-name="taskName" :task-values="taskValues"
                           :current-ent="currentEnt" :ents="ents" :add-annos="true"
                           :cancellable-annos="true" :ctx-menu-option="'Label Text'"
                           @select:addSynonym="addTextAnno"
                           @remove:anno="removeTextAnno"></clinical-text>
            <task-bar :project-id="projectId" :document-id="docId" @submit:successful="submitSuccess"></task-bar>
          </div>
        </div>
      </div>
      <multipane-resizer></multipane-resizer>
      <div :style="{ flexGrow: 1, width: '375px', minWidth: '425px', maxWidth: '1000px' }">
        <div class="sidebar-container">
          <transition name="slide-left">
            <document-annotation-sidebar :clf-tasks="docClfTasks" :reg-tasks="docRegTasks"
                                         :clf-values="docClfValues" :reg-values="docRegValues"
                                         :selected-anno-value="currentDocAnnoValue"
                                         @selected:class="selectTaskLabel"
                                         @changed:selectedAnnoValue="showAnnotationsForDocAnnoValue"
                                         @updated:regTaskValue="updatedRegValue"
                                         @create:regTaskValue="createRegValue">
            </document-annotation-sidebar>
          </transition>
        </div>
      </div>
    </multipane>

    <modal v-if="helpModal" class="help-modal" :closable="true" @modal:close="helpModal = false">
      <h3 slot="header">{{ project.name }} Annotation Help</h3>
      <div slot="body" class="help-modal-body">
        <p>Annotate each document for the associated classification and / or regression tasks.</p>
        <p>Add Annotations for each classification task class or regression task annotation entry.</p>
        <div>Keyboard Shortcuts</div>
        <table class="table">
          <thead>
          <tr>
            <th>Shortcut Key</th>
            <th>Key Name</th>
            <th>Description</th>
          </tr>
          </thead>
          <tbody>
          <tr>
            <td><font-awesome-icon icon="arrow-up"></font-awesome-icon></td>
            <td>Up Arrow</td>
            <td>Previous Document</td>
          </tr>
          <tr>
            <td><font-awesome-icon icon="arrow-down"></font-awesome-icon></td>
            <td>Down Arrow</td>
            <td>Next Document</td>
          </tr>
          <tr>
            <td><font-awesome-icon icon="level-down-alt" :transform="{ rotate: 90 }"></font-awesome-icon></td>
            <td>Enter Key</td>
            <td>Submit</td>
          </tr>
          </tbody>
        </table>
      </div>
      <div slot="footer">
        <button class="btn btn-primary" @click="helpModal = false">Close</button>
      </div>
    </modal>

    <modal v-if="errors.modal" @modal:close="errors.modal = false" class="error-modal">
      <h3 slot="header" class="text-danger">Error: {{errors.message}}</h3>
      <div slot="body" class="error-body">
        <p v-if="errors.description.length > 0">{{errors.description}}</p>
        <p v-if="errors.stacktrace">Full Error:</p>
        <p v-if="errors.stacktrace" class="error-stacktrace">{{errors.stacktrace}}</p>
      </div>
      <div slot="footer">
        <a href="/"><button class="btn btn-primary">MedCATtrainer Home</button></a>
      </div>
    </modal>

    <modal v-if="projectCompleteModal" @modal:close="projectCompleteModal = false">
      <h3 slot="header" class="text-success">Project Annotations Complete</h3>
      <div slot="body">
        <p>Exit this window to review annotations or return to the project selection screen</p>
      </div>
      <div slot="footer">
        <a href="/"><button class="btn btn-primary">MedCATtrainer Home</button></a>
      </div>
    </modal>

    <modal v-if="confirmRemoveClfValModal" :closable="true"
           @modal:close="cancelledRemoveClfValue">
      <h3 slot="header">
        Confirm Removal Label: {{currentDocAnnoValue.doc_anno_value}}
      </h3>
      <div slot="body">This will delete all annotations associated with this class label:
        <div v-for="ent of ents" :key="ent.id" class="confirm-remove-body">
          <div class="highlight-task-0">{{ent.value}}</div>
        </div>
      </div>
      <div slot="footer">
        <button class="btn btn-primary" @click="confirmedRemoveClfValue">Confirm</button>
      </div>
    </modal>
  </div>
</template>

<script>
import _ from 'lodash'

import DocumentSummary from '@/components/common/DocumentSummary.vue'
import Modal from '@/components/common/Modal.vue'
import ClinicalText from '@/components/common/ClinicalText.vue'
import DocumentService from '@/mixins/DocumentService'
import DocumentAnnotationSidebar from '@/components/doc_anno/AnnotationSidebar'
import { Multipane, MultipaneResizer } from 'vue-multipane'
import TaskBar from '@/components/doc_anno/TaskBar'

const TASK_NAME = 'Document Annotation'
const TASK_VALUES = ['Labelled']

export default {
  name: 'DocAnnotations',
  components: {
    TaskBar,
    DocumentAnnotationSidebar,
    DocumentSummary,
    Modal,
    ClinicalText,
    Multipane,
    MultipaneResizer
  },
  mixins: [DocumentService],
  props: {
    projectId: {
      required: true
    },
    docId: {
      required: false
    }
  },
  data () {
    return {
      docs: null,
      docIds: null,
      docIdsToDocs: null,
      nextDocSetUrl: null,
      project: null,
      validatedDocuments: null,
      ents: null,
      taskName: TASK_NAME,
      taskValues: TASK_VALUES,
      currentDoc: null,
      currentEnt: null,
      currentDocAnnoValue: null,
      currentTask: null,
      loadingDoc: null,
      docClfTasks: null,
      docRegTasks: null,
      docClfValues: [],
      docRegValues: [],
      helpModal: false,
      projectCompleteModal: false,
      errors: {
        modal: false,
        message: '',
        description: '',
        stacktrace: ''
      },
      confirmRemoveClfValModal: false,
      removeClfLabelYes: null,
      removeClfLabelNo: null
    }
  },
  created () {
    let loadedDataCallback = () => {
      this.$http.get('/api/document-annotation-tasks/').then(resp => {
        const projTasks = resp.data.results.filter(r => this.project.doc_annotations.indexOf(r.id) !== -1)
        this.docClfTasks = projTasks.filter(r => r.labels)
        this.docRegTasks = projTasks.filter(r => !r.labels)
        this.currentTask = _.head(this.docClfTasks.concat(this.docRegTasks))
      }).catch(err => {
        this.errors.modal = true
        if (err.response) {
          this.errors.message = err.response.data.message || 'Internal Server Error.'
          this.errors.description = err.response.data.description || ''
          this.errors.stacktrace = err.response.data.stacktrace
        }
      })
    }
    this.fetchData('/api/project-annotate-documents', loadedDataCallback)
  },
  methods: {
    prepareDoc () {
      this.loadingDoc = true
      this.fetchDocAnnotations()
    },
    fetchAnnotations (annoValue, url) {
      if (!annoValue || !annoValue.annotations || annoValue.annotations.length === 0) {
        this.loadingDoc = false
        this.ents = []
        return new Promise((resolve) => resolve())
      }
      const annoIds = annoValue.annotations
      let annosUrl = url || `/api/annotations/?id__in=${annoIds}`
      return this.$http.get(annosUrl).then(resp => {
        if (resp.data.previous === null) {
          this.ents = resp.data.results
        } else {
          this.ents = this.ents.concat(resp.data.results)
        }

        if (resp.data.next) {
          this.fetchAnnotations(annoValue, resp.data.next)
        } else {
          this.loadingDoc = false
          this.ents = _.orderBy(this.ents,
            ['start_ind'], ['asc']).map(e => {
            e.assignedValues = {}
            e.assignedValues[TASK_NAME] = TASK_VALUES[0]
            return e
          })
        }
      })
    },
    fetchDocAnnotations () {
      const urlQuery = `project=${this.projectId}&document=${this.currentDoc.id}`
      const clfValsProm = this.$http.get(`/api/document-annotation-clf-values/?${urlQuery}`)
        .then(resp => { this.docClfValues = resp.data.results })
      const regValsProm = this.$http.get(`/api/document-annotation-reg-values/?${urlQuery}`)
        .then(resp => { this.docRegValues = resp.data.results })
      Promise.all([clfValsProm, regValsProm]).then(resps => {
        this.currentDocAnnoValue = _.head(this.docClfValues.concat(this.docRegValues))
        this.fetchAnnotations(this.currentDocAnnoValue)
      })
    },
    showAnnotationsForDocAnnoValue (annoValue) {
      this.currentDocAnnoValue = annoValue
      this.currentTask = this.docClfTasks.concat(this.docRegTasks).filter(t => t.id === annoValue.doc_anno_task)[0]
      return this.fetchAnnotations(this.currentDocAnnoValue)
    },
    selectTaskLabel (task, label, selected) {
      const clickedValue = this.docClfValues.filter(v => {
        return v.doc_anno_task === task.id && v.doc_anno_value === label
      })[0]
      if (selected) {
        if (task.multi_label) {
          this.selectClass(task, label)
        } else {
          // deselect the other values that are currently selected
          const alreadySelected = this.docClfValues.filter(v => {
            return v.doc_anno_task === task.id && v.doc_anno_value !== label
          })
          const deselectThenSelect = () => {
            this.deselectClass(alreadySelected[0]).then(_ => {
              this.selectClass(task, label)
            }).catch(_ => {
            })
          }

          if (alreadySelected.length > 0) {
            if (alreadySelected !== this.currentDocAnnoValue) {
              this.showAnnotationsForDocAnnoValue(alreadySelected[0]).then(_ => {
                deselectThenSelect()
              })
            } else {
              deselectThenSelect()
            }
          } else {
            this.selectClass(task, label)
          }
        }
      } else {
        if (clickedValue !== this.currentDocAnnoValue) {
          this.showAnnotationsForDocAnnoValue(clickedValue).then(_ => {
            this.deselectClass(clickedValue)
          })
        } else {
          this.deselectClass(clickedValue)
        }
      }
    },
    selectClass (task, label) {
      this.ents = []
      let payload = {
        user: this.$cookie.get('user-id'),
        project: Number(this.projectId),
        document: Number(this.currentDoc.id),
        doc_anno_task: task.id,
        doc_anno_value: label,
        annotations: []
      }
      return this.$http.post(`/api/document-annotation-clf-values/`, payload).then(resp => {
        payload.id = resp.data.id
        this.docClfValues.push(payload)
        this.currentDocAnnoValue = _.last(this.docClfValues)
        this.fetchAnnotations()
      })
    },
    deselectClass (docAnnoValue) {
      if (this.ents.length === 0) {
        return this.confirmedRemoveClfValue(docAnnoValue)
      } else {
        this.confirmRemoveClfValModal = true
        return new Promise((resolve, reject) => {
          this.removeClfLabelYes = resolve
          this.removeClfLabelNo = reject
        }).then(_ => {
          this.currentDocAnnoValue = docAnnoValue
        }).catch(err => {
          this.removeClfLabelNo = undefined
          this.removeClfLabelYes = undefined
          throw err
        })
      }
    },
    confirmedRemoveClfValue (docAnnoValue) {
      const valueId = docAnnoValue.id || this.currentDocAnnoValue.id
      return this.$http.delete(`/api/document-annotation-clf-values/${valueId}/`).then(_ => {
        this.confirmRemoveClfValModal = false
        this.docClfValues.splice(this.docClfValues.indexOf(this.docClfValues.filter(v => v.id === valueId)[0]), 1)
        this.currentDocAnnoValue = null
        this.ents = []
        if (this.removeClfLabelYes) {
          this.removeClfLabelYes()
          this.removeClfLabelYes = null
        }
      })
    },
    cancelledRemoveClfValue () {
      this.confirmRemoveClfValModal = false
      if (this.removeClfLabelNo) {
        this.removeClfLabelNo('cancelled')
      }
    },
    updateClfValueAnnotations (docAnnoValue, ents) {
      let payload = {
        user: this.$cookie.get('user-id'),
        project: Number(this.projectId),
        document: Number(this.currentDoc.id),
        doc_anno_task: docAnnoValue.doc_anno_task,
        doc_anno_value: docAnnoValue.doc_anno_value,
        annotations: ents.map(e => e.id)
      }
      return this.$http.put(`/api/document-annotation-clf-values/${docAnnoValue.id}/`, payload)
    },
    createRegValue (task, value) {
      const docAnnoValue = {
        doc_anno_task: task.id,
        doc_anno_value: value
      }
      this.updatedRegValue(docAnnoValue)
    },
    updatedRegValue (docAnnoValue) {
      if (docAnnoValue.id) {
        if (docAnnoValue.doc_anno_value.length === 0) {
          // cleared value
          return this.$http.delete(`/api/document-annotation-reg-values/${docAnnoValue.id}/`).then(_ => {
            this.currentDocAnnoValue = null
            this.docRegValues.splice(this.docRegValues.indexOf(docAnnoValue), 1)
          })
        } else {
          return this.$http.put(`/api/document-annotation-reg-values/${docAnnoValue.id}/`, docAnnoValue).then(
            this.showAnnotationsForDocAnnoValue(docAnnoValue)
          )
        }
      } else {
        let payload = {
          user: this.$cookie.get('user-id'),
          project: Number(this.projectId),
          document: Number(this.currentDoc.id),
          doc_anno_task: docAnnoValue.doc_anno_task,
          doc_anno_value: docAnnoValue.doc_anno_value,
          annotations: []
        }
        return this.$http.post('/api/document-annotation-reg-values/', payload).then(resp => {
          payload.id = resp.data.id
          this.docRegValues.push(payload)
          this.showAnnotationsForDocAnnoValue(payload)
        })
      }
    },
    addTextAnno (selection) {
      let selIdxs = []
      let docText = this.currentDoc.text
      while (docText.indexOf(selection.selStr) !== -1) {
        const i = docText.lastIndexOf(selection.selStr)
        selIdxs.push([i, i + selection.selStr.length])
        docText = docText.slice(0, selIdxs[selIdxs.length - 1][0])
      }
      selIdxs = _.reverse(selIdxs)
      const newEnt = {
        user: this.$cookie.get('user-id'),
        start_ind: selIdxs[selection.selectionOccurrenceIdx][0],
        end_ind: selIdxs[selection.selectionOccurrenceIdx][1],
        value: selection.selStr,
        document: this.currentDoc.id,
        project: this.project.id,
        anno_value_id: this.currentDocAnnoValue.id
      }
      this.$http.post('/api/annotations/', newEnt).then(resp => {
        let updatePromise
        newEnt.id = resp.data.id
        if (this.docClfTasks.map(t => t.id).indexOf(this.currentDocAnnoValue.doc_anno_task) !== -1) {
          updatePromise = this.updateClfValueAnnotations(this.currentDocAnnoValue, this.ents.concat([newEnt]))
        } else if (this.docRegTasks.map(t => t.id).indexOf(this.currentDocAnnoValue.doc_anno_task) !== -1) {
          updatePromise = this.updatedRegValue(this.currentDocAnnoValue)
        }
        if (updatePromise) {
          updatePromise.then(_ => {
            this.currentDocAnnoValue.annotations.push(resp.data.id)
            this.fetchAnnotations(this.currentDocAnnoValue)
          })
        }
      })
    },
    removeTextAnno (ent) {
      this.$http.delete(`/api/annotations/${ent.id}/`).then(_ => {
        this.ents.splice(this.ents.indexOf(ent), 1)
      })
    },
    submitSuccess () {
      const currDocIdIdx = this.docs.map(d => d.id).indexOf(this.currentDoc.id)
      this.project.validated_documents.push(this.currentDoc.id)
      this.validatedDocuments = this.project.validated_documents
      if (currDocIdIdx === this.docs.length - 1) {
        this.projectCompleteModal = true
      } else {
        this.loadDoc(this.docIdsToDocs[this.docs[currDocIdIdx + 1].id])
        this.prepareDoc()
      }
    }
  }
}
</script>

<style lang="scss">
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

.help-icon, .summary-icon, .undo-icon {
  color: $text;
  font-size: 22px;
}

.summary {
  padding-left: 20px
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
  display: flex;
  justify-content: space-between;
  flex-direction: column;
  padding: 5px;
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
  width: 10px;

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

.summary-title {
  padding-bottom: 10px;
  font-size: 17px;
}

.error-stacktrace {
  white-space: pre-wrap;
}

.confirm-remove-body {
  display: block;
  margin: 5px;
  text-align: center;
  > div {
    display: inline-block;
  }
}

</style>
