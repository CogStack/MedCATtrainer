<template>
  <div class="task-bar">
    <div class="task-bar-task">
      <span class="task-name">Concept Annotation</span>
    </div>
    <div class="task-bar-choices">
      <span>
        <button :disabled="taskLocked" class="btn task-btn-0" @click="correct">
          Correct</button>
      </span>
      <span>
        <button :disabled="taskLocked" class="btn task-btn-1" @click="remove">
          Remove</button>
      </span>
      <span>
        <button :disabled="taskLocked" class="btn task-btn-2" @click="alternative">
          Alternative Concept</button>
      </span>
    </div>
  </div>
</template>

<script>
import _ from 'lodash'

export default {
  name: 'TaskBar',
  props: {
    taskLocked: Boolean,
    altSearch: Boolean
  },
  methods: {
    correct: function () {
      this.$emit('select:correct')
    },
    remove: function () {
      this.$emit('select:remove')
    },
    alternative: function () {
      this.$emit('select:alternative', !this.altSearch)
    },
    keyup: function (e) {
      // 1-3 select a value
      if (e.keyCode >= 49 && e.keyCode <= 51 && !this.taskLocked) {
        let codeRange = _.range(3)
        let keyRange = _.range(49, 52)
        let selectIdx = _.zipObject(keyRange, codeRange)[e.keyCode]
        switch (selectIdx) {
          case 0:
            this.correct()
            break
          case 1:
            this.remove()
            break
          case 2:
            this.alternative()
        }
      }
    }
  },
  mounted: function () {
    window.addEventListener('keyup', this.keyup)
  },
  beforeDestroy: function () {
    window.removeEventListener('keyup', this.keyup)
  }
}
</script>

<style scoped lang="scss">
.task-bar {
  width: 100%;
  text-align: center;
  padding-top: 5px;
  padding-bottom: 30px;
  background-color: $background;
  color: $text;
}

.task-bar-choices {
  padding: 5px;
}

.task-name {
  font-size: 22px;
}
</style>
