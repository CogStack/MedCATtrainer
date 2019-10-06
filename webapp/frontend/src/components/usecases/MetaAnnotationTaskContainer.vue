<template>
  <div v-if="tasks && tasks.length > 0">
    <div class="title">Meta Annotation Tasks</div>
    <div v-for="task of tasks" :key="task.id">
      <meta-annotation-task @select:metaAnno="selectedTaskAnno" :task="task"></meta-annotation-task>
    </div>
  </div>
</template>

<script>
import MetaAnnotationTask from '@/components/usecases/MetaAnnotationTask.vue'

export default {
  name: 'MetaAnnotationTaskContainer',
  components: {
    MetaAnnotationTask
  },
  props: {
    taskIDs: Array,
    selectedEnt: {
      type: Object,
      default: function () {
        return {}
      }
    }
  },
  data: function () {
    return {
      tasks: Array
    }
  },
  methods: {
    fetchMetaTasks: function () {
      this.$http.get(`/api/meta-tasks/`).then(resp => {
        let tasks = resp.data.results.filter(r => {
          return this.taskIDs.includes(r.id)
        })
        let values = tasks.map(t => t.values).flat()
        this.$http.get(`/api/meta-task-values/`).then(resp => {
          let taskValueObjs = resp.data.results.filter(r => values.includes(r.id))
          let taskValObjMap = {}
          for (const valId of values) {
            taskValObjMap[valId] = taskValueObjs.filter(o => o.id === valId)[0]
          }
          tasks = tasks.map(t => {
            t.options = t.values.map(val => taskValObjMap[val])
            t.value = null
            delete t['values']
            return t
          })
          this.tasks = tasks
          this.fetchMetaAnnotations()
        })
      })
    },
    fetchMetaAnnotations: function () {
      if (this.tasks && this.selectedEnt !== null) {
        for (let t of this.tasks) {
          t.value = null
        }
        this.$http.get(`/api/meta-annotations/?annotated_entity=${this.selectedEnt.id}`).then(resp => {
          // map current state tasks to these entities - to delete as needed.
          for (let r of resp.data.results) {
            let task = this.tasks.filter(t => t.id === r.meta_task)[0]
            task.value = r.meta_task_value
            task.annotation_id = r.id
          }
        })
      }
    },
    selectedTaskAnno: function (task, option) {
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
  created: function () {
    this.fetchMetaTasks()
  },
  watch: {
    'taskIDs': 'fetchMetaTasks',
    'selectedEnt': 'fetchMetaAnnotations'
  }
}
</script>

<style scoped lang="scss">
</style>
