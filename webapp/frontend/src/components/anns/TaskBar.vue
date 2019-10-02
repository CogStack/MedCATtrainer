<template>
  <div class="task-bar">
    <!--<div class="task-bar-task">-->
      <!--<span class="task-name">Concept Annotation</span>-->
    <!--</div>-->
    <div class="task-bar-choices">
      <span>
        <button :disabled="taskLocked" class="btn task-btn-0" @click="correct">
          Correct</button>
      </span>
      <span>
        <button :disabled="taskLocked" class="btn task-btn-1" @click="remove">
          Wrong</button>
      </span>
      <span>
        <button :disabled="taskLocked" class="btn task-btn-2" @click="alternative">
          Alternative Concept</button>
      </span>
    </div>
    <div class="submit">
      <button :disabled="submitDisabled()" @click="submit()" class="btn btn-outline-primary mb-2 submit-btn" type="button">
        Submit
      </button>
    </div>
  </div>
</template>

<script>
import _ from 'lodash'

export default {
  name: 'TaskBar',
  props: {
    ents: Array,
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
    submit: function () {
      this.$emit('submit', true)
    },
    submitDisabled: function () {
      if (this.ents !== null) {
        return !this.ents.every(e => {
          return Object.values(e.assignedValues).every(e => e !== null)
        })
      }
      return true
    },
    keyup: function (e) {
      if (e.keyCode === 13) {
        if (!this.submitDisabled()) {
          this.submit()
        }
      } else if (e.keyCode >= 49 && e.keyCode <= 51 && !this.taskLocked) {
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
  padding: 5px 0;
  background-color: $background;
  color: $text;

  div {
    display: inline-block;
  }

  .submit {
    float: right;
  }
}
</style>
