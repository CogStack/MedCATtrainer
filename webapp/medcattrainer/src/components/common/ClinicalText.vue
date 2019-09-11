<template>
  <div class="note-container border-bottom">
    <transition name="fade">
      <div v-if="loading" class="loading">
        <div class="spinner">
          <font-awesome-icon icon="spinner" size="1x" spin></font-awesome-icon>
        </div>
      </div>
    </transition>
    <div v-if="!loading" class="clinical-note">
      <v-runtime-template :template="formattedText"></v-runtime-template>
    </div>
  </div>
</template>

<script>
import $ from 'jquery'
import VRuntimeTemplate from 'v-runtime-template'

export default {
  name: 'ClinicalText',
  components: {
    VRuntimeTemplate,
  },
  props: {
    text: String,
    task: Object,
    ents: Array,
    loading: true,
    currentEnt: Object,
  },
  computed: {
    formattedText: function() {
      if (this.loading || !this.text || !this.ents || this.ents.length === 0)
        return "";
      // const taskValuesToTasks = Object.assign(...this.task.values.map(([key, val]) => ({[val]: key})));
      const taskValueNamesToButtonIndices = Object.assign(...this.task.values.map((val, i) =>  ({[val[0]]: i})));
      const taskHighlightDefault = 'highlight-task-default';

      let formattedText = '';
      let start = 0;

      this.text = this.text.replace('<', '\<')
        .replace('>', '\>')
        .replace('[', '\[')
        .replace(']', '\]');
      for (let i = 0; i < this.ents.length; i++) {
        // highlight the span with default
        let highlightText = this.text.slice(this.ents[i].start_ind, this.ents[i].end_ind);
        let styleClass = taskHighlightDefault;

        if (this.ents[i].assignedValues[this.task.name]) {
          let btnIndex = taskValueNamesToButtonIndices[this.ents[i].assignedValues[this.task.name]];
          styleClass = `highlight-task-${btnIndex}`;
        }

        styleClass = this.ents[i] === this.currentEnt ? `${styleClass} highlight-task-selected` : styleClass
        let spanText = `<span @click="selectEnt(${i})" class="${styleClass}">${highlightText}</span>`;
        let precedingText = this.text.slice(start, this.ents[i].start_ind);
        precedingText = precedingText.length !== 0 ? precedingText : ' ';
        start = this.ents[i].end_ind;
        formattedText += precedingText + spanText;
        if (i === this.ents.length -1 )
          formattedText += this.text.slice(start, this.text.length - 1);
      }

      let el = $('<div></div>');
      el.html(formattedText);
      // strip all plain text HTML that may be malformed and only leave the <span> els we've included.
      $(":not(*[class^='highlight-task'])",  el).remove();
      formattedText = el.html();

      formattedText = `<div>${formattedText}</div>`;
      return formattedText ;
    }
  },
  updated: function() {
    this.$nextTick(function () {
      let el = document.getElementsByClassName('highlight-task-selected');
      if (el[0]) {
        el[0].scrollIntoView({
          block: "center",
          behavior: "smooth",
        });
      }
    });
  },
  methods: {
    selectEnt: function(entIdx) {
      this.$emit('select:concept', entIdx)
    },
  },
}
</script>

<style lang="scss">
.note-container {
  overflow: scroll;
  flex: 1 1 auto;
}

.loading {
  background: $loading-background-color;
  opacity: 0.3;
  height: 100%;
  position: relative;

  .spinner {
    position: absolute;
    top: 50%;
    left: 50%;
    font-size: 64px;
  }
}

.fade-enter-active, .fade-leave-active {
  transition: opacity .3s;
}

.fade-enter, .fade-leave-to {
  opacity: 0;
}

.clinical-note {
  padding: 5px;
  white-space: pre-wrap;
}

.highlight-task-default {
  background: lightgrey;
  border: 3px solid lightgrey;
  border-radius: 8px;
  cursor: pointer;
}

.highlight-task-selected {
  font-size: 20px;
  font-weight: bold;
}

@each $i, $col in $task-colors {
  .highlight-task-#{$i} {
    background-color: $col;
    border-radius: 8px;
    cursor: pointer;
    border: 3px solid $col;
    color: white;
  }
}

/*
<!--.highlight-task-0 {-->
  <!--box-shadow: 0 0 10px 5px $task-color-0;-->
  <!--border-radius: 5px;-->
<!--}-->

<!--.highlight-task-1 {-->
  <!--box-shadow: 0 0 10px 5px $task-color-1;-->
  <!--border-radius: 5px;-->
<!--}-->

<!--.highlight-task-2 {-->
  <!--box-shadow: 0 0 10px 5px $task-color-2;-->
  <!--border-radius: 5px;-->
<!--}-->

<!--.highlight-task-3 {-->
  <!--box-shadow: 0 0 10px 5px $task-color-3;-->
  <!--border-radius: 5px;-->
<!--}-->

<!--.highlight-task-4 {-->
  <!--box-shadow: 0 0 10px 5px $task-color-4;-->
  <!--border-radius: 5px;-->
<!--}-->

<!--.highlight-task-5 {-->
  <!--box-shadow: 0 0 10px 5px $task-color-5;-->
  <!--border-radius: 5px;-->
<!--}-->
*/
</style>
