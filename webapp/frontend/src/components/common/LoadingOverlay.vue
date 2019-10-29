<template>
  <transition name="fade">
    <div v-if="loading" class="loading">
      <div class="spinner">
        <font-awesome-icon icon="spinner" size="1x" spin></font-awesome-icon>
      </div>
    </div>
  </transition>
</template>

<script>
export default {
  name: 'LoadingOverlay',
  props: {
    loading: Boolean
  }
}
</script>

<style scoped lang="scss">
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
</style>
