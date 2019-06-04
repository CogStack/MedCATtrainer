let doc_json = getData();


let info = new Vue({
  el: '#train-annotations',
  delimiters: ['[[', ']]'],
  data: {
    selected_concept: doc_json['entities'][0],
    show: false
  },
  methods: {
    show_info: function(id) {
      for(i = 0; i <= doc_json['entities'].length; i++){
        if(doc_json['entities'][i].id == id){
          this.selected_concept = doc_json['entities'][i];
          break;
        }
      }
    },
    concept_feedback: function(neg) {
      let d = {};
      d['cui'] = this.selected_concept['cui'];
      d['text'] = doc_json['text'];
      d['negative'] = neg;
      d['tkn_inds'] = [this.selected_concept['start_tkn'], this.selected_concept['end_tkn']];
      d['ajaxRequest'] = true;

      this.$http.post('/add_cntx', d, {
         headers: {
                 'X-CSRFToken': Cookies.get('csrftoken')
               }
      });
    },
    create_concept: function() {
      let d = {};
      console.log(this.$refs)
      d['name'] = this.$refs.cntx_name.value;
      d['cui'] = this.$refs.cui.value;
      d['tui'] = this.$refs.tui.value;
      d['source_value'] = this.$refs.source_value.value;
      d['text'] = this.$refs.cntx_text.value;
      d['ajaxRequest'] = true;

      this.$http.post('/add_concept_manual', d, {
         headers: {
                 'X-CSRFToken': Cookies.get('csrftoken')
               }
      });
      this.show=false;
    }
 
  }
})
