<template>
  <div class="task-bar">
    <div class="task-bar-task">
      <span class="task-name">Concept Annotation</span>
    </div>
    <div class="task-bar-choices">
      <span>
        <button :disabled="taskLocked" class="btn task-btn-0" @click="correct">
          Correct</button>
      </span>
      <span>
        <button :disabled="taskLocked" class="btn task-btn-1" @click="remove">
          Remove</button>
      </span>
      <span>
        <button :disabled="taskLocked" class="btn task-btn-1" @click="alternative">
          Alternative Concept</button>
      </span>
      <div class="alt-concept-picker" @keyup.stop>
        <v-select class="picker" v-if="altSearch" v-model="selectedCUI" label="name" @search="searchCUI" :options="searchResults"></v-select>
        <font-awesome-icon class="cancel" v-if="altSearch" icon="times-circle" @click="cancelReassign"></font-awesome-icon>
      </div>
    </div>
  </div>
</template>

<script>
import _ from 'lodash'
import vSelect from 'vue-select'

export default {
  name: 'TaskBar',
  components: {
    vSelect
  },
  props: {
    taskLocked: Boolean
  },
  data: function () {
    return {
      altSearch: false,
      searchResults: [],
      selectedCUI: null
    }
  },
  methods: {
    correct: function () {
      this.$emit('select:correct')
    },
    remove: function () {
      this.$emit('select:remove')
    },
    alternative: function () {
      this.altSearch = !this.altSearch
    },
    searchCUI: _.debounce(function (term, loading) {
      loading(true)
      this.$http.get(`/api/search-concepts/?search=${term}&projectId=${this.projectId}`)
        .then(resp => {
          loading(false)
          this.searchResults = resp.data.results.map(r => {
            return {
              name: r.pretty_name,
              cui: r.cui,
              desc: r.desc,
              synonyms: _.replace(r.synonyms, new RegExp(',', 'g'), ', ')
            }
          })
        })
    }, 400),
    selectedCorrectCUI: function (item) {
      if (item) {
        this.$emit('select:alternative', item)
        this.altSearch = false
        this.searchResults = []
        this.selectedCUI = null
      }
    },
    cancelReassign: function () {
      this.altSearch = false
      this.searchResults = []
      this.selectedCUI = null
    },
    keyup: function (e) {
      // 1-3 select a value
      if (e.keyCode >= 49 && e.keyCode <= 51 && !this.taskLocked) {
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
            break
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
  text-align: center;
  padding-top: 5px;
  padding-bottom: 30px;
  background-color: $background;
  color: $text;
}

.task-bar-choices {
  padding: 5px;
}

.task-name {
  font-size: 22px;
}

.alt-concept-picker {
  padding: 5px;
}

.cui-btns {
  opacity: 0.7;
  float: right;
  position: relative;

  &:hover {
    opacity: 0.9;
    cursor: pointer;
  }
}

.edit {
  @extend .cui-btns;
  top: 7px;
}

.cancel {
  @extend .cui-btns;
  top: 10px;
}

.picker {
  width: calc(100% - 30px);
  display: inline-block;
}

.editing {
  opacity: 0.9;
}
</style>
