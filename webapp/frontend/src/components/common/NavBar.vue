<template>
  <div class="nav-bar">
    <div class="nav-buttons">
      <button :disabled="backDisabled()" @click="back()" type="button" class="btn btn-outline-warning mb-2">
        <font-awesome-icon icon="backward"></font-awesome-icon>
      </button>
      <button :disabled="nextDisabled()"  @click="next()" type="button" class="btn btn-outline-warning mb-2">
        <font-awesome-icon icon="forward"></font-awesome-icon>
      </button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'NavBar',
  props: {
    currentEnt: Object,
    ents: Array,
    useEnts: {
      default () {
        return true
      },
      type: Boolean
    },
    nextBtnDisabled: Boolean,
    backBtnDisabled: Boolean
  },
  methods: {
    nextDisabled () {
      if (this.useEnts) {
        return this.ents === null ? true : this.ents[this.ents.length - 1] === this.currentEnt
      }
      return this.nextBtnDisabled
    },
    backDisabled () {
      if (this.useEnts) {
        return this.ents === null ? true : this.ents[0] === this.currentEnt
      }
      return this.backBtnDisabled
    },
    next () {
      this.$emit('select:next')
    },
    back () {
      this.$emit('select:back')
    },
    keyup (e) {
      if (e.keyCode === 37 && !this.backDisabled()) {
        this.back()
      } else if (e.keyCode === 39 && !this.nextDisabled()) {
        this.next()
      }
    }
  },
  mounted () {
    window.addEventListener('keyup', this.keyup)
  },
  beforeDestroy () {
    window.removeEventListener('keyup', this.keyup)
  }
}
</script>

<style scoped lang="scss">
.nav-bar {
  display: inline-block;
  background: $background;
  color: $text;
}

.nav-buttons {
  padding: 10px 10px;
}
</style>
