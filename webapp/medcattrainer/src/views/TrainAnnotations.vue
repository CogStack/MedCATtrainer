<template>
  <div class="container-fluid app-container">
    <div class="app-header">
      <div class="half-width">
        <span>Train Annotations:
          <h4 class="project-name">{{ project === null ? '' : project.name }}</h4>
        </span>
      </div>

      <div class="half-width meta">
        <h5 class="file-name-heading" v-if="docs.length > 0">
          <span class="file-name">{{ currentDoc.name }}</span>
          <span class="divider">|</span>
          <span class="file-name">{{ totalDocs - (project !== null ? project.validated_documents.length : 0)}} Remaining</span>
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
      <clinical-text :loading="loadingDoc" :text="currentDoc !== null ? currentDoc.text : null"
                     :currentEnt="currentEnt" :ents="ents" :task="task" @select:concept="selectEntity"
                      @select:addSynonym="addSynonym">
      </clinical-text>
      <div class="sidebar-container">
        <transition name="slide-left">
          <concept-summary v-if="!conceptSynonymSelection" :selectedEnt="currentEnt" :tasks="[task]" class="concept-summary"></concept-summary>
        </transition>
        <transition name="slide-left">
          <add-synonym v-if="conceptSynonymSelection" :selection="conceptSynonymSelection" :projectId="projectId"
                       @request:addSynonymComplete="conceptSynonymSelection = null" class="add-synonym"></add-synonym>
        </transition>
        <task-bar class="tasks" :currentTask="task" :tasks="[task]" :taskLocked="taskLocked" @select:taskValue="markEntity"></task-bar>
        <nav-bar class="nav" :tasks="[task]" :ents="ents" :currentEnt="currentEnt"
                 @select:next="next" @select:back="back" @submit="submitDoc"></nav-bar>
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

    <modal v-if="docToSubmit !== null" @modal:close="docToSubmit=null">
      <h3 slot="header">Submit Document</h3>
      <div slot="body">Please confirm this Document is ready for submission</div>
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
import TaskBar from '@/components/common/TaskBar.vue'
import AddSynonym from '@/components/anns/AddSynonym.vue'

// Only retrieve 1000 entities at a time??
const ENT_LIMIT = 1000;

const annotationTask =  {
  name: 'Concept Annotation',
  propName: 'correct',
  values: [
    ['Correct', 1],
    ['Incorrect', 0]
  ]
};

