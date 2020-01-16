<template>
  <div class="summary">
    <table class="table table-condensed table-striped table-hover">
      <thead>
        <th>Annotated Text</th>
        <th>Concept ID</th>
        <th>Concept Name</th>
        <th>ICD-10</th>
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
          <td>{{concept.icd10 || ''}}</td>
          <td v-for="task in metaAnnos[concept.id]" :key="task.id">
            <span v-if="concept.correct">{{taskMaps[task.id][task.value]}}</span>
            <span v-if="!concept.correct">n/a</span>
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
      metaAnnos: {
        default () {
          return {}
        },
        type: Object
      },
      taskMaps: Object
    }
  },
  watch: {
    'tasksIDs': 'fetchMetaTasks'
  },
  created () {
    this.enrichSummary()
  },

  methods: {
    enrichSummary() {
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
    enrichMetaAnnos () {
      const that = this
      this.annos.forEach(ent => {
        this.fetchMetaAnnotations(ent, () => {
          this.metaAnnos[ent.id] = _.cloneDeep(that.tasks)
        })
      })
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

.summary-header {
}

.summary-body {

}
</style>
