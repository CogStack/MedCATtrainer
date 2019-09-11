<template>
  <div class="task-bar border-top border-left">
    <div class="task-bar-task border-bottom">
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
}

.task-bar-choices {
  padding: 5px;
}

.task-name {
  font-weight: bold;
  font-size: 22px;
}

.task-btn-0 {
  background-color: $task-color-0;
  color: white;
}

.task-btn-1 {
  background-color: $task-color-1;
  color: white;
}

.task-btn-2 {
  background-color: $task-color-2;
  color: white;
}

.task-btn-3 {
  background-color: $task-color-3;
  color: white;
}

.task-btn-4 {
  background-color: $task-color-4;
  color: white;
}

.task-btn-5 {
  background-color: $task-color-5;
}
</style>
