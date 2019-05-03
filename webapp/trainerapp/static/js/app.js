Vue.component('clinical-text', {
  props: ['text', 'span', 'task'],
  computed: {
    formattedText: function() {
      let taskHighlight = 'highlight-task-default';
      if (this.task.taskName in this.span.taskLabels) {
        taskHighlight = 'highlight-task-' + this.span.taskLabels[this.task.taskName];
      }
      let highlightText = this.text.slice(this.span.start_ind, this.span.end_ind);
      let formattedTxt = `<span id="focusSpan" class="${taskHighlight}">${highlightText}</span>`;
      formattedTxt = this.text.slice(0, this.span.start_ind) + formattedTxt +
          this.text.slice(this.span.end_ind, this.text.length);
      return formattedTxt;
    }
  },
  updated: function() {
    this.$nextTick(function () {
      document.getElementById('focusSpan').scrollIntoView({
        block: "center",
        behavior: "smooth",
      });
    });
  },
  template: `
    <div class="note-container">
      <p class="clinical-note" v-html="formattedText"></p>
    </div>
  `
});

Vue.component('sidebar', {
  props: ['text', 'items', 'tasks', 'taskIdx', 'spanIdx'],
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
  },
  template: `
    <div class="mb-2 border-top border-right app-sidebar">
      <div v-if="text.length > 0">
        <table class="table table-striped">
          <thead>
            <tr>
              <th>Text Span</th>
              <th v-for="task in tasks">{{task.taskName}}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(item, index) in items">
              <td>{{text.slice(item.start_ind, item.end_ind)}}</td>
              <td v-for="task in tasks">{{taskValue(task, item)}}</td>
            </tr>
          </tbody>
        </table>
        </div>
      </div>
    </div>
  `
});

Vue.component('taskBar', {
  props: ['tasks', 'currentTask', 'select'],
  template: `
    <div class="task-bar col-sm-6 border-top border-right" style="text-align: center">
      <div class="row">
        <div class="col-sm-3">
        Task: <span>{{currentTask.taskName}}</span>
      </div>
      <div class="col-sm-9">
        <span v-for="(val, index) of currentTask.values">
          <button  :class="'btn task-btn-' + index"
                @click="select(val[1])"> {{ val[0] }}
          </button>
        </span>
      </div>
      </div>
    </div>
  `
});

Vue.component('navBar', {
  props: ['tasksComplete', 'current', 'totalTasks', 'totalSpans', 'next', 'back', 'submit'],
  methods: {
    nextDisabled: function() {
      return this.current.spanIndex === (this.totalSpans - 1)  &&
          this.current.taskIndex === (this.totalTasks - 1);
    },
    backDisabled: function() {
      return this.current.spanIndex === 0 && this.current.taskIndex === 0
    }
  },
  template: `
    <div class="nav-bar col-sm-6 border-top">
      <button :disabled="backDisabled()" @click="back" type="button" class="btn btn-warning mb-2">
        <i class="fas fa-backward"></i>
      </button>
      <button :disabled="nextDisabled()"  @click="next" type="button" class="btn btn-warning mb-2">
        <i class="fas fa-forward"></i>
      </button> 
      <button :disabled="!tasksComplete" @click.prevent="submit" class="btn btn-primary mb-2" type="button" 
      style="float: right;">Submit</button>
    </div>
  `
});


let trainData = taskTrainingData();

let data = {
  items: [],
  text: trainData.data.text,
  current: {
    spanIndex: 0,
    taskIndex: 0,
    span: null,
    task: {
      values: []
    },
  },
  tasksComplete: true,  // Is this needed?
  tasks: []
};

data.tasks = _.pairs(trainData.tasks).map((task) => {
  return {
    taskName: task[0],
    values: task[1]
  };
});


data.items = trainData.data.entities.map(i => {
  let item = {};
  Object.assign(item, i);
  item.taskLabels = {}; // one per task?
  return item;
});

data.current.span =  data.items[0];
data.current.task = data.tasks[0];

let next = function() {
  let taskIndex = data.current.taskIndex;
  let spanIndex = data.current.spanIndex;
  if (taskIndex < data.tasks.length - 1) {
    data.current.taskIndex++;
    data.current.task = data.tasks[data.current.taskIndex];
  } else if (spanIndex < data.items.length-1) {
    data.current.spanIndex++;
    data.current.span = data.items[data.current.spanIndex];
    data.current.taskIndex = 0;
    data.current.task = data.tasks[0];
  } else
    console.error('Cannot proceed to next element that does not exist');
};

let back = function() {
  let taskIndex = data.current.taskIndex;
  let spanIndex = data.current.spanIndex;
  if (taskIndex > 0) {
    data.current.taskIndex--;
    data.current.task = data.tasks[data.current.taskIndex];
  } else if (spanIndex > 0) {
    data.current.spanIndex--;
    data.current.span = data.items[data.current.spanIndex];
  } else
    console.log('Cannot proceed to next element.');
};


let app = new Vue({
  el: '#app',
  data: data,
  methods: {
    select: function (val) {
      app.$set(data.current.span.taskLabels, data.current.task.taskName, val);
      if (!(data.current.spanIndex === (data.items.length - 1)  &&
          data.current.taskIndex === (data.tasks.length - 1)))
        next()
    },
    next: next,
    back: back,
    submit: function () {
      let payload = taskTrainingData().data;
      // collate task labels per span and set within the entity object.
      payload.entities = payload.entities.map((e) => {
        return Object.assign(e, e.taskLabels)
      });
      this.$http.post('/save', payload);
    }
  }
});





