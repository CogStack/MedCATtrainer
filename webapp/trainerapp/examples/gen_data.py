import json
import pickle
import re
from glob import glob
from random import random

import pandas as pd
from sklearn import pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import cohen_kappa_score, accuracy_score, f1_score
from sklearn.model_selection import train_test_split, GridSearchCV

"""
Throw away script for:
1) Generating example files to be hand labelled
2) Outputting some metrics of hand labelled in comparison to another hand labelled dataset prefixed with 'r1' dir 
3) Outputting Cohen's Kappa
4) Cross validating and training a RandomForest model on 100 characters before/after
The notes.csv file is the result of SQL: select * from NOTEEVENTS where category='Discharge summary' 
"""

_note_events_csv = '/Users/tom/phd/tdy_ehr/mimic_tidy/data/notes.csv'


_token = 'seizure|epilepsy|seizre|seizur'

def gen_training_data():
    df = pd.read_csv(_note_events_csv)
    df = df.iloc[0:1000, :]
    cui = 'C0036572'
    tui = 'T1834'
    output_texts = []
    for i, text in enumerate(df.text):
        t_l = text.lower()
        matches = re.finditer(_token, t_l)
        txt_blob = {
            'text': text,
            'entities': [],
        }
        for i, m in enumerate(matches):
            txt_blob['entities'].append({
                'id': i,
                'start_tkn': 0,
                'end_tkn': 0,
                'source_value': '',
                'start_ind': m.start(),
                'end_ind': m.end(),
                'label': cui,
                'cui': cui,
                'tui': tui,
                'acc': str(random()),
                'type': 'Medical Device',
                'cntx': {
                    'text': m[0],
                    'cntx_ent_start': m.start(),
                    'cntx_ent_end': m.end(),
                }
            })
        if len(txt_blob['entities']) != 0:
            output_texts.append(txt_blob)

    output_dir = '/Users/tom/phd/cattrainer/webapp/trainerapp/examples/input/train'
    for i, text in enumerate(output_texts):
        text['f_name'] = f'{i}.json'
        json.dump(text, open(f'{output_dir}/{text["f_name"]}', 'w'))


def num_of_occurrences():
    output_dir = '/Users/tom/phd/cattrainer/webapp/trainerapp/examples/incomplete/train/*'
    no_temps = 0
    concept_counts = 0
    historical = 0
    not_historical = 0
    for f_n in glob(output_dir):
        with open(f_n) as f:
            ents = json.load(f)['entities']
            concept_counts += len(ents)
            no_temps = len([e for e in ents if 'Temporality' not in e])
            not_historical += len([e for e in ents
                                   if 'Temporality' in e and e['Temporality'] == 0])
            historical += len([e['Temporality'] for e in ents
                               if 'Temporality' in e and e['Temporality'] == 1])
    print(f'# Concept:{concept_counts}')
    print(f'# Hist:   {historical}')
    print(f'# N Hist: {not_historical}')
    print(f'# No Temp:{no_temps}')


def calc_cohens_kappa():
    r1_output_dir = '/Users/tom/phd/cattrainer/webapp/trainerapp/examples/output/train/*'
    r2_output_dir = '/Users/tom/phd/cattrainer/webapp/trainerapp/examples/r1_labs/output/train/*'

    r2_dir = '/Users/tom/phd/cattrainer/webapp/trainerapp/examples/r1_labs/output/train/'

    complete_r1 = glob(r1_output_dir)
    complete_r2 = glob(r2_output_dir)

    r_2_files = [f.split('/')[-1] for f in complete_r2]

    r1_labels = []
    r2_labels = []

    docs_used = set()

    for full_f_n in complete_r1:
        f_n = full_f_n.split('/')[-1]
        if f_n in r_2_files:
            r_1_ents = json.load(open(full_f_n))['entities']
            r_2_ents = json.load(open(r2_dir + f_n))['entities']
            r1_ctx_start = {e['start_ind']: e for e in r_1_ents if 'Temporality' in e}
            r2_ctx_to_ent = {e['start_ind']: e for e in r_2_ents if 'Temporality' in e}
            for k, v in r1_ctx_start.items():
                if k in r2_ctx_to_ent:
                    docs_used.add(f_n)
                    r1_labels.append(v['Temporality'])
                    r2_labels.append(r2_ctx_to_ent[k]['Temporality'])

    print(f'intersection Docs: {len(docs_used)}')
    percent_agreement = (len([1 for r_1, r_2 in zip(r1_labels, r2_labels) if r_1 == r_2]) / \
                        len(r1_labels)) * 100
    print(f'# concepts: {len(r1_labels)}')
    print(f'# not historical r1: {len([l for l in r1_labels if l == 0])}')
    print(f'# historical r1:     {len([l for l in r1_labels if l == 1])}')
    print(f'# not historical r2: {len([l for l in r2_labels if l == 0])}')
    print(f'# historical r2:     {len([l for l in r2_labels if l == 1])}')
    # print('# concepts: ')
    print(f'% agreement:{percent_agreement}')
    score = cohen_kappa_score(r1_labels, r2_labels)
    print(f'Kappa:{score}')


