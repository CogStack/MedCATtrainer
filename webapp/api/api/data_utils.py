import pandas as pd

from .models import *
import numpy as np


def dataset_from_file(dataset: Dataset):
    df = None
    if '.csv' in dataset.original_file.path:
        df = pd.read_csv(dataset.original_file.path)
    elif '.xlsx' in dataset.original_file.path:
        df = pd.read_excel(dataset.original_file.path)

    df.columns = [c.lower() for c in df.columns]
    if df is not None:
        if 'text' not in df.columns:
            raise Exception("Please make sure the uploaded file has a column with header 'text'")

        for i, row in enumerate(df.iterrows()):
            row = row[1]
            text = row['text']
            if 'name' in df.columns:
                name = row['name']
            else:
                name = f"Doc {i}"

            document = Document()
            document.name = name
            document.text = text
            document.dataset = dataset
            document.save()
    else:
        raise Exception("Please make sure the file is either a .csv or .xlsx format")


def delete_orphan_docs(dataset: Dataset):
    Document.objects.filter(dataset__id=dataset.id).delete()
