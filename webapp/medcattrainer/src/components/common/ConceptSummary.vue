<template>
  <div class="border-left border-bottom sidebar" id="info">
    <div class="ent-name">{{selectedEnt !== null ? selectedEnt.value : ''}}</div>
    <table class="table table-hover info">
      <tbody v-for="(value, name) in cleanProps()">
        <tr>
          <td>{{name}}</td>
          <td>{{value}}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>

const HIDDEN_PROPS = [
  'value', 'project', 'document', 'start_ind', 'end_ind',
  'entity', 'assignedValues', 'correct',
];

const PROP_MAP = {
  'acc': 'Accuracy',
  'user': 'User',
  'id': 'Entity ID',
};

export default {
  name: 'ConceptSummary',
  props: {
    selectedEnt: Object,
    tasks: Array
  },
  methods: {
    cleanProps: function() {
      if (this.selectedEnt !== null) {
        // remove props
        let ent = Object.keys(this.selectedEnt)
          .filter(k => !HIDDEN_PROPS.includes(k))
          .reduce((obj, key) => {
            obj[key] = this.selectedEnt[key];
            return obj;
          }, {});

        //flatten task vals
        for (const [k, v] of Object.entries(this.selectedEnt.assignedValues)) {
          ent[k] = v || 'n/a';
        }

        //pretty print props:
        for (const [prop, name] of Object.entries(PROP_MAP)) {
          if (ent[prop])
            ent[name] = ent[prop];
            delete ent[prop]
        }
        return ent
      }
      return {}
    },
    fetchDetail: function() {
      const params = {
        headers: {'Authorization': `Token ${this.$cookie.get('api-token')}`}
      };
      if (this.selectedEnt !== null) {
        this.$http.get(`/entities/${this.selectedEnt.id}/`, params).then(resp => {
          this.selectedEnt.CUI = resp.data.label;
          // doesn't appear this is being fully reactive... - loading?? pane needed??
          // fetch other concept related information.
          // this.$http.get(`/concepts/${this.selectedEnt.CUI}/`, params).then(resp => {
          //   this.selectedEnt.Description = resp.data.desc;
          //   this.selectedEnt.TUI = resp.data.tui;
          // })
        })
      }
    },
  },
  mounted: function() {
    this.fetchDetail();
  },
  watch: {
    'selectedEnt': 'fetchDetail'
  }
}
</script>

<style scoped lang="scss">
.ent-name {
  padding: 10px;
  font-size: 22px;
}

.sidebar {
  flex: 0 0 300px;
  overflow: auto;
}
</style>