def train_basic_classifier():
    r1_output_dir = '/Users/tom/phd/cattrainer/webapp/trainerapp/examples/output/train/*'
    r2_output_dir = '/Users/tom/phd/cattrainer/webapp/trainerapp/examples/r1_labs/output/train/*'

    r2_dir = '/Users/tom/phd/cattrainer/webapp/trainerapp/examples/r1_labs/output/train/'

    complete_r1 = glob(r1_output_dir)
    complete_r2 = glob(r2_output_dir)

    r_2_files = [f.split('/')[-1] for f in complete_r2]

    tokens = []
    labels = []

    docs_used = set()

    chars_either_side = 100

    for full_f_n in complete_r1:
        f_n = full_f_n.split('/')[-1]
        if f_n in r_2_files:
            text = json.load(open(full_f_n))['text']
            r_1_ents = json.load(open(full_f_n))['entities']
            r_2_ents = json.load(open(r2_dir + f_n))['entities']
            r1_ctx_start = {e['start_ind']: e for e in r_1_ents if 'Temporality' in e}
            r2_ctx_to_ent = {e['start_ind']: e for e in r_2_ents if 'Temporality' in e}
            for k, v in r1_ctx_start.items():
                if k in r2_ctx_to_ent and v['Temporality'] == r2_ctx_to_ent[k]['Temporality']:
                    docs_used.add(f_n)
                    str_left = text[v['start_ind'] - chars_either_side:v['start_ind']]
                    str_right = text[v['end_ind']:v['end_ind'] + chars_either_side]
                    full_ctx = str_left + str_right
                    tokens.append(full_ctx)
                    labels.append(v['Temporality'])

    PUNC = r'[\[\.,\\/#!$%\^&\*;:{}=\-_`~()\]\'\"\|<>/\?\@\$\%\£\+]'

    def clean(txt):
        txt = txt.lower()
        txt = re.sub('\[\*\*.*?\*\*\]', '', txt)
        txt = re.sub('\d', '', txt)
        txt = re.sub('(\s+)', ' ', txt)
        txt = re.sub(PUNC, ' ', txt)
        return txt

    clean_txt = [clean(t) for t in tokens]

    # print a random subset.
    print('\n'.join([f'{t} \t ----> {l}' for t, l in zip(clean_txt[30:40], labels[30:40])]))

    clean_samples = []
    for sampl in clean_txt:
        toks = sampl.split()
        # throw away toks either side
        toks = toks[1:len(toks)-2]
        toks = [t for t in toks if len(t) > 1]
        clean_samples.append(' '.join(toks))

    X_train, X_test, y_train, y_test = train_test_split(clean_samples, labels, test_size=0.3,
                                                        random_state=1)

    params = {
        'vect__stop_words': ['english'],
        'vect__sublinear_tf': [True, False],
        'vect__max_features': [500, 1000, 10000],
        'vect__norm': ['l1', 'l2'],
        'clf__max_depth': [5, 20, 50, 75],
        'clf__n_estimators': [100, 300, 500, 1000, 2000],
    }

    model = pipeline.Pipeline([
        ('vect', TfidfVectorizer()),
        ('clf', RandomForestClassifier())
        # ('clf', SVC())
    ])

    search = GridSearchCV(model, params, scoring='f1', n_jobs=4, cv=3)
    print('Finding best params')
    search.fit(X_train, y_train)
    model.set_params(**search.best_params_)

    print('Found best params:')
    print(search.best_params_)

    print('Final Fitting')
    model.fit(X_train, y_train)

    pickle.dump(model, open('temp_model.pickle', 'wb'))

    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    print(accuracy_score(y_test, y_pred))
    print(f1_score(y_test, y_pred))


if __name__ == '__main__':
    # num_of_occurrences()
    # gen_training_data()
    # calc_cohens_kappa()
    train_basic_classifier()
