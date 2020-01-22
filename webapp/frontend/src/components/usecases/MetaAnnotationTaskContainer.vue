<template>
  <div v-if="tasks && tasks.length > 0">
    <div class="title">Meta Annotation Tasks</div>
    <div class="task-list">
      <meta-annotation-task v-for="task of tasks" :key="task.id"
                            @select:metaAnno="selectedTaskAnno" :task="task"></meta-annotation-task>
    </div>
  </div>
</template>

<script>
import MetaAnnotationTask from '@/components/usecases/MetaAnnotationTask.vue'
import MetaAnnotationService from '@/mixins/MetaAnnotationService.js'

export default {
  name: 'MetaAnnotationTaskContainer',
  components: {
    MetaAnnotationTask
  },
  mixins: [MetaAnnotationService],
  props: {
    taskIDs: Array,
    selectedEnt: {
      type: Object,
      default () {
        return {}
      }
    }
  },
  data () {
    return {
      tasks: Array
    }
  },
  methods: {
    selectedTaskAnno (task, option) {
      if (task.value === option.id) {
        // remove annotation
        this.$http.delete(`/api/meta-annotations/${task.annotation_id}/`).then(() => {
          task.value = null
          task.annotation_id = null
        })
      } else if (task.value && task.value !== option.id) {
        // update
        let payload = {
          validated: !this.selectedEnt.deleted && !this.selectedEnt.alternative,
          annotated_entity: this.selectedEnt.id,
          meta_task: task.id,
          meta_task_value: option.id
        }
        this.$http.put(`/api/meta-annotations/${task.annotation_id}/`, payload).then(() => {
          task.value = option.id
        })
      } else {
        // create new
        const payload = {
          validated: !this.selectedEnt.deleted && !this.selectedEnt.alternative,
          annotated_entity: this.selectedEnt.id,
          meta_task: task.id,
          meta_task_value: option.id
        }
        this.$http.post(`/api/meta-annotations/`, payload).then((resp) => {
          task.annotation_id = resp.data.id
          task.value = resp.data.meta_task_value
        })
      }
    }
  },
  created () {
    const that = this
    this.fetchMetaTasks(this.taskIDs, () => {
      if (that.selectedEnt) {
        that.fetchMetaAnnotations(that.selectedEnt)
      }
    })
  },
  watch: {
    'taskIDs': 'fetchMetaTasks',
    'selectedEnt': 'fetchMetaAnnotations'
  }
}
</script>

<style scoped lang="scss">
.task-list {
  height: 250px;
  overflow-y: auto;
}
</style>
