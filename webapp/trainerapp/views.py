import datetime
import json
import os
import re
from datetime import datetime
from io import BytesIO
from zipfile import ZipFile
import pathlib

from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from spacy import displacy
from .models import UseCase
from .cat_wrap import CatWrap
from .utils import training_to_file

cat_wrap = CatWrap()

DATA_DIR = os.getenv("DATA_DIR", "/tmp/")

_INPUT_DIR = 'input'
_OUTPUT_DIR = 'output'
_INCOMPLETE_DIR = 'incomplete'


def _in_path(folder):
    return f'{DATA_DIR}{_INPUT_DIR}/{folder}'


def _out_path(folder):
    return f'{DATA_DIR}{_OUTPUT_DIR}/{folder}'


def _incomplete_path(folder):
    return f'{DATA_DIR}{_INCOMPLETE_DIR}/{folder}'


def home(request):
    context = {}
    context['usecases'] = UseCase.objects.all()
    return render(request, 'home.html', context=context)


def train_usecase(request):
    context = {}
    context['usecases'] = UseCase.objects.all()
    return render(request, 'train_usecase.html', context=context)


def train_annotations(request):
    context = {}

    if request.POST and 'text' in request.POST:
        doc_html, doc_json = cat_wrap.get_html_and_json(request.POST['text'])

        context['doc_html'] = doc_html
        context['doc_json'] = doc_json
        context['text'] = request.POST['text']
    return render(request, 'train_annotations.html', context=context)


def train(request, id=0):
    usecase = UseCase.objects.get(id=id)
    params = {}
    params['cuis'] = [x.strip() for x in usecase.cuis.split(",")]
    params['tuis'] = [x.strip() for x in usecase.tuis.split(",")]
    params['tokens'] = [x.strip() for x in usecase.tokens.split(",")]
    params['cntx_tokens'] = [x.strip() for x in usecase.cntx_tokens.split(",")]
    # Type can decide are we showing all spans at once, or using context
    type = usecase.type

    # Get the filters
    filters = []
    for filt in usecase.filters.all():
        filters.append((filt.name, filt.value, filt.acc))
    params['filters'] = filters

    #Get the tasks for this usecase
    tasks = {}
    task_descriptions = {}
    for task in usecase.tasks.all():
        tasks[task.name] = []
        task_descriptions[task.name] = {'description': task.description}
        task_descriptions[task.name]['values'] = {}
        for value in task.values.all():
            tasks[task.name].append((value.name, value.value))
            task_descriptions[task.name]['values'][value.name] = value.description

    context = {}
    context['tasks'] = tasks
    context['title'] = usecase.title
    context['description'] = usecase.description
    context['taskDescriptions'] = task_descriptions
    in_path = DATA_DIR + "input/" + usecase.folder
    # Create input, sometimes it does not exist
    pathlib.Path(_in_path(usecase.folder)).mkdir(parents=True, exist_ok=True)

    context['data'] = cat_wrap.get_doc(params, in_path)

    # Create folders if they don't exist
    pathlib.Path(_out_path(usecase.folder)).mkdir(parents=True, exist_ok=True)
    pathlib.Path(_incomplete_path(usecase.folder)).mkdir(parents=True, exist_ok=True)

    return render(request, 'app.html', context)


def _store_doc(request, id, out_path):
    usecase = UseCase.objects.get(id=id)
    data = json.loads(request.body)
    in_path = _in_path(usecase.folder)
    cat_wrap.save_doc(data, in_path, out_path)
    return redirect('train', id)


def add_cntx(request):
    data = json.loads(request.body)
    cui = data['cui'] # ID of the annotation
    tkn_inds = data['tkn_inds'] # [ind_first, ind_last] - Index of the first and last token
    text = data['text'] # Text of the document
    negative = data['negative'] # 0 or 1 

    cat_wrap.cat.add_concept_cntx(cui=cui, text=text, tkn_inds=tkn_inds, negative=negative)

    # Add the training to file
    tui = ''
    name = cat_wrap.cat.cdb.cui2pretty_name.get(cui, None)
    start_ind = data['char_inds'][0]
    end_ind = data['char_inds'][1]
    train_data_path = os.getenv('TRAIN_DATA', '/tmp/train_anns.csv')
    if cui in cat_wrap.cat.cdb.cui2tui:
        tui = cat_wrap.cat.cdb.cui2tui[cui]
    training_to_file(cui, tui, name, text, start_ind, end_ind, not negative, train_data_path)

    return HttpResponse('')



