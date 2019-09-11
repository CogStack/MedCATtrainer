<template>
  <div class="mb-2 border-top border-right app-sidebar">
    <div v-if="text && text.length > 0">
      <table class="table table-striped table-hover">
        <thead>
        <tr>
          <th>Text Span</th>
          <th>CUI</th>
          <th>Accuracy</th>
          <th v-for="task in tasks">{{task.taskName}}</th>
        </tr>
        </thead>
        <tbody>
        <tr @click="selectItem(item)"
            :class="{'bg-primary': index === spanIdx, 'text-white': index === spanIdx}"
            v-for="(item, index) in items">
          <td>{{text.slice(item.start_ind, item.end_ind)}}</td>
          <td>{{item.cui}}</td>
          <td>{{parseFloat(item.acc).toFixed(2)}}</td>
          <td v-for="task in tasks">{{taskValue(task, item)}}</td>
        </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>

export default {
  name: 'SideBar',
  props: {
    text: String,
    items: Array,
    tasks: Array,
    taskIdx: Number,
    spanIdx: Number,
    selectItem: Function,
  },
  computed: {
    taskValues: function() {
      let mappedTasks = {};
      for(let task of this.tasks) {
        let mappedVals = {};
        for(let val of task.values) {
          mappedVals[val[1]] = val[0]
        }
        mappedTasks[task.taskName] = mappedVals;
      }
      return mappedTasks;
    },
  },
  methods: {
    taskValue: function(task, item) {
      let spanTaskVal = task.taskName in item.taskLabels ? item.taskLabels[task.taskName] : 'n/a';
      return spanTaskVal !== 'n/a' ? this.taskValues[task.taskName][spanTaskVal] : 'n/a';
    }
  }
}
</script>

<style scoped lang="scss">
.app-sidebar {
  flex: 0 0 300px;
  overflow: auto;

  table {
    font-size: 10pt;
    cursor: pointer;
  }
}
</style>
