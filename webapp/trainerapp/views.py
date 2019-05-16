import datetime
import json
import os
import re
from datetime import datetime
from io import BytesIO
from zipfile import ZipFile

from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.staticfiles.templatetags.staticfiles import static

from .models import UseCase
from .cat_train import get_doc, save_doc

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
    context['data'] = get_doc(params, in_path)
    print(context['data'])

    return render(request, 'app.html', context)


def train_save(request, id=0):
    # This expects a POST request with the data
    usecase = UseCase.objects.get(id=id)
    data = json.loads(request.body)
    in_path = _in_path(usecase.folder)
    out_path = _out_path(usecase.folder)
    save_doc(data, in_path, out_path)
    return redirect('train', id)


def upload(request, id=0):
    usecase = UseCase.objects.get(id=id)
    in_path = _in_path(usecase.folder)
    os.makedirs(in_path, exist_ok=True)
    for f in request.FILES.values():
        with open(f'{in_path}/{f.name}', 'wb') as file:
            for bytes in f.chunks():
                file.write(bytes)
    return HttpResponse(status=200)


def incomplete(request, id=0):
    # TODO: Should this be any different to upload?
    # ideally we'd want to know where the entities are that CAT has missed?
    # log somewhere or we get an alert??
    usecase = UseCase.objects.get(id=id)
    incomplete_path = _incomplete_path(usecase.folder)
    os.makedirs(incomplete_path, exist_ok=True)
    for f in request.FILES.values():
        with open(f'{incomplete_path}/{f.name}', 'wb') as file:
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


