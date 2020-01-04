<template>
  <transition name="fade">
    <div v-if="loading" class="loading">
      <h3 class="loading-message">
        <slot name="message">
        </slot>
      </h3>
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
  height: 100%;
  position: relative;

  .loading-message {
    position: absolute;
    top: 40%;
    left: 45%;
    opacity: 0.25;
  }

  .spinner {
    position: absolute;
    top: 50%;
    left: 50%;
    font-size: 64px;
    opacity: 0.25;
  }
}

.fade-enter-active, .fade-leave-active {
  transition: opacity .3s;
}

.fade-enter, .fade-leave-to {
  opacity: 0;
}
</style>