const taskValueToBackendValue = {
  true: 'Correct',
  false: 'Incorrect'
};

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
  },
  props: {
    projectId: {
      required: true,
    },
    docId: {
      required: false,
    }
  },
  data: function() {
    return {
      docs: [],
      totalDocs: 0,
      nextDocSetUrl: null,
      nextEntSetUrl: null,
      task: annotationTask,
      taskLocked: false,
      project: null,
      validatedDocuments: [],
      ents: null,
      currentDoc: null,
      currentEnt: null,
      loadingDoc: false,
      helpModal: false,
      errorModal: false,
      docToSubmit: null,
      conceptSynonymSelection: null,
    }
  },
  created: function() {
    this.fetchData()
  },
  watch: {
    '$route': 'fetchData',
  },
  methods: {
    fetchData: function() {
      this.$http.get(`/project-annotate-entities?id=${this.projectId}`).then(resp => {
        if (resp.data.count === 0)
          this.errorModal = true;
        else {
          this.project = resp.data.results[0];
          this.validatedDocuments = this.project.validated_documents;
          this.fetchDocuments();
        }
      })
    },
    fetchDocuments: function() {
      let params = this.nextDocSetUrl === null ? `?dataset=${this.projectId}`:
          this.nextDocSetUrl.split('/').slice(-1)[0];

      this.$http.get(`/documents/${params}`).then(resp => {
        if (resp.data.results.length > 0) {
          this.docs = this.docs.concat(resp.data.results);
          this.totalDocs = resp.data.count;
          this.nextDocSetUrl = resp.data.next;

          if (this.currentDoc === null) {
            const docIdRoute = Number(this.$route.params.docId);

            if (docIdRoute) {
              // Ideally should only load this page and have load prev docs... meh
              if (this.docs.map(d => d.id).includes(docIdRoute))
                this.loadDoc(docIdRoute);
              else
                this.fetchDocuments()
            } else {
              // find first unvalidated doc.
              const ids = _.difference(this.docs.map(d => d.id), this.validatedDocuments);
              if (ids.length !== 0) {
                this.$router.replace({
                  name: this.$route.name,
                  params: {
                    projectId: this.$route.params.projectId,
                    docId: ids[0]
                  }
                });
                this.loadDoc(ids[0]);
                // load next url worth of docs?
              } else {
                if (nextDocSetUrl !== null)
                  this.fetchDocuments();
                else // no unvalidated docs and no next doc URL. Go back to first doc.
                  this.$router.replace({
                    name: this.$route.name,
                    params: {
                      projectId: this.$route.params.projectId,
                      docId: this.docs[0].id
                    }
                  });
              }
            }
          }
        }
      }).catch(err => {
        console.error(err);
        // use error modal to show errors?
      });
    },
    loadDoc: function(docId) {
      this.currentDoc = _.find(this.docs, (d) => d.id === docId);
      this.prepareDoc()
    },
    prepareDoc: function() {
      this.loadingDoc = true;
      let payload = {
        project_id: this.project.id,
        document_ids: [this.currentDoc.id]
      };
      this.$http.post('/prepare-documents', payload).then(resp => {
        // assuming a 200 is fine here.
        this.fetchEntities(0, 0);
      }).catch(err => {
        console.error(err)
      });
    },
    fetchEntities: function(entsFetched, pages) {
      if (entsFetched < ENT_LIMIT) {
        let params = this.nextEntSetUrl === null ? `?project=${this.projectId}&document=${this.currentDoc.id}`:
            this.nextEntSetUrl.split('/').slice(-1)[0];
        this.$http.get(`/annotated-entities${params}`).then(resp => {
          let useAssignedVal = !this.project.require_entity_validation ||
            this.project.validated_documents.indexOf(this.currentDoc.id) !== -1;

          if (resp.data.previous === null) {
            this.ents = resp.data.results;
            this.ents.map(e => {
              e.assignedValues = {};
              e.assignedValues[this.task.name] = useAssignedVal ?
                taskValueToBackendValue[e[this.task.propName]] : null;
              return e
            });
            this.currentEnt = this.ents[0]
          } else {
            const newEnts = resp.data.results;
            newEnts.map(e => {
              e.assignedValues = {};
              e.assignedValues[this.task.name] = useAssignedVal ?
                taskValueToBackendValue[e[this.task.propName]] : null;
              return e
            });
            this.ents = this.ents.concat(newEnts)
          }
          this.nextEntSetUrl = resp.data.next;
          if (this.nextEntSetUrl) {
            this.fetchEntities(resp.data.results.length * (pages + 1), pages + 1)
          } else {
            this.loadingDoc = false
          }
        })
      }
    },
    selectEntity: function(entIdx) {
      this.currentEnt = this.ents[entIdx];
    },
    markEntity: function(taskValue) {
      this.currentEnt.assignedValues[this.task.name] = taskValue[0];
      this.currentEnt[this.task.propName] = taskValue[1];
      this.currentEnt.validated = 1;
      this.taskLocked = true;
      this.$http.put(`/annotated-entities/${this.currentEnt.id}/`, this.currentEnt).then(resp => {
        if (this.ents.slice(-1)[0].id !== this.currentEnt.id)
          this.next();
        else
          this.currentEnt = null;
        this.taskLocked = false
      })
    },
    addSynonym: function(selection) {
      this.conceptSynonymSelection = selection
    },
    next: function() {
      this.currentEnt = this.ents[this.ents.indexOf(this.currentEnt)+1]
    },
    back: function() {
      this.currentEnt = this.ents[this.ents.indexOf(this.currentEnt)-1]
    },
    submitDoc: function(docId) {
      this.docToSubmit = docId;
    },
    submitConfirmed: function() {
      this.project.validated_documents = this.project.validated_documents.concat(this.currentDoc.id);
      this.validatedDocuments = this.project.validated_documents;
      this.project.require_entity_validation = this.project.require_entity_validation ? 1 : 0;
      this.$http.put(`/project-annotate-entities/${this.projectId}/`, this.project).then(resp => {
        this.docToSubmit = null;
      })
    }
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

.sidebar-container {
  display: flex;
  flex-direction: column;
  width: 400px;
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
