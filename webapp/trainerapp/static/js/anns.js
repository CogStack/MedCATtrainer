let doc_json = getData();


let info = new Vue({
  el: '#train-annotations',
  delimiters: ['[[', ']]'],
  data: {
    selected_concept: doc_json['entities'][0],
    show: false,
    elementVisible: false,
    msg: '',
    search_query: '',
    search_results: [],
    searching: false,
  },
  watch: {
    'search_query': function(newSearch, oldSearch) {
      this.$data.search_results = [];
      this.debounced_search_query();
    }
  },
  created: function() {
    this.debounced_search_query = _.debounce(this.search, 400)
  },
  methods: {
    show_info: function(id) {
      this.selected_concept = doc_json.entities.filter((e) => Number(e.id) === id)[0];
    },

    concept_feedback: function(neg) {
      if(neg){
        this.showMsg("Negative feedback recorded");
      }
      else{
        this.showMsg("Positive feedback recorded");
      }
      let d = {};
      d['cui'] = this.selected_concept['cui'];
      d['text'] = doc_json['text'];
      d['negative'] = neg;
      d['tkn_inds'] = [this.selected_concept['start_tkn'], this.selected_concept['end_tkn']];
      d['char_inds'] = [this.selected_concept['start_ind'], this.selected_concept['end_ind']];
      d['ajaxRequest'] = true;

      this.$http.post('/add_cntx', d, {
        headers: {
          'X-CSRFToken': Cookies.get('csrftoken')
        }
      });
    },

    search: function() {
      if (this.search_query.length > 0) {
        this.$http.get(`/search_concept?q=${this.search_query}`, {
          headers: {
            'X-CSRFToken': Cookies.get('csrftoken')
          }
        }).then((resp) => {
          console.log(resp);
          this.searching = false;
          this.$data.search_results = resp.body.results
        }).catch((err) => {
          this.showMsg('Failed to search for concepts');
          this.searching = false;
          console.error(err)
        });
        this.searching = true;
      }
    },
    select_concept: function(concept) {
      this.search_results = [];
      this.$refs.cui.value = concept.cui;
      this.$refs.cntx_name.value = concept.name;
      this.$refs.tui.value = concept.tui;
      this.$refs.synonyms.value = concept.synonyms.join(',');
    },
    create_concept: function() {
      let d = {};
      console.log(this.$refs);
      d['name'] = this.$refs.cntx_name.value;
      d['cui'] = this.$refs.cui.value;
      d['tui'] = this.$refs.tui.value;
      d['source_value'] = this.$refs.source_value.value;
      d['synonyms'] = this.$refs.synonyms.value;
      d['text'] = this.$refs.cntx_text.value;
      d['ajaxRequest'] = true;


      this.$http.post('/add_concept_manual', d, {
         headers: {
          'X-CSRFToken': Cookies.get('csrftoken')
         }
      }).then((resp) => {
        this.showMsg("New concept created");
        this.show=false;
      }).catch((err) => {
        this.showMsg('Failed to create new concept');
        console.error(err)
      });
    },

    save_cdb_model: function() {
      let d = {};
      d['ajaxRequest'] = true;
      this.$http.post('/save_cdb_model', d, {
         headers: {
          'X-CSRFToken': Cookies.get('csrftoken')
         }
      }).then((resp) => {
        this.showMsg('New training data added and model saved');
        this.show=false;
      }).catch((err) => {
        this.showMsg('Failed to save changes');
        console.error(err)
      });
    },

    reset_cdb_model: function() {
      let d = {};
      d['ajaxRequest'] = true;

      this.$http.post('/reset_cdb_model', d, {
        headers: {
          'X-CSRFToken': Cookies.get('csrftoken')
        }
      }).then(() => {
        this.showMsg('Model reset to the last saved instance');
        this.show=false;
      }).catch((err) => {
        this.showMsg('Failed to save changes');
        console.error(err)
      });
    },

    showMsg: function(msg) {
      this.msg = msg;
      this.elementVisible = true;
      let vm = this;
      setTimeout(function () { vm.hideMsg() }, 4000);
    },

    hideMsg: function() {
      this.elementVisible = false;
    }
  }
});
