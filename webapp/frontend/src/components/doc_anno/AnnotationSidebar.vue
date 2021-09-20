<template>
  <div @mousedown.stop>
    <div class="title">Document Annotations</div>
    <div class="available-doc-annos">
      <div class="doc-anno-entry" v-for="annoTask of clfTasks" :key="annoTask.id"
           :class="{'selected-doc-anno-task': annoTask.id === (selectedAnnoValue || {}).doc_anno_task}">
        <div>
          <div class="task-name doc-anno-title">{{annoTask.name}}</div>
          <div class="task-description doc-anno-description">{{annoTask.description}}</div>
          <div class="task-values-container">
            <button @click.stop.prevent v-for="label of annoTask.labels" :key="label" class="btn btn-outline-primary task-value"
                    :class="{'selected': isSelectedTask(annoTask, label)}"
                    @click="selectDocClassLabel(annoTask, label)">{{(clsLabelsIdtoVals[label] || {}).label}}
              <font-awesome-icon @click.stop icon="check-square" class="select-annos-icon"
                                 :class="{'is-selected-annos-icon': isLabelSelected(annoTask, label)}"
                                 v-if="isSelectedTask(annoTask, label)"
                                 @click="selectDocAnnoValue(annoTask, label)"></font-awesome-icon>
            </button>
          </div>
        </div>
      </div>
      <div @click.stop.prevent @click="selectDocRegTask(annoTask)" class="doc-anno-entry"
           :class="{'selected-doc-anno-task': annoTask.id === (selectedAnnoValue || {}).doc_anno_task}" v-for="annoTask of regTasks" :key="annoTask.id">
        <div>
          <div class="task-name doc-anno-title">{{annoTask.name}}</div>
          <div class="task-description doc-anno-description">{{annoTask.description}}</div>
          <div @keyup.stop  class="reg-value-entry">
            <input :class="{'is-invalid': isInvalid(annoTask)}" @keyup="updateRegvalue(annoTask, [])" class="form-control"
                   type="text" v-model="regTaskIdsToVals[annoTask.id]">
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import _ from 'lodash'

export default {
  name: 'DocumentAnnotationSidebar',
  props: {
    clfTasks: null,
    regTasks: null,
    clfValues: null,
    regValues: null,
    selectedAnnoValue: null
  },
  data () {
    return {
      clsLabelsIdtoVals: {},
      regTaskIdsToVals: {}
    }
  },
  methods: {
    fetchClfTaskValues () {
      const taskVals = _.uniq(_.flatten(this.clfTasks.map(t => t.labels)))
      if (taskVals.length > 0) {
        this.$http.get(`/api/document-annotation-cls-labels/`).then(resp => {
          const clsVals = resp.data.results.filter(r => taskVals.indexOf(r.id) !== -1)
          for (const val of clsVals) {
            this.$set(this.clsLabelsIdtoVals, val.id, val)
          }
          if (!this.selectedAnnoValue && this.clfTasks.length > 0 &&
            !_.isEmpty(this.clsLabelsIdtoVals.length > 0)) {
            this.selectDocClassLabel(this.clfTasks.filter(t => t.id === clsVals[0].doc_anno_task), clsVals[0])
          }
        })
      }
    },
    selectDocClassLabel (task, label) {
      this.$emit('selected:class', task, label, !this.isSelectedTask(task, label))
    },
    updateRegvalue: _.debounce(function (task) {
      if (!this.isInvalid(task)) {
        const existingVal = this.regValues.filter(v => v.id === task.id)
        if (existingVal.length > 0) {
          this.$emit('updated:regTaskValue', existingVal[0])
        } else {
          const value = Number(this.regTaskIdsToVals[task.id])
          this.$emit('create:regTaskValue', task, value)
        }
      }
    }, 500),
    isSelectedTask (task, label) {
      return this.clfValues.filter(v => {
        return v.doc_anno_task === task.id && v.doc_anno_value === label
      }).length > 0
    },
    isInvalid (annoTask) {
      const value = Number(this.regTaskIdsToVals[annoTask.id])
      if (_.isFinite(value)) {
        if (annoTask.minimum && value < annoTask.minimum) {
          return true
        }
        return (annoTask.maximum && value > annoTask.maximum)
      }
      return true
    },
    selectDocAnnoValue (task, label) {
      const annoValue = this.clfValues.filter(v => {
        return v.doc_anno_task === task.id && v.doc_anno_value === label
      })[0]
      if (this.selectedAnnoValue !== annoValue) {
        this.$emit('changed:selectedAnnoValue', annoValue)
      }
    },
    selectDocRegTask (task) {
      const regValue = this.regValues.filter(v => v.doc_anno_task === task.id)
      if (regValue.length > 0) {
        const newVal = regValue[0]
        this.$emit('changed:selectedAnnoValue', newVal)
      }
    },
    isLabelSelected (task, label) {
      return (this.selectedAnnoValue || {}).doc_anno_value === (this.clsLabelsIdtoVals[label] || {}).id &&
        (this.selectedAnnoValue || {}).doc_anno_task === task.id
    }
  },
  watch: {
    clfTasks: 'fetchClfTaskValues',
    regValues (vals) {
      this.regTaskIdsToVals = Object.fromEntries(new Map(vals.map(v => [v.doc_anno_task, v.doc_anno_value])))
    }
  }
}
</script>

<style scoped lang="scss">
.available-doc-annos {
  overflow-y: auto;
}

.doc-anno-entry {
  padding: 10px;
}

.doc-anno-title {
   width: 225px;
}

.doc-anno-description {
  width: calc(100% - 225px);
}

.selected-doc-anno-task {
  border: 1px solid $task-color-0;
  border-radius: 7px;
}

.select-annos-icon {
  opacity: 0.2;
  &:hover {
    opacity: 1;
  }
}

.is-selected-annos-icon {
  opacity: 1;
}

</style>
