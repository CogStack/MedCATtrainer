<template>
  <div>
    <b-overlay :show="loading" no-wrap opacity="0.5">
      <template #overlay>
        <b-spinner :variant="'primary'"></b-spinner>
      </template>
    </b-overlay>
    <div>
      <div class="search-bar">
        <b-input v-model="filter" type="search" placeholder="Search for concepts..."></b-input>
        <span v-if="filter === ''">Project Concept Filter: {{(allItems || []).length}}</span>
        <span v-if="filter !== ''">Found {{allFilteredItems.length}} - showing first {{items.length}}</span>
      </div>

      <b-table ref="concept-table" id="table-id"
               :items="items"
               :fields="fields"
               sticky-header
               show-empty
               small>
        <template #cell(name)="data">
          <span v-html="data.item.name"></span>
        </template>
      </b-table>
    </div>
  </div>
</template>

<script>
import _ from 'lodash'

const ROW_LIMIT = 100

export default {
  name: "ConceptFilter",
  props: {
    cuis: String,
    cdb_id: Number
  },
  data () {
    return {
      rowLimit: ROW_LIMIT,
      currentPage: 1,
      loading: false,
      items: null,
      allItems: null,
      allFilteredItems: null,
      fields: [
        { key: 'cui', label: 'CUI', sortable: true },
        { key: 'name', label: 'Name', sortable: true }
      ],
      filter: '',
    }
  },
  created () {
    this.loading = true
    let payload = {
      cuis: this.cuis !== '' ? this.cuis.split(',') : null,
      cdb_id: this.cdb_id
    }
    this.$http.post('/api/cuis-to-concepts/', payload).then(resp => {
      const items = resp.data.concept_list.sort((a,b) => a.name.localeCompare(b.name))
      if (items.length > ROW_LIMIT) {
        this.items = items.slice(0, ROW_LIMIT)
        this.allItems = items
      } else {
        this.items = items
        this.allItems = this.items
      }
      this.loading = false
    })
  },
  mounted () {
    const tableScrollBody = this.$refs["concept-table"].$el;
    /* Consider debouncing the event call */
    tableScrollBody.addEventListener("scroll", this.onScroll);
  },
  beforeDestroy() {
    /* Clean up just to be sure */
    const tableScrollBody = this.$refs["concept-table"].$el;
    tableScrollBody.removeEventListener("scroll", this.onScroll);
  },
  methods: {
    onScroll (event) {
      if (
        event.target.scrollTop + event.target.clientHeight >=
        event.target.scrollHeight
      ) {
        // fetch more items
        if (this.allFilteredItems !== null && this.items.length !== this.allFilteredItems.length) {
          window.setTimeout(() => {
            if (this.filter.length !== 0) {
              if (this.items.length < this.allFilteredItems.length) {
                this.items = this.allFilteredItems.slice(0, ROW_LIMIT * this.currentPage)
                this.currentPage ++
                this.loading = false
              }
            } else if (this.items.length !== this.allItems.length) {
              this.items = this.allItems.slice(0, ROW_LIMIT * this.currentPage)
              this.currentPage ++
              this.loading = false
            } else {
              this.loading = false
            }
          }, 200)
          this.loading = true
        }
      }
    },
    filterItems: _.debounce(function(filterStr) {
      filterStr = filterStr.toLowerCase()
      function highlightCUINames(concepts, query) {
        const lowercaseQuery = query.toLowerCase();
        return concepts.map(concept => {
          const name = concept.name
          let lowercaseStr = name.toLowerCase();
          let result = '';
          let lastIndex = 0;

          while (true) {
            const index = lowercaseStr.indexOf(lowercaseQuery, lastIndex);
            if (index === -1) break;

            result += name.slice(lastIndex, index);
            result += `<span class="highlight">${name.slice(index, index + query.length)}</span>`;

            lastIndex = index + query.length;
          }
          result += name.slice(lastIndex);
          return {...concept, ...{ name: result }}
        });
      }
      let filteredItems = this.allItems.filter((v) => v.name.toLowerCase().includes(filterStr))
      filteredItems = filteredItems.sort((a,b) => {
        const aStartsWith = a.name.toLowerCase().startsWith(filterStr)
        const bStartsWith = b.name.toLowerCase().startsWith(filterStr)
        if (aStartsWith !== bStartsWith) {
          return aStartsWith ? -1 : 1
        }
        return a.name.length - b.name.length

      })
      filteredItems = highlightCUINames(filteredItems, filterStr)

      if (filteredItems.length > ROW_LIMIT) {
        this.allFilteredItems = filteredItems
        this.items = this.allFilteredItems.slice(0, ROW_LIMIT)
      } else {
        this.items = filteredItems
        this.allFilteredItems = []
      }
      this.currentPage = 0
      this.loading = false
    }, 300)
  },
  watch: {
    filter (newVal, oldVal) {
      if (newVal.length > 0) {
        this.filterItems(newVal)
      } else {
        this.items = this.allItems.slice(0, ROW_LIMIT)
        this.allFilteredItems = null
        this.currentPage = 0
        this.loading = false
      }
    }
  }
}
</script>

<style lang="scss">
.search-bar {
  margin: 10px 0;
  width: calc(100% - 300px);

  input {
    display: inline-block;
    width: calc(100% - 300px);
  }

  span {
    float: right;
  }
}

.highlight {
  font-weight: bold;
}
</style>
