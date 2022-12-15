import re

import pandas as pd

from .models import *

_MAX_DATASET_SIZE_DEFAULT = 10000


def dataset_from_file(dataset: Dataset):
    if '.csv' in dataset.original_file.path:
        df = pd.read_csv(dataset.original_file.path, on_bad_lines='error')
    elif '.xlsx' in dataset.original_file.path:
        df = pd.read_excel(dataset.original_file.path)
    else:
        raise Exception("Please make sure the file is either a .csv or .xlsx format")

    df.columns = [c.lower() for c in df.columns]
    max_dataset_size = os.environ.get('MAX_DATASET_SIZE', _MAX_DATASET_SIZE_DEFAULT)

    if df['name'].nunique() != df.shape[0] and os.environ.get('UNIQUE_DOC_NAMES_IN_DATASETS', True):
        raise Exception('name column entries must be unique')

    if df.shape[0] > int(max_dataset_size):
        raise Exception(f'Attempting to upload a dataset with {df.shape[0]} rows. The Max dataset size is set to'
                        f' {max_dataset_size}, please reduce the number of rows or contact the MedCATTrainer'
                        f' administrator to increase the env var value:MAX_DATASET_SIZE')

    if 'text' not in df.columns or 'name' not in df.columns:
        raise Exception("Please make sure the uploaded file has a column with two columns:'name', 'text'. "
                        "The 'name' column are document IDs, and the 'text' column is the text you're "
                        "collecting annotations for")


    for i, row in enumerate(df.iterrows()):
        row = row[1]
        document = Document()
        document.name = row['name']
        document.text = sanitise_input(row['text'])
        document.dataset = dataset
        document.save()


def sanitise_input(text: str):
    tags = [('<br>', '\n'), ('</?p>', '\n'), ('<span(?:.*?)?>', ''),
            ('</span>', ''), ('<div (?:.*?)?>', '\n'), ('</div>', '\n'),
            ('</?html>', ''), ('</?body>', ''), ('</?head>', '')]
    for tag, repl in tags:
        text = re.sub(tag, repl, text)
    return text


def delete_orphan_docs(dataset: Dataset):
    Document.objects.filter(dataset__id=dataset.id).delete()
