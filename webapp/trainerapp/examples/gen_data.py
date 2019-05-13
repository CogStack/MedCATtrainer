import json
import re
from random import random

import pandas as pd

"""
Script for generating example files from mimic3 data saved to disk. 
The notes.csv file is the result of SQL: select * from NOTEEVENTS where category='Discharge summary' 
"""
_note_events_csv = '/Users/tom/phd/tdy_ehr/mimic_tidy/data/notes.csv'


def gen_training_data():
    df = pd.read_csv(_note_events_csv)
    df = df.iloc[0:100, :]
    token = 'bled|bleed|bleeding|hemorrhage'
    cui = 'C0019080'
    tui = 'T046'
    output_texts = []
    for i, text in enumerate(df.text):
        t_l = text.lower()
        matches = re.finditer(token, t_l)
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


if __name__ == '__main__':
    gen_training_data()