def save_cdb_model(request):
    cat_wrap.cat.cdb.save_dict(os.getenv('CDB_PATH', '/tmp/cdb.dat'))
    return HttpResponse('')


def reset_cdb_model(request):
    cat_wrap.cat.cdb.load_dict(os.getenv('CDB_PATH', '/tmp/cdb.dat'))
    return HttpResponse('')


def add_concept(request):
    data = json.loads(request.body)
    concept = data['concept']
    text = data.get('text', None)
    tkn_inds = data.get('tkn_inds', None)


    cat_wrap.cat.add_concept(concept, text, tkn_inds)

    return HttpResponse('')


def add_concept_manual(request):
    concept = json.loads(request.body)
    text = concept['text']
    tkn_inds = None
    train_data_path = os.getenv('TRAIN_DATA', '/tmp/train_anns.csv')

    # This is a bit of a hack, the add_concept version should be used in the future
    if text is not None:
        doc = cat_wrap.cat(text)
        for tkn in doc:
            if len(tkn.text.strip()) > 1 and tkn.text.strip() in concept['source_value'].strip():
                tkn_inds = [tkn.i]
                break
    # Find char inds
    start_ind = text.find(concept['source_value'])
    end_ind = start_ind + len(concept['source_value'])
    synonyms = [x for x in concept['synonyms'].split(',') if len(x) > 0]

    cat_wrap.cat.add_concept(concept, text, tkn_inds)
    training_to_file(concept['cui'], concept['tui'], concept['name'], text, start_ind,
                     end_ind, 1, train_data_path, "|".join(synonyms))

    # Add synonyms if they exist
    for synonym in synonyms:
        concept['source_value'] = synonym
        cat_wrap.cat.add_concept(concept, text, tkn_inds)


    return train_annotations(request)


def train_save(request, id=0):
    usecase = UseCase.objects.get(id=id)
    return _store_doc(request, id, _out_path(usecase.folder))


def incomplete(request, id=0):
    usecase = UseCase.objects.get(id=id)
    return _store_doc(request, id, _incomplete_path(usecase.folder))


def upload(request, id=0):
    usecase = UseCase.objects.get(id=id)
    in_path = _in_path(usecase.folder)
    os.makedirs(in_path, exist_ok=True)
    for f in request.FILES.values():
        with open(f'{in_path}/{f.name}', 'wb') as file:
            for bytes in f.chunks():
                file.write(bytes)
    return HttpResponse(status=200)


def download(request, id=0):
    usecase = UseCase.objects.get(id=id)
    output_path = _out_path(usecase.folder)
    incomplete_path = _incomplete_path(usecase.folder)

    download_f_name = ''.join([c for c in usecase.title if re.match(r'\w', c)]) + \
                       datetime.now().strftime('%Y-%m-%d:%H%M') + '.zip'
    s = BytesIO()
    labelled_zip = ZipFile(s, 'w')
    for file_name in os.listdir(output_path):
        labelled_zip.write(os.path.join(output_path, file_name), f'complete/{file_name}')
    for file_name in os.listdir(incomplete_path):
        labelled_zip.write(os.path.join(incomplete_path, file_name), f'incomplete/{file_name}')

    # fix for Linux zip files read in Windows
    for file in labelled_zip.filelist:
        file.create_system = 0

    labelled_zip.close()
    response = HttpResponse(content_type='attachment/zipfile')
    response['Content-Disposition'] = f'attachment; filename={download_f_name}'
    s.seek(0)
    response.write(s.read())
    return response


@csrf_exempt
def api(request):
    errors = []
    annotations = []
    data = json.loads(request.body)
    text = ""
    if 'content' not in data or 'text' not in data['content']:
        errors.append("Wrong input format, please consult the API documentation")
    else:
        text = data['content']['text']
        try:
            annotations = cat_wrap.cat.get_entities(text)
        except Exception as e:
            errors.append(str(e))

    res = {
        "result": {
            "text": text,
            "annotations": annotations,
            "metadata": {},
            "success": True if not errors else False,
            "errors": errors,
        },
        "footer": {}
    }

    return JsonResponse(res)
