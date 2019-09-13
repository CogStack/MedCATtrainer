<template>
  <div class="nav-bar border-top border-left">
    <div class="nav-buttons border-bottom">
      <button :disabled="backDisabled()" @click="back()" type="button" class="btn btn-warning mb-2">
        <font-awesome-icon icon="backward"></font-awesome-icon>
      </button>
      <button :disabled="nextDisabled()"  @click="next()" type="button" class="btn btn-warning mb-2">
        <font-awesome-icon icon="forward"></font-awesome-icon>
      </button>
    </div>
    <div class="submit-container border-bottom">
      <button :disabled="submitDisabled()" @click="submit()" class="btn btn-primary mb-2 submit-btn" type="button">
        Submit
      </button>
    </div>

  </div>
</template>

<script>
export default {
  name: 'NavBar',
  props: {
    tasks: Array,
    ents: Array,
    currentEnt: Object,
  },
  methods: {
    nextDisabled: function() {
      return this.ents === null ? true : this.ents[this.ents.length - 1] === this.currentEnt;
    },
    backDisabled: function() {
      return this.ents === null ? true : this.ents[0] === this.currentEnt;
    },
    submitDisabled: function() {
      // all tasks complete for all ents
      if (this.ents !== null) {
        return !this.ents.every(e => {
          return Object.values(e.assignedValues).every(e => e !== null)
        })
      }
      return true
    },
    next: function() {
      this.$emit('select:next')
    },
    back: function() {
      this.$emit('select:back')
    },
    submit: function() {
      this.$emit('submit')
    },
    keyup: function(e) {
      if (e.keyCode === 13) {
        if (!this.submitDisabled())
          this.submit();
      } else if (e.keyCode === 37 && !this.backDisabled()) {
        this.back();
      } else if (e.keyCode === 39 && !this.nextDisabled()) {
        this.next();
      }
    }
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
.nav-bar {
  width: 100%;
}

.nav-buttons {
  text-align: center;
  width: 100%;
  padding: 5px 0;
}

.submit-btn {
  width: 80%;
  max-width: 400px;
  padding: 5px 0;
}

.submit-container {
  width: 100%;
  text-align: center;
}
</style>
