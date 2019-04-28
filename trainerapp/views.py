from django.shortcuts import render
from django.contrib.staticfiles.templatetags.staticfiles import static
from .models import UseCase

TEST = {'text': 'sp. significantly reducing (60%) the number of parasites in the fish. This article is protected by copyright. All',
 'f_name': '1.json',
 'entities': [{'id': 1,
   'start_tkn': 2,
   'end_tkn': 3,
   'start_ind': 4,
   'end_ind': 26,
   'label': 'C3890174',
   'source_value': 'significantly reducing',
   'acc': '0.4987738',
   'cui': 'C3890174',
   'tui': 'T038',
   'type': 'Biologic Function',
   'cntx': {'text': 'sp. significantly reducing (60%) the',
    'cntx_ent_start': 4,
    'cntx_ent_end': 26}},
  {'id': 3,
   'start_tkn': 11,
   'end_tkn': 11,
   'start_ind': 47,
   'end_ind': 56,
   'label': 'C0030498',
   'source_value': 'parasites',
   'acc': '1',
   'cui': 'C0030498',
   'tui': 'T204',
   'type': 'Eukaryote',
   'cntx': {'text': '%) the number of parasites in the fish. This',
    'cntx_ent_start': 17,
    'cntx_ent_end': 26}},
  {'id': 6,
   'start_tkn': 17,
   'end_tkn': 17,
   'start_ind': 75,
   'end_ind': 82,
   'label': 'C1706852',
   'source_value': 'article',
   'acc': '0.5611645',
   'cui': 'C1706852',
   'tui': 'T170',
   'type': 'Intellectual Product',
   'cntx': {'text': 'in the fish. This article is protected by copyright.',
    'cntx_ent_start': 18,
    'cntx_ent_end': 25}}]}

def home(request):
    context = {}
    context['usecases'] = UseCase.objects.all()

    return render(request, 'home.html', context=context)

def train(request, id=0):
    usecase = UseCase.objects.get(id=id)

    cuis = [x.strip() for x in usecase.cuis.split(",")]
    tuis = [x.strip() for x in usecase.tuis.split(",")]
    tokens = [x.strip() for x in usecase.tokens.split(",")]
    cntx_tokens = [x.strip() for x in usecase.cntx_tokens.split(",")]
    # Type can decide are we showing all spans at once, or using context
    type = usecase.type

    # Get the filters
    filters = []
    for filt in usecase.filters.all():
        filters.append((filt.name, filt.value, filt.acc))

    #Get the tasks for this usecase
    tasks = {}
    for task in usecase.tasks.all():
        tasks[task.name] = []
        for value in task.values.all():
            tasks[task.name].append((value.name, value.value))

    # Now get the training data from json files
    print(usecase, cuis, tuis, tokens, filters, tasks)

    context = {}
    context['tasks'] = tasks
    context['title'] = usecase.title
    context['data'] = TEST

    # Context is now used by the HTML file from Tom
    print(context)

    return render(request, 'home.html', context)

