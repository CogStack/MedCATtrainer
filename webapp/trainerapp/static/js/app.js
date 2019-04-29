Vue.component('clinical-text', {
  props: ['text', 'spans', 'labels', 'spanIndex'],
  computed: {
    formattedText: function() {

      let wrap_in_text = function(txt, spanTxt, valStart, valEnd) {
        return txt.slice(0, valStart-1) + spanTxt + txt.slice(valEnd+1, txt.length)
      };
      let txt = this.text;
      let formattedTxt = '';

      // find non_overlapping spans and slice each of those...
      if (this.spans && this.spans.length > 0) {
        let sortedSpans = this.spans.sort((a, b) => a[0] - b[0]);

        let start = 0;
        let end = sortedSpans[0][0];

        for (let i = 0; i < sortedSpans.length; i++) {
          formattedTxt += txt.slice(start, end);
          const valStart = sortedSpans[i][0];
          const valEnd = sortedSpans[i][1];
          let spanTxt = '';
          if (this.labels[i] === null)
            spanTxt = `<span class="bg-primary text-white">${txt.slice(valStart, valEnd)}</span>`;
          else if (this.labels[i])
            spanTxt = `<span class="bg-success text-white">${txt.slice(valStart, valEnd)}</span>`;
          else
            spanTxt = `<span class="bg-danger text-white">${txt.slice(valStart, valEnd)}</span>`;

          if (this.spanIndex === i) {
            spanTxt = `<span id="focusSpan" class="highlight">${spanTxt}</span>`;
          }
          formattedTxt += spanTxt;

          if (i !== sortedSpans.length - 1)
            end = sortedSpans[i+1][0];
          else
            end = txt.length - 1;
          start = sortedSpans[i][1];
        }
        formattedTxt += txt.slice(start, end);
      }
      return formattedTxt;
    }
  },
  updated: function() {
    this.$nextTick(function () {
      document.getElementById('focusSpan').scrollIntoView({
        block: "center",
        behavior: "smooth",
      });
    });
  },
  template: `
    <div class="note-container">
      <p class="clinical-note" v-html="formattedText"></p>
    </div>
  `
});

Vue.component('sidebar', {
  props: ['texts', 'currentDoc', 'currentSpan'],
  template: `
    <div class="col-3 mb-2 border-top border-right app-sidebar">
      <div v-if="texts.length > 0">
        <h3>Document:{{currentDoc + 1}} of {{texts.length}}</h3>
        <h4>Span:{{currentSpan + 1}} of {{texts[currentDoc].spans.length}}</h4>
        <h4></h4>
      </div>
    </div>
  `
});

let data = {
  allTexts: [],
  current: {
    text: '',
    spans: [],
    labels: [],
    spanIndex: -1,
    docIndex: -1,
  },
  searchTerm: '',
  classifierTask: '',
};

let nextSpan = function(data) {
  if (data.current.docIndex === data.allTexts.length - 1 &&
      data.current.spanIndex === data.current.spans.length - 1)
    return;
  if (data.current.spanIndex === data.current.spans.length - 1) {
    data.current.docIndex ++;
    data.current.spanIndex = 0;
    let newCurrText = data.allTexts[data.current.docIndex];
    data.current.text = newCurrText.text;
    data.current.spans = newCurrText.spans;
    data.current.labels = newCurrText.labels;
  } else {
    data.current.spanIndex++;
  }

};

// call data resource here.

data.allTexts = taskTrainingData().entities.map(i => {
  // per document / text there should be multiple spans...
  return {
    labels: [null],
    spans: [[i.cntx.cntx_ent_start, i.cntx.cntx_ent_end]],
    type: [i.type],
    text: taskTrainingData().text
  };
  // convert spans to this data model ... append all other useful info... to this model
});
// side bar and clinical text components
data.current.docIndex = 0;
data.current.spanIndex = 0;
const currText = data.allTexts[data.current.docIndex];
data.current.text = currText.text;
data.current.spans = currText.spans;
data.current.labels = currText.labels;


let app = new Vue({
  el: '#app',
  data: data,
  methods: {
    yes: function (e) {
      e.preventDefault();
      data.allTexts[data.current.docIndex].labels[data.current.spanIndex] = true;
      nextSpan(data);
    },
    no: function (e) {
      e.preventDefault();
      data.allTexts[data.current.docIndex].labels[data.current.spanIndex] = false;
      nextSpan(data);
    },
    back: function (e) {
      e.preventDefault();
      if (data.current.spanIndex === 0) {
        data.current.docIndex--;
        data.current.spanIndex = 0;
        let newCurrText = data.allTexts[data.current.docIndex];
        data.current.text = newCurrText.text;
        data.current.spans = newCurrText.spans;
        data.current.labels = newCurrText.labels;
      } else {
        data.current.spanIndex--;
      }
    },
    next: function (e) {
      e.preventDefault();
      nextSpan(data);
    },
    save: function(e) {
      e.preventDefault();
      this.$http.post('/store', data.allTexts)
          .then(response => {

          });
    }
  }
});




