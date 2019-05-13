import json
import os

from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.staticfiles.templatetags.staticfiles import static

from .models import UseCase
from .cat_train import get_doc, save_doc

DATA_DIR = os.getenv("DATA_DIR", "/tmp/")


def home(request):
    context = {}
    context['usecases'] = UseCase.objects.all()
    context['data_dir'] = DATA_DIR + 'input/' 

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
    for task in usecase.tasks.all():
        tasks[task.name] = []
        for value in task.values.all():
            tasks[task.name].append((value.name, value.value))

    context = {}
    context['tasks'] = tasks
    context['title'] = usecase.title
    in_path = DATA_DIR + "input/" + usecase.folder
    context['data'] = get_doc(params, in_path)
    print(context['data'])

    # Context is now used by the HTML file from Tom
    #print(json.dumps(context, indent=2))

    return render(request, 'app.html', context)


def train_save(request, id=0):
    # This expects a POST request with the data
    usecase = UseCase.objects.get(id=id)
    data = json.loads(request.body)
    in_path = DATA_DIR + "input/" + usecase.folder
    out_path = DATA_DIR + "output/" + usecase.folder

    save_doc(data, in_path, out_path)
    return redirect('train', id)


def upload(request, id=0):
    usecase = UseCase.objects.get(id=id)
    upload_path = f'{DATA_DIR}input/{usecase.folder}'
    for f in request.FILES.values():
        with open(f'{upload_path}/{f.name}', 'wb') as file:
            for bytes in f.chunks():
                file.write(bytes)

    return HttpResponse(status=200)
