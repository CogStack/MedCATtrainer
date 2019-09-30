<template>
  <div class="note-container">
    <transition name="fade">
      <div v-if="loading" class="loading">
        <div class="spinner">
          <font-awesome-icon icon="spinner" size="1x" spin></font-awesome-icon>
        </div>
      </div>
    </transition>
    <div v-if="!loading" class="clinical-note">
      <v-runtime-template ref="clinicalText" :template="formattedText"></v-runtime-template>
    </div>
    <vue-simple-context-menu
      :elementId="'ctxMenuId'"
      :options="ctxMenuOptions"
      ref="ctxMenu"
      @option-clicked="ctxOptionClicked">
    </vue-simple-context-menu>
  </div>
</template>

<script>
import _ from 'lodash'
import VRuntimeTemplate from 'v-runtime-template'
import VueSimpleContextMenu from 'vue-simple-context-menu'

export default {
  name: 'ClinicalText',
  components: {
    VRuntimeTemplate,
    VueSimpleContextMenu
  },
  props: {
    text: String,
    taskName: String,
    taskValues: Array,
    task: Object,
    ents: Array,
    loading: Boolean,
    currentEnt: Object
  },
  data: function () {
    return {
      ctxMenuOptions: [
        {
          name: 'Add Synonym'
        }
      ],
      selection: null
    }
  },
  computed: {
    formattedText: function () {
      if (this.loading || !this.text || !this.ents) { return '' }
      if (this.ents.length === 0) {
        let text = this.text.replace('&', '&amp').replace('<', '&gt').replace('>', '&gt')
        return `<div @contextmenu.prevent.stop="showCtxMenu($event)">${text === 'nan' ? '' : text}</div>`
      }

      const taskHighlightDefault = 'highlight-task-default'
      let formattedText = ''
      let start = 0
      let timeout = 0
      for (let i = 0; i < this.ents.length; i++) {
        // highlight the span with default
        let highlightText = this.text.slice(this.ents[i].start_ind, this.ents[i].end_ind)
        let styleClass = taskHighlightDefault
        if (this.ents[i].assignedValues[this.taskName] !== null) {
          let btnIndex = this.taskValues.indexOf(this.ents[i].assignedValues[this.taskName])
          styleClass = `highlight-task-${btnIndex}`
        }

        styleClass = this.ents[i] === this.currentEnt ? `${styleClass} highlight-task-selected` : styleClass
        timeout = this.ents[i] === this.currentEnt && i === 0 ? 500 : timeout
        let spanText = `<span @click="selectEnt(${i})" class="${styleClass}">${highlightText}</span>`
        let precedingText = this.text.slice(start, this.ents[i].start_ind)
        precedingText = precedingText.length !== 0 ? precedingText : ' '
        start = this.ents[i].end_ind
        formattedText += precedingText + spanText
        if (i === this.ents.length - 1) {
          formattedText += this.text.slice(start, this.text.length - 1)
        }
      }
      formattedText = formattedText
        .replace(/<(?!span)/g, '&lt')
        .replace(/&lt(?=\/span>)/g, '<')
        .replace(/(?<!")>/g, '&gt')
        .replace(/(?<=<\/span)&gt/g, '>')
      formattedText = `<div @contextmenu.prevent.stop="showCtxMenu($event)">${formattedText}</div>`

      this.scrollIntoView(timeout)
      return formattedText
    }
  },
  methods: {
    scrollIntoView: function (timeout) {
      let el = document.getElementsByClassName('highlight-task-selected')
      setTimeout(function () { // setTimeout to put this into event queue
        if (el[0]) {
          el[0].scrollIntoView({
            block: 'center',
            behavior: 'smooth'
          })
        }
      }, timeout)
    },
    selectEnt: function (entIdx) {
      this.$emit('select:concept', entIdx)
    },
    showCtxMenu: function (event) {
      let selection = window.getSelection()
      let selStr = selection.toString()
      // gather text around selection
      let priorText = selection.anchorNode.data.slice(0, selection.anchorOffset)
      let nextText = selection.extentNode.data.slice(selection.extentOffset)

      let priorSibling = selection.anchorNode.previousSibling
      let nextSibling = selection.anchorNode.nextSibling
      _.range(3).forEach(function () {
        if (priorSibling !== null) {
          priorText = `${priorSibling.innerText || priorSibling.textContent}${priorText}`
          priorSibling = priorSibling.previousSibling
        }
        if (nextSibling !== null) {
          nextText += (nextSibling.innerText || nextSibling.textContent)
          nextSibling = nextSibling.nextSibling
        }
      })
      // take only 100 chars of either side?
      nextText = nextText.length < 100 ? nextText : nextText.slice(0, 100)
      priorText = priorText.length < 15 ? priorText : priorText.slice(-15)
      this.selection = {
        selStr: selStr,
        prevText: priorText,
        nextText: nextText
      }
      this.$refs.ctxMenu.showMenu(event)
    },
    ctxOptionClicked: function (event) {
      this.$emit('select:addSynonym', this.selection)
    }
  }
}
</script>

<style lang="scss">

.note-container {
  flex: 1 1 auto;
  overflow-y: auto;
  background: rgba(0, 114, 206, .2);
  padding: 75px 75px 0 75px;
  border-radius: 10px;
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
  background: white;
  overflow: scroll;
  height: 100%;
  box-shadow: 0px -2px 3px 2px rgba(0,0,0,0.2);
  padding: 25px;
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
</style>
