<template>
  <div class="task-bar" >
    <div class="task-bar-choices">
      <button :disabled="taskLocked" class="btn task-btn-0" @click="correct">
        Correct</button>
      <button :disabled="taskLocked" class="btn task-btn-1" @click="remove">
        Incorrect</button>
      <button :disabled="taskLocked" class="btn task-btn-2" @click="kill">
        Terminate</button>
        <button :disabled="taskLocked" class="btn task-btn-3" @click="alternative">
          Alternative</button>
    </div>
    <button :disabled="submitDisabled()" @click="submit()" class="btn btn-outline-primary mb-2 submit-btn submit"
              type="button">Submit</button>
  </div>
</template>

<script>
import _ from 'lodash'

export default {
  name: 'TaskBar',
  props: {
    ents: Array,
    taskLocked: Boolean,
    submitLocked: Boolean,
    altSearch: Boolean
  },
  methods: {
    correct: function () {
      this.$emit('select:correct')
    },
    remove: function () {
      this.$emit('select:remove')
    },
    kill: function () {
      this.$emit('select:kill')
    },
    alternative: function () {
      this.$emit('select:alternative', !this.altSearch)
    },
    submit: function () {
      this.$emit('submit', true)
    },
    submitDisabled: function () {
      if (this.ents !== null && !this.submitLocked) {
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
      } else if (e.keyCode >= 49 && e.keyCode < 53 && !this.taskLocked) {
        let codeRange = _.range(4)
        let keyRange = _.range(49, 53)
        let selectIdx = _.zipObject(keyRange, codeRange)[e.keyCode]
        switch (selectIdx) {
          case 0:
            this.correct()
            break
          case 1:
            this.remove()
            break
          case 2:
            this.kill()
            break
          case 3:
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
  text-align: center;

  .task-bar-choices {
    width: calc(100% - 100px);
  }

  div {
    display: inline-block;
  }

  .submit {
    float: right;
    width: 100px
  }
}
</style>
