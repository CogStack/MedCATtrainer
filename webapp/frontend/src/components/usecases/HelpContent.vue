<template>
  <div>
    <div v-for="(info, taskName) in descriptions">
      <h4>Task: {{taskName}}</h4>
      <p>{{info.description}}</p>
      <table class="table table-striped">
        <thead>
        <th>Value</th>
        <th>Description</th>
        </thead>
        <tbody>
        <tr v-for="(valueHelp, value) in info.values">
          <td>{{value}}</td>
          <td>{{valueHelp}}</td>
        </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
export default {
  name: 'HelpContent',
  props: {
    descriptions: Object
  }
}
</script>

<style scoped lang="scss">

</style>
