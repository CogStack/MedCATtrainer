<template>
  <div class="summary">
    <table class="table table-condensed   table-hover">
      <thead>
        <th>Annotated Text</th>
        <th>Concept ID</th>
        <th>Concept Name</th>
        <th v-if="showInfoCol('icd10')">ICD-10</th>
        <th v-if="showInfoCol('opcs4')">OPCS-4</th>
        <th v-for="task in tasks" :key="task.id">{{task.name}}</th>
      </thead>
      <tbody>
        <tr v-for="concept in annos" :key="concept.id" class="summary-body" @click="selectConcept(concept)">
          <td>
            <span>{{leftContext(concept)}}</span>
            <span :class="highlightClass(concept)">
              {{concept.value}}
            </span>
            <span>{{rightContext(concept)}}</span>
          </td>
          <td>{{concept.cui}}</td>
          <td>{{concept.pretty_name}}</td>
          <td v-if="showInfoCol('icd10')">{{concept.icd10 || ''}}</td>
          <td v-if="showInfoCol('opcs4')">{{concept.opcs4 || ''}}</td>
          <td v-for="task in metaAnnos[concept.id]" :key="task.id">
            <span>{{taskMaps[task.id][task.value]}}</span>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
import _ from 'lodash'
import MetaAnnotationService from '@/mixins/MetaAnnotationService.js'
import ConceptDetailService from '@/mixins/ConceptDetailService.js'

export default {
  name: 'AnnotationSummary',
  props: {
    annos: Array,
    currentDoc: Object,
    taskIDs: Array
  },
  mixins: [ConceptDetailService, MetaAnnotationService],
  data () {
    return {
      metaAnnos: Object,
      taskMaps: Object
    }
  },
  created () {
    this.enrichSummary()
  },

  methods: {
    enrichSummary () {
      const that = this

      this.annos.forEach(anno => {
        if (!anno.pretty_name) {
          this.fetchDetail(anno)
        }
      })
      if (this.taskIDs.length > 0) {
        this.fetchMetaTasks(this.taskIDs, () => {
          that.taskMaps = {}
          that.tasks.forEach(task => {
            that.taskMaps[task.id] = {}
            task.options.forEach(op => {
              that.taskMaps[task.id][op.id] = op.name
            })
          })
          that.enrichMetaAnnos()
        })
      }
    },
    showInfoCol (info) {
      return _.some(this.annos, a => a[info])
    },
    enrichMetaAnnos () {
      const that = this
      this.metaAnnos = {}
      for (let ent of this.annos) {
        this.fetchMetaAnnotations(ent, tasks => {
          that.$set(that.metaAnnos, ent.id, tasks)
        })
      }
    },
    selectConcept (concept) {
      this.$emit('select:AnnoSummaryConcept', this.annos.indexOf(concept))
    },
    leftContext (concept) {
      return this.currentDoc.text.slice(_.max([0, concept.start_ind - 20]), concept.start_ind)
    },
    rightContext (concept) {
      const docText = this.currentDoc.text
      return this.currentDoc.text.slice(concept.end_ind, _.min([docText.length, concept.end_ind + 20]))
    },
    highlightClass (concept) {
      return {
        'highlight-task-default': !(concept.correct || concept.deleted || concept.killed || concept.alternative),
        'highlight-task-0': concept.correct,
        'highlight-task-1': concept.deleted,
        'highlight-task-2': concept.killed,
        'highlight-task-3': concept.alternative
      }
    }
  }
}
</script>

<style scoped lang="scss">

.summary {
  height: 650px;
  overflow-y: auto;
}
</style>
