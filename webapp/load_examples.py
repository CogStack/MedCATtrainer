import os

import pandas as pd
import requests
from time import sleep
import json

PORT = 8000
URL = f'http://localhost:{PORT}/api/'
sleep(15)

CDB_TMP_FILE = '/home/cdb.dat'
VOCAB_TMP_FILE = '/home/vocab.dat'
DATASET_TMP_FILE = '/home/ds.csv'

print('Checking for default projects / datasets / CDBs / Vocabs')
while True:
    # check API is available
    if requests.get(URL).status_code == 200:
        # check API default username and pass are available.
        payload = {"username": "admin", "password": "admin"}
        resp = requests.post(f"{URL}api-token-auth/", json=payload)
        if resp.status_code != 200:
            break

        headers = {
            'Authorization': f'Token {json.loads(resp.text)["token"]}',
        }

        # check concepts DB, vocab, datasets and projects are empty
        resp_cdbs = requests.get(f'{URL}concept-dbs/', headers=headers)
        resp_vocabs = requests.get(f'{URL}vocabs/', headers=headers)
        resp_ds = requests.get(f'{URL}datasets/', headers=headers)
        resp_projs = requests.get(f'{URL}project-annotate-entities/', headers=headers)
        all_resps = [resp_cdbs, resp_vocabs, resp_ds, resp_projs]

        codes = [r.status_code == 200 for r in all_resps]
        if all(codes) and all(json.loads(r.text)['count'] == 0 for r in all_resps):
            print("Found No Objects. Populating Example: Concept DB, Vocabulary, Dataset and Project...")
            # download example cdb, vocab, dataset
            print("Downloading example CDB...")
            cdb_file = requests.get('https://s3-eu-west-1.amazonaws.com/zkcl/cdb-medmen.dat')
            with open(CDB_TMP_FILE, 'wb') as f:
                f.write(cdb_file.content)
            print("Downloading example vocab...")
            vocab_file = requests.get('https://s3-eu-west-1.amazonaws.com/zkcl/vocab.dat')
            with open(VOCAB_TMP_FILE, 'wb') as f:
                f.write(vocab_file.content)
            print("Downloading example dataset")
            ds = requests.get('https://medcattrainer-psych-notes.s3-eu-west-1.amazonaws.com/psych.csv')
            with open(DATASET_TMP_FILE, 'w') as f:
                f.write(ds.text)

            # Upload CDB and vocab
            print('Creating CDB / Vocab / Dataset / Project in the Trainer')
            res_cdb_mk = requests.post(f'{URL}concept-dbs/', headers=headers,
                                       data={'name': 'api_upload_cdb', 'use_for_training': True},
                                       files={'cdb_file': open(CDB_TMP_FILE, 'rb')})
            cdb_id = json.loads(res_cdb_mk.text)['id']
            res_vocab_mk = requests.post(f'{URL}vocabs/', headers=headers,
                                         files={'vocab_file': open(VOCAB_TMP_FILE, 'rb')})
            vocab_id = json.loads(res_vocab_mk.text)['id']

            # Upload the dataset
            dataset = pd.read_csv(DATASET_TMP_FILE)
            payload = {
                'dataset_name': 'Example Dataset',
                'dataset': dataset.loc[:, ['name', 'text']].to_dict(),
                'description': f'Example clinical text from the MT Samples corpus https://www.mtsamples.com/'
            }
            resp = requests.post(f'{URL}create-dataset/', json=payload, headers=headers)
            ds_id = json.loads(resp.text)['dataset_id']

            user_id = json.loads(requests.get(f'{URL}users/', headers=headers).text)['results'][0]['id']

            # Create the project
            payload = {
                'name': 'Example Annotation Project - UMLS (Diseases / Symptoms / Findings)',
                'description': 'Example projects using example psychiatric clinical notes from '
                               'https://www.mtsamples.com/',
                'cuis': '',
                'tuis': 'T047, T048, T184',
                'dataset': ds_id,
                'concept_db': cdb_id,
                'vocab': vocab_id,
                'members': [user_id]
            }
            proj_mk = requests.post(f'{URL}project-annotate-entities/', json=payload, headers=headers)
            print('Successfully created the example project')

            # clean up temp files
            os.remove(CDB_TMP_FILE)
            os.remove(VOCAB_TMP_FILE)
            os.remove(DATASET_TMP_FILE)
            break
        else:
            print('Found at least one object amongst cdbs, vocabs, datasets & projects. Skipping example creation')
            break
    # Repeat...
    sleep(5)
