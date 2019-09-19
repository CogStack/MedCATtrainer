<template>
  <div class="task-bar">
    <div class="task-bar-task">
      Task: <span class="task-name">{{currentTask.name}}</span>
    </div>
    <div class="task-bar-choices">
        <span v-for="(val, index) of currentTask.values">
          <button :disabled="taskLocked" :class="'btn task-btn-' + index"
                   @click="select(val)"> {{ val[0] }}
          </button>
        </span>
    </div>
  </div>
</template>

<script>
import _ from 'lodash'

export default {
  name: 'TaskBar',
  props: {
    tasks: Array,
    taskLocked: Boolean,
    currentTask: Object,
  },
  methods: {
    select: function(val) {
      this.$emit('select:taskValue', val)
    },
    keyup: function(e) {
      // 1-9 select a value
      if (e.keyCode >= 49 && e.keyCode <= 57 && !this.taskLocked) {
        let codeRange = _.range(10);
        let keyRange = _.range(49, 58);
        let selectIdx = _.zipObject(keyRange, codeRange)[e.keyCode];
        if (selectIdx <= this.currentTask.values.length)
          this.$emit('select:taskValue', this.currentTask.values[selectIdx])
      }
    },
  },
  mounted: function() {
    window.addEventListener('keyup', this.keyup)
  },
  beforeDestroy: function() {
    window.removeEventListener('keyup', this.keyup)
  }
}
</script>

<style scoped lang="scss">
.task-bar {
  width: 100%;
  text-align: center;
  padding: 5px;
  background-color: $background;
  color: $text;
}

.task-bar-choices {
  padding: 5px;
}

.task-name {
  font-weight: bold;
  font-size: 22px;
  color: $text-highlight;
}

@each $i, $col in $task-colors {
  .task-btn-#{$i} {
    background-color: $col;
    color: white;
  }
}
</style>
