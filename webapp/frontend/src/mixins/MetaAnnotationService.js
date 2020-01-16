
import _ from 'lodash'

export default {
  name: 'MetaAnnotationService',
  data: function () {
    return {
      tasks: Array
    }
  },
  methods: {
    fetchMetaTasks: function (taskIDs, callback) {
      this.$http.get(`/api/meta-tasks/`).then(resp => {
        let tasks = resp.data.results.filter(r => {
          return taskIDs.includes(r.id)
        })
        let values = _.flatten(tasks.map(t => t.values))
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
          callback()
        })
      })
    },
    fetchMetaAnnotations: function (selectedEnt, callback) {
      if (this.tasks && selectedEnt !== null) {
        for (let t of this.tasks) {
          t.value = null
        }
        this.$http.get(`/api/meta-annotations/?annotated_entity=${selectedEnt.id}`).then(resp => {
          // map current state tasks to these entities - to delete as needed.
          for (let r of resp.data.results) {
            let task = this.tasks.filter(t => t.id === r.meta_task)[0]
            task.value = r.meta_task_value
            task.annotation_id = r.id
            if (callback) {
              callback()
            }
          }
        })
      }
    }
  }
}
