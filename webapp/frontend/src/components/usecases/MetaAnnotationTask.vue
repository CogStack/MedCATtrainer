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
    selectTaskValue (option) {
      this.$emit('select:metaAnno', this.task, option)
    }
  }
}
</script>

<style scoped lang="scss">

</style>
