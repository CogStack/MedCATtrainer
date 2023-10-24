import os

import pandas as pd
import requests
from time import sleep
import json


def main(port=8000,
         umls_cdb_tmp_file='/home/cdb.dat',
         snomed_cdb_tmp_file='/home/snomed-cdb.dat',
         vocab_tmp_file='/home/vocab.dat',
         dataset_tmp_file='/home/ds.csv',
         initial_wait=15):

    val = os.environ.get('LOAD_EXAMPLES')
    if val is not None and val not in ('1', 'true', 't', 'y'):
        print('Found Env Var LOAD_EXAMPLES is False, not loading example data, cdb, vocab and project')
        return

    URL = f'http://localhost:{port}/api/'
    sleep(initial_wait)

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
                print("Downloading example UMLS CDB...")
                cdb_file = requests.get('https://cogstack-medcat-example-models.s3.eu-west-2.amazonaws.com/medcat-example-models/cdb-medmen-v1.dat')
                with open(umls_cdb_tmp_file, 'wb') as f:
                    f.write(cdb_file.content)
                print("Downloading example SNOMED CT CDB...")
                snomed_cdb_file = requests.get('https://cogstack-medcat-example-models.s3.eu-west-2.amazonaws.com/medcat-example-models/snomed-cdb-mc-v1.cdb')
                with open(snomed_cdb_tmp_file, 'wb') as f:
                    f.write(snomed_cdb_file.content)
                print("Downloading example vocab...")
                vocab_file = requests.get('https://cogstack-medcat-example-models.s3.eu-west-2.amazonaws.com/medcat-example-models/vocab.dat')
                with open(vocab_tmp_file, 'wb') as f:
                    f.write(vocab_file.content)
                print("Downloading example dataset")
                ds = requests.get('https://raw.githubusercontent.com/CogStack/MedCATtrainer/master/notebook_docs/example_data/ortho.csv')
                with open(dataset_tmp_file, 'w') as f:
                    f.write(ds.text)

                ds_dict = pd.read_csv(dataset_tmp_file).loc[:, ['name', 'text']].to_dict()
                create_example_project(URL, headers, umls_cdb_tmp_file, vocab_tmp_file, ds_dict, 'umls_cdb',
                                       'Example Project - UMLS (Diseases / Symptoms / Findings')
                create_example_project(URL, headers, snomed_cdb_tmp_file, vocab_tmp_file, ds_dict, 'snomed_cdb',
                                       'Example Project - SNOMED CT All')

                # clean up temp files
                os.remove(umls_cdb_tmp_file)
                os.remove(snomed_cdb_tmp_file)
                os.remove(vocab_tmp_file)
                os.remove(dataset_tmp_file)
                break
            else:
                print('Found at least one object amongst cdbs, vocabs, datasets & projects. Skipping example creation')
                break
        # Repeat...
        sleep(5)


def create_example_project(url, headers, cdb, vocab, ds_dict, cdb_name, project_name):
    print('Creating CDB / Vocab / Dataset / Project in the Trainer')
    res_cdb_mk = requests.post(f'{url}concept-dbs/', headers=headers,
                               data={'name': cdb_name, 'use_for_training': True},
                               files={'cdb_file': open(cdb, 'rb')})
    cdb_id = json.loads(res_cdb_mk.text)['id']
    res_vocab_mk = requests.post(f'{url}vocabs/', headers=headers,
                                 files={'vocab_file': open(vocab, 'rb')})
    vocab_id = json.loads(res_vocab_mk.text)['id']

    # Upload the dataset
    payload = {
        'dataset_name': 'Example Dataset',
        'dataset': ds_dict,
        'description': f'Example clinical text from the MT Samples corpus https://www.mtsamples.com/'
    }
    resp = requests.post(f'{url}create-dataset/', json=payload, headers=headers)
    ds_id = json.loads(resp.text)['dataset_id']

    user_id = json.loads(requests.get(f'{url}users/', headers=headers).text)['results'][0]['id']

    # Create the project
    payload = {
        'name': project_name,
        'description': 'Example projects using example psychiatric clinical notes from '
                       'https://www.mtsamples.com/',
        'cuis': '',
        'annotation_guideline_link': 'https://docs.google.com/document/d/1xxelBOYbyVzJ7vLlztP2q1Kw9F5Vr1pRwblgrXPS7QM/edit?usp=sharing',
        'dataset': ds_id,
        'concept_db': cdb_id,
        'vocab': vocab_id,
        'members': [user_id]
    }
    requests.post(f'{url}project-annotate-entities/', json=payload, headers=headers)
    print('Successfully created the example project')


if __name__ == '__main__':
    main()
    # main(port=8001,
    # umls_cdb_tmp_file='/home/cerberus/projects/MedCATtrainer/scratch/cdb.dat',
    # snomed_cdb_tmp_file='/home/cerberus/projects/MedCATtrainer/scratch/snomed-cdb.dat',
    # vocab_tmp_file='/home/cerberus/projects/MedCATtrainer/scratch/vocab.dat',
    # dataset_tmp_file='/home/cerberus/projects/MedCATtrainer/scratch/ds.csv')
