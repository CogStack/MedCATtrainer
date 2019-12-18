import pandas
import pandas as pd

from .models import *
import numpy as np


def text_from_csv(dataset: Dataset):
    df = pandas.read_csv(dataset.original_file.path, escapechar='\\')

    if 'text' not in df.columns:
        # TODO: Fix me
        raise Exception("Please make sure that the csv has a 'text' column")

    for row in df.iterrows():
        row = row[1]
        text = row['text']
        if 'name' in df.columns:
            name = row['name']
        else:
            name = "NO NAME"

        document = Document()
        document.name = name
        document.text = text
        document.dataset = dataset
        document.save()


# TODO: convert into a bg process
def text_classification_csv_import(dataset):
    f = open(dataset.original_file.path)
    print(f.read())
    skip_cols = ['id', 'text', 'name']
    df = pandas.read_csv(dataset.original_file.path)

    # First create all the TextClasses
    cols = [str(col) for col in list(df.columns)]

    # Text must be in the columns
    if 'text' not in cols:
        # TODO: Fix exception to something normal
        raise Exception("Please make sure that there is a column named 'text' in the csv file")

    for col in cols:
        col = col
        name = col.strip()
        while len(TextClass.objects.filter(name=name)) > 0:
            name = name + "_" + str(np.random.randint(100000))
        if col.strip().lower() not in skip_cols:
            # Create the necessary values
            vals = []
            raw_vals = pandas.unique([str(x).strip().lower() for x in df[col].values])
            for raw_val in raw_vals:
                # Only if it doesn't exist create it
                if len(TextClassValue.objects.filter(name=raw_val)) == 0:
                    text_class_value = TextClassValue(name=raw_val)
                    text_class_value.save()
                    vals.append(text_class_value)
            text_class = TextClass()
            text_class.name = name
            text_class.save()
            for val in vals: text_class.values.add(val)
            text_class.save()

    # Create the documents and the TextClassifiedDataset
    for row in df.iterrows():
        row = row[1]
        text = row['text']
        if 'name' in cols:
            name = row['name']
        else:
            name = "NO NAME"

        document = Document()
        document.name = name
        document.text = text
        document.dataset = dataset
        document.save()
        for col in cols:
            col = col
            if col.strip().lower() not in skip_cols:
                val = str(row[col]).strip().lower()
                text_class = TextClass.objects.get(name=col.strip())
                text_class_value = TextClassValue.objects.get(name=val)
                text_classified_dataset = TextClassifiedDataset()
                text_classified_dataset.document = document
                text_classified_dataset.text_class = text_class
                text_classified_dataset.text_class_value = text_class_value
                text_classified_dataset.save()

    dataset.data_imported = True
    dataset.save()
