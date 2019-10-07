<template>
  <div>
    <div class="task-name">{{task.name}}</div>
    <div class="task-description">{{task.description}}</div>
    <div class="task-values-container">
      <button class="btn btn-outline-primary task-value" :class="{'selected': task.value === option.id}"
              v-for="option of task.options" :key="option.id"
              @click="selectTaskValue(option)">{{option.name}}</button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'MetaAnnotationTask',
  props: {
    task: Object
  },
  methods: {
    selectTaskValue: function (option) {
      this.$emit('select:metaAnno', this.task, option)
    }
  }
}
</script>

<style scoped lang="scss">
.task-name {
  font-size: 16px;
  padding: 10px 15px 5px 15px;
  display: inline-block;
  width: 125px;
}

.task-description {
  font-size: 12px;
  padding: 10px 15px 5px 15px;
  display: inline-block;
  width: calc(100% - 125px);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.selected {
  color: #fff;
  background-color: #005EB8;
  border-color: #005EB8;
}

.task-values-container {
  padding: 0 15px 10px 15px;
  display: flex;
  flex-direction: row;
  box-shadow: 0 5px 5px -5px rgba(0,0,0,0.2);

  .task-value {
    flex: 1 1 auto;
  }
}
</style>
