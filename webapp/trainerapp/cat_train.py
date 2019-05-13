import os
import json
from medcat.preprocessing.tokenizers import spacy_split_all
from medcat.preprocessing.cleaners import spacy_tag_punct
from medcat.utils.spacy_pipe import SpacyPipe
import numpy as np
from functools import partial

from medcat.cat import CAT
from medcat.utils.vocab import Vocab
from medcat.cdb import CDB

nlp = SpacyPipe(spacy_split_all, disable=['ner', 'parser'])
nlp.add_punct_tagger(tagger=partial(spacy_tag_punct, skip_stopwords=False))

vocab = Vocab()
vocab.load_dict(os.getenv('VOCAB_PATH', '../models/vocab.dat'))
cdb = CDB()
cdb.load_dict(os.getenv('CDB_PATH', '../models/cdb.dat'))
cat = CAT(cdb=cdb, vocab=vocab)

def get_doc(params, in_path, is_text=False):
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
    tokens= params.get('tokens', [])
    cntx_tokens = params.get('cntx_tokens', [])
    cntx_size = 5 # This is not really used anymore, but good for cntx_tokens
    filters = [(x[0], str(x[1]), float(x[2])) for x in params.get('filters', [])]
    f_names = [x for x in os.listdir(in_path) if ('.txt' in x or '.json' in x) and not x.startswith(".")]

    out_data = {}
    for f_name in f_names:
        f = open(os.path.join(in_path, f_name), 'r')
        if '.txt' in f_name:
            # It is a text file
            data = json.loads(cat.get_json(f.read()))
        else:
            # Already processed by cat - json
            data = json.load(f)

        out_data['text'] = data['text']
        out_data['f_name'] = f_name
        out_data['entities'] = []

        doc = nlp(data['text'])
        for ent in data['entities']:
            if ent['cui'] in cuis or ent['tui'] in tuis or any([True if x in ent['source_value'] else False for x in tokens]):
                # Check filters first, skip if not valid
                skip_flag = False
                for name, value, acc in filters:
                    if name in ent:
                        ent_val = ent['name']
                        ent_acc = ent.get(name + "_acc", 0)
                        if ent_val != value or ent_acc < acc:
                            skip_flag = True
                if skip_flag:
                    # Skip this entity
                    continue

                start = max(0, ent['start_tkn'] - cntx_size)
                end = min(len(doc), ent['end_tkn'] + cntx_size)
                cntx_ent_start = len(doc[start:ent['start_tkn']].text)
                cntx_ent_end = cntx_ent_start + len(ent['source_value']) + 1

                ent['cntx'] = {'text': str(doc[start:end+1])}
                # Check cntx_text filter if exists
                if cntx_tokens:
                    cntx_tokens = [str(x).lower() for x in cntx_tokens]
                    if any([True if x in ent['cntx']['text'] else False for x in cntx_tokens]):
                        # Skip this entity
                        continue
                out_data['entities'].append(ent)

        # Doc is fine, return it
        if len(out_data['entities']) > 0:
            break

    return out_data



def save_doc(data, in_path, out_path, del_cntx=True):
    """ Save the newly annotated document

    data:  a dictionary with the new data
        data = {'f_name': <file_name>,
                'entities': [<entity>, ...]}
    """

    f_name = data['f_name']
    f_in = open(os.path.join(in_path, f_name), 'r')
    f_out = open(os.path.join(out_path, f_name), 'w')
    ents = data['entities']
    ids = [x['id'] for x in ents]
    new_ents = []

    doc = json.load(f_in)
    for ent in doc['entities']:
        if ent['id'] not in ids:
            new_ents.append(ent)

    if del_cntx:
        for ent in ents:
            if 'cntx' in ent:
                del ent['cntx']

    new_ents.extend(ents)
    doc['entities'] = new_ents

    # Remoe old file
    f_in.close()
    os.remove(os.path.join(in_path, f_name))

    json.dump(doc, f_out)
