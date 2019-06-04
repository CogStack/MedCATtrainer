import os
import json
from medcat.preprocessing.tokenizers import spacy_split_all
from medcat.preprocessing.cleaners import spacy_tag_punct
from medcat.utils.spacy_pipe import SpacyPipe
import numpy as np
from functools import partial

from medcat.cat import CAT
from medcat.utils.helpers import doc2html
from medcat.utils.vocab import Vocab
from medcat.cdb import CDB

from spacy import displacy

class CatWrap(object):
    # CHECK SHORT CONTEXT
    def __init__(self):
        vocab = Vocab()
        vocab.load_dict(os.getenv('VOCAB_PATH', 'models/vocab.dat'))
        vocab.make_unigram_table()

        cdb = CDB()
        cdb.load_dict(os.getenv('CDB_PATH', 'models/cdb.dat'))

        self.cat = CAT(cdb=cdb, vocab=vocab)
        self.cat.spacy_cat.DEBUG = True

    def add_concepts(self, in_file):
        pass


    def get_html_and_json(self, text):
        doc = self.cat(text)
        doc_json = self.cat.get_json(text)
        return doc2html(doc), doc_json


    def get_doc(self, params, in_path, is_text=False):
        """
        params:  A dictionary with values for cuis, tuis, tokens, cntx_size,
                 filters[(<name>, <value>, <acc>), ...]
                     params = {'cuis': ['c23123', 'c3216564', ...],
                               'tuis': ['t122', 't222', ...],
                               'tokens': ['kidney', 'heart attack', ...],
                               'cntx_tokens': ['not', 'maybe wrong', 'error', ...]
                               'filters': [('negated', 1, 0.6), ('historical', '10years', 0.5)]}
        """
        cuis = params.get('cuis', [])
        tuis = params.get('tuis', [])
        tokens= [tkn for tkn in params.get('tokens', []) if len(tkn.strip()) > 0]
        cntx_tokens = params.get('cntx_tokens', [])
        cntx_size = 5 # This is not really used anymore, but good for cntx_tokens
        filters = [(x[0], str(x[1]), float(x[2])) for x in params.get('filters', [])]
        f_names = [x for x in os.listdir(in_path) if ('.txt' in x or '.json' in x) and not x.startswith(".")]

        out_data = {}
        out_data['f_names'] = f_names
        for f_name in f_names:
            f = open(os.path.join(in_path, f_name), 'r')
            if '.txt' in f_name:
                # It is a text file
                data = json.loads(self.cat.get_json(f.read()))
            else:
                # Already processed by cat - json
                data = json.load(f)

            out_data['text'] = data['text']
            out_data['f_name'] = f_name
            out_data['entities'] = []

            for ent in data['entities']:
                if ent['cui'] in cuis or ent['tui'] in tuis or any([True if x in ent['source_value'] else False for x in tokens]):
                    # Check filters first, skip if not valid
                    skip_flag = False
                    for name, value, acc in filters:
                        if name in ent:
                            ent_val = ent['name']
                            ent_acc = ent.get(name + "_acc", 100)
                            if ent_val != value or ent_acc < acc:
                                skip_flag = True
                    if skip_flag:
                        # Skip this entity
                        continue

                    # Check cntx_text filter if exists
                    if cntx_tokens:
                        # Get the tokens and remove the zero length
                        cntx_tokens = [x for x in [str(x).lower() for x in cntx_tokens] if len(x) > 0]
                        if any([True if x in ent['cntx']['text'] else False for x in cntx_tokens]):
                            # Skip this entity
                            continue
                    out_data['entities'].append(ent)

            # Doc is fine, return it
            if len(out_data['entities']) > 0:
                break

        return out_data



    def save_doc(self, data, in_path, out_path, del_cntx=True):
        """ Save the newly annotated document

        data:  a dictionary with the new data
            data = {'f_name': <file_name>,
                    'entities': [<entity>, ...]}
        """

        f_name = data['f_name']
        if '.json' not in f_name:
            os.remove(os.path.join(in_path, f_name))
            f_out = open(os.path.join(out_path, f_name.replace('.txt', '.json')), 'w')
            json.dump(data, f_out)
        else:
            f_in = open(os.path.join(in_path, f_name), 'r')
            f_out = open(os.path.join(out_path, f_name), 'w')
            ents = data['entities']
            ids = [x['id'] for x in ents]
            new_ents = []

            doc = json.load(f_in)

            for ent in doc['entities']:
                if ent['id'] not in ids:
                    new_ents.append(ent)

            new_ents.extend(ents)
            doc['entities'] = new_ents

            # Remove old file
            f_in.close()
            os.remove(os.path.join(in_path, f_name))

            json.dump(doc, f_out)
