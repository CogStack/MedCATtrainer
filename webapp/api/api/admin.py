import copy
import logging
import os
import re
import tarfile
from collections import defaultdict
from datetime import datetime
from glob import glob
from typing import Dict, List

import pkg_resources
from django.contrib.auth.models import User
from django.db.models import QuerySet, Model
from django.http import HttpResponse, HttpResponseRedirect
from io import StringIO
import json
from background_task import background

from django.contrib import admin
from rest_framework.exceptions import PermissionDenied

from .models import *
from .forms import *

admin.site.register(Entity)
admin.site.register(MetaTaskValue)
admin.site.register(MetaTask)
admin.site.register(MetaAnnotation)
admin.site.register(Vocabulary)
admin.site.register(Relation)
admin.site.register(EntityRelation)


def reset_project(modeladmin, request, queryset):
    if not request.user.is_staff:
        raise PermissionDenied

    for project in queryset:
        # Remove all annotations and cascade to meta anns
        AnnotatedEntity.objects.filter(project=project).delete()

        # Remove cui_counts
        ProjectCuiCounter.objects.filter(project=project).delete()

        # Set all validated documents to none
        project.validated_documents.clear()


def download_without_text(modeladmin, request, queryset):
    if not request.user.is_staff:
        raise PermissionDenied

    projects = queryset
    return download_projects_without_text(projects, with_doc_name=False)


def download_without_text_with_doc_names(modeladmin, request, queryset):
    if not request.user.is_staff:
        raise PermissionDenied

    projects = queryset
    return download_projects_without_text(projects, with_doc_name=True)


def download_projects_without_text(projects, with_doc_name):

    all_projects_out = {'projects': []}
    for project in projects:
        out = {}
        out['name'] = project.name
        out['id'] = project.id
        out['cuis'] = project.cuis
        out['documents'] = []

        if project.cuis_file is not None and project.cuis_file:
            # Add cuis from json file if it exists
            cuis_from_file = ",".join(json.load(open(project.cuis_file.path)))
            all_cuis = out['cuis'] + "," + cuis_from_file if len(out['cuis']) > 0 else cuis_from_file
            out['cuis'] = all_cuis

        for doc in project.validated_documents.all():
            out_doc = {}
            out_doc['id'] = doc.id
            out_doc['last_modified'] = str(doc.last_modified)
            out_doc['annotations'] = []
            if with_doc_name:
                out_doc['name'] = doc.name

            anns = AnnotatedEntity.objects.filter(project=project, document=doc)

            for ann in anns:
                out_ann = {}
                out_ann['id'] = ann.id
                out_ann['user'] = ann.user.username
                out_ann['validated'] = ann.validated
                out_ann['correct'] = ann.correct
                out_ann['deleted'] = ann.deleted
                out_ann['alternative'] = ann.alternative
                out_ann['killed'] = ann.killed
                out_ann['irrelevant'] = ann.irrelevant
                out_ann['last_modified'] = str(ann.last_modified)
                out_ann['manually_created'] = ann.manually_created
                out_ann['acc'] = ann.acc
                if ann.icd_code:
                    out_ann['icd_code'] = ann.icd_code.code
                if ann.opcs_code:
                    out_ann['opcs_code'] = ann.opcs_code.code
                out_ann['meta_anns'] = {}

                # Get MetaAnnotations
                meta_anns = MetaAnnotation.objects.filter(annotated_entity=ann)
                for meta_ann in meta_anns:
                    o_meta_ann = {}
                    o_meta_ann['name'] = meta_ann.meta_task.name
                    o_meta_ann['value'] = meta_ann.meta_task_value.name
                    o_meta_ann['acc'] = meta_ann.acc
                    o_meta_ann['validated'] = meta_ann.validated

                    # Add annotation
                    key = meta_ann.meta_task.name
                    out_ann['meta_anns'][key] = o_meta_ann

                out_doc['annotations'].append(out_ann)
            out['documents'].append(out_doc)
        all_projects_out['projects'].append(out)

    sio = StringIO()
    json.dump(all_projects_out, sio)
    sio.seek(0)

    f_name = "MedCAT_Export_No_Text_{}.json".format(datetime.now().strftime('%Y-%m-%d:%H:%M:%S'))
    response = HttpResponse(sio, content_type='text/json')
    response['Content-Disposition'] = 'attachment; filename={}'.format(f_name)
    return response


_dt_fmt = '%Y-%m-%d::%H:%M-%z'


def download_deployment_export(data_only=False):
    """
    Packages projects, annotations, meta-annotations etc. into a flat list of linked entities,
    ready to be downloaded and imported into a new trainer instance
    :param projects:
    :return: dict:
    """
    def clean_dict(d, keys=None):
        filter_keys = ['_state', 'id']
        if keys is not None:
            filter_keys += keys
        return {k: v for k, v in d.items() if k not in filter_keys}

    def extract_model_dict(model, date_keys: List[str]=None, m2m_fields: List[str]=None):
        date_keys = date_keys if date_keys else []
        m2m_fields = m2m_fields if m2m_fields else []
        out_dict = {}
        for m in model.objects.all():
            m_dict = {k: v.strftime(_dt_fmt) if k in date_keys else v for k, v in clean_dict(m.__dict__).items()}
            for k in m2m_fields:
                m_dict[k] = [m2m_f['id'] for m2m_f in getattr(model.objects.get(id=m.id), k).values()]
            out_dict[m.id] = m_dict
        return out_dict

    user_keys = ['username', 'first_name', 'last_name', 'email', 'is_staff', 'is_active']
    users_map = {u.id: {k: v for k, v in u.__dict__.items() if k in user_keys} for u in User.objects.all()}

    project_anno_map = extract_model_dict(ProjectAnnotateEntities, ['create_time'],
                                          ['members', 'validated_documents', 'cdb_search_filter', 'tasks'])
    project_anno_map = {p_id: dict(p_val, **{'members': [v['id'] for v in
                                                         ProjectAnnotateEntities.objects.get(id=p_id).members.values()]})
                        for p_id, p_val in project_anno_map.items()}
    project_cui_file_map = {p.cuis_file.path: p.id for p in
                            ProjectAnnotateEntities.objects.exclude(cuis_file__exact="")}

    annos_map = extract_model_dict(AnnotatedEntity, ['last_modified', 'create_time'])
    document_map = extract_model_dict(Document, ['create_time', 'last_modified'])
    meta_anno_tasks_map = extract_model_dict(MetaTask, [], ['values'])
    meta_anno_values_map = extract_model_dict(MetaTaskValue)
    meta_annos_map = extract_model_dict(MetaAnnotation)
    dataset_filename_map = {d.original_file.path: d.id for d in Dataset.objects.all()}
    dataset_map = extract_model_dict(Dataset, ['create_time'])
    entities_map = extract_model_dict(Entity)

    # concepts table is intentionally ignored: [ {'cdb': 2 i.e. the id} ]
    cdbs_imported = list(Concept.objects.values('cdb').distinct())
    cdbs = extract_model_dict(ConceptDB)
    cdbs_file_map = {c.cdb_file.path: c.id for c in ConceptDB.objects.all()}

    vocabs = extract_model_dict(Vocabulary)
    vocab_file_map = {v.vocab_file.path: v.id for v in Vocabulary.objects.all()}

    # tar gz, the entire thing
    export = {
        'users': users_map,
        'projects': project_anno_map,
        'annos': annos_map,
        'meta_annos': meta_annos_map,
        'meta_anno_tasks': meta_anno_tasks_map,
        'meta_anno_values': meta_anno_values_map,
        'dataset_map': dataset_map,
        'datasets_file_to_id': dataset_filename_map,
        'documents_map': document_map,
        'entities_map': entities_map,
        'cdbs_imported': cdbs_imported,
        'cdbs': cdbs,
        'cdb_files_to_id': cdbs_file_map,
        'vocabs': vocabs,
        'vocabs_file_to_id': vocab_file_map,
        'project_cui_file_to_id': project_cui_file_map,
        'medcat_version': [p.version for p in pkg_resources.working_set if p.project_name == 'medcat'][0],
        'medcattrainer_version': '1.0'  # TODO: source from setup.py?
    }

    filename = 'mc_trainer_deployment_export.tar.gz'
    try:
        # write everything to a tar.gz
        with tarfile.open(filename, 'w:gz') as tar:
            json.dump(export, open('data.json', 'w'))
            tar.add('data.json')
            if not data_only:
                for d_path in dataset_filename_map.keys():
                    tar.add(d_path, arcname=f'datasets/{d_path.split("/")[-1]}')
                for cdb_file_path in cdbs_file_map.keys():
                    tar.add(cdb_file_path, arcname=f'cdbs/{cdb_file_path.split("/")[-1]}')
                for vocab_file_path in vocab_file_map.keys():
                    tar.add(vocab_file_path, arcname=f'vocabs/{vocab_file_path.split("/")[-1]}')
                for project_cui_file_path in project_cui_file_map.keys():
                    tar.add(project_cui_file_path, arcname=f'project_cui_files/{project_cui_file_path.split("/")[-1]}')

        # clean up
        os.remove('data.json')
        file_loaded = open(filename, 'rb')
        response = HttpResponse(file_loaded.read(), content_type='application/x-gzip')
        file_loaded.close()
        response['Content-Type'] = 'application/octet-stream'
        # response['Content-Length'] = str(os.stat(filename).st_size)
        response['Content-Encoding'] = 'tar'
        response['Content-Disposition'] = 'attachment; filename={}'.format(filename)
        return response
    finally:
        try:
            os.remove(filename)
        except FileNotFoundError:
            pass


def upload_deployment_export(filename: str):
    prfx = f'{settings.MEDIA_ROOT}/prev_deployment'
    with tarfile.open(filename, 'r:gz') as f:
        os.makedirs(prfx, exist_ok=True)
        f.extractall(prfx)

    dep_map = json.load(open(f'{prfx}/data.json'))

    # check medcat major version is consistent
    curr_ver = [p.version for p in pkg_resources.working_set if p.project_name == 'medcat'][0]
    compatible_mc_ver = curr_ver.split('.')[0] == dep_map['medcat_version'].split('.')[0]

    def _remap_model_data(model, dep_map_key, time_fields=None, foreign_key_fields=None,
                          file_names=None, file_name_attr='', filename_map_prev_id=None,
                          idempotent_model_save=True):
        remapped_models = {}
        mappings = dep_map[dep_map_key]

        time_fields = time_fields if time_fields else []
        foreign_key_fields = foreign_key_fields if foreign_key_fields else []

        errors = [f'Errors for: {model}']
        # fileField mappings
        filename_map_prev_id = filename_map_prev_id if filename_map_prev_id else {}
        file_names = file_names if file_names else []
        for file_path in file_names:
            m = model()
            setattr(m, file_name_attr, file_path)
            file_name = file_path.split('/')[-1]
            prev_model_id = [v for k, v in filename_map_prev_id.items() if k.split('/')[-1] == file_name][0]
            remapped_models[str(prev_model_id)] = m
            del mappings[str(prev_model_id)][file_name_attr]

        for prev_model_id, model_data in mappings.items():
            m = model() if prev_model_id not in remapped_models else remapped_models[prev_model_id]
            f_key_fields = [f[0] for f in foreign_key_fields]
            vals_to_set = {}
            for m_k, m_v in model_data.items():
                m_k = re.sub(r'_id$', '', m_k)
                if 'polymorphic_ctype' in m_k or 'project_ptr' == m_k or m_v is None:
                    continue
                if m_k not in f_key_fields:
                    if m_k in time_fields:
                        m_v = datetime.strptime(m_v, _dt_fmt)
                    try:
                        setattr(m, m_k, m_v)
                    except Exception:
                        errors.append(f'Error setting prop: {m_k} onto with val:{m_v},' +
                                      'has this prop been removed / changed?')
                else:
                    _, f_key_model, f_key_type, remap_dict = foreign_key_fields[f_key_fields.index(m_k)]
                    if f_key_type == 'FK':
                        try:
                            m_v = f_key_model.objects.get(id=remap_dict[str(m_v)].id)
                            setattr(m, m_k, m_v)
                        except Exception:
                            errors.append(f'Error attempting to map prop: {m_k} onto with val:{m_v}' +
                                          f'as foreign key from {f_key_model}. Has this prop been removed / changed?')
                    elif f_key_type == 'M2M':
                        try:
                            vals_to_set[m_k] = f_key_model.objects.filter(id__in=[remap_dict[str(v)].id for v in m_v])
                        except KeyError as e:
                            errors.append(f'Error attempting to map prop: {m_k} onto with val:{m_v}' +
                                          f'as M2M key from {f_key_model}. Has this prop been removed / changed?')
            remapped_models[prev_model_id] = m
            m.save()
            if idempotent_model_save:  # Cannot have save signal and m2m fields on a model...
                for m2m_field, vals in vals_to_set.items():
                    getattr(m, m2m_field).set(vals)
                m.save()

        if len(errors) == 1:
            errors = []
        return remapped_models, errors

    # User model probably doesn't work without a password
    errs = []

    cdb_files = [cdb_file for cdb_file in glob(f'{prfx}/cdbs/*')]
    remapped_cdbs, cdb_errs = _remap_model_data(ConceptDB, 'cdbs', time_fields=[], foreign_key_fields=[],
                                                file_names=cdb_files, file_name_attr='cdb_file',
                                                filename_map_prev_id=dep_map['cdb_files_to_id'])
    errs += cdb_errs

    vocab_files = [vocab_file for vocab_file in glob(f'{prfx}/vocabs/*')]
    remapped_vocabs, voc_errs = _remap_model_data(Vocabulary, 'vocabs', time_fields=[], foreign_key_fields=[],
                                                  file_names=vocab_files, file_name_attr='vocab_file',
                                                  filename_map_prev_id=dep_map['vocabs_file_to_id'])
    errs += voc_errs

    dataset_files = [dataset_file for dataset_file in glob(f'{prfx}/datasets/*')]
    remapped_datasets, ds_errs = _remap_model_data(Dataset, 'dataset_map', time_fields=['create_time'], foreign_key_fields=[],
                                                   file_names=dataset_files, file_name_attr='original_file',
                                                   filename_map_prev_id=dep_map['datasets_file_to_id'],
                                                   idempotent_model_save=False)
    errs += ds_errs
    # documents will be re-created, by each new dataset. Re-map each old document id to their new id.
    prev_dataset_id_to_doc_ids = defaultdict(list)
    prev_dataset_id_to_texts = defaultdict(list)
    for d_id, ds in dep_map['documents_map'].items():
        prev_dataset_id_to_doc_ids[str(ds['dataset_id'])].append(d_id)
        prev_dataset_id_to_texts[str(ds['dataset_id'])].append(ds['text'])

    remapped_documents = {}
    for prev_ds_id, new_ds in remapped_datasets.items():
        texts = prev_dataset_id_to_texts[prev_ds_id]
        prev_doc_ids = prev_dataset_id_to_doc_ids[prev_ds_id]
        for t, prev_id in zip(texts, prev_doc_ids):
            docs = Document.objects.filter(dataset=new_ds).filter(text=t)
            if len(docs) == 1:
                remapped_documents[prev_id] = docs[0]
            elif len(docs) > 1:
                remapped_documents[prev_id] = docs[0]
                errs.append('DatasetError: Found multiple documents associated with '
                            f'Prev Dataset:{prev_id}, DocNames:{[d.name for d in docs]}')
            else:
                errs.append(f'DatasetError: Cannot find doc, prev_id:{prev_id}')

    remapped_entities, ent_errs = _remap_model_data(Entity, 'entities_map')
    errs += ent_errs

    # remove any users with same username
    User.objects.filter(username__in=[u['username'] for u in dep_map['users'].values()]).delete()
    remapped_users, usr_errs = _remap_model_data(User, 'users')
    errs += usr_errs
    for user in remapped_users.values():
        user.set_password('')

    remapped_meta_values, meta_vals_errs = _remap_model_data(MetaTaskValue, 'meta_anno_values')
    errs += meta_vals_errs
    remapped_meta_tasks, meta_tasks_errs = _remap_model_data(MetaTask, 'meta_anno_tasks', time_fields=[],
                                                             foreign_key_fields=[('values', MetaTaskValue, 'M2M', remapped_meta_values),
                                                                                 ('default', MetaTaskValue, 'FK', remapped_meta_values)])
    errs += meta_tasks_errs

    cui_files = [cui_file for cui_file in glob(f'{prfx}/project_cui_files/*')]
    remapped_projects, projs_errs = _remap_model_data(ProjectAnnotateEntities, 'projects', time_fields=['create_time'],
                                                      foreign_key_fields=[('dataset', Dataset, 'FK', remapped_datasets),
                                                                          ('validated_documents', Document, 'M2M', remapped_documents),
                                                                          ('members', User, 'M2M', remapped_users),
                                                                          ('concept_db', ConceptDB, 'FK', remapped_cdbs),
                                                                          ('vocab', Vocabulary, 'FK', remapped_vocabs),
                                                                          ('cdb_search_filter', ConceptDB, 'M2M', remapped_cdbs),
                                                                          ('tasks', MetaTask, 'M2M', remapped_meta_tasks)],
                                                      file_names=cui_files, file_name_attr='cuis_file',
                                                      filename_map_prev_id=dep_map['project_cui_file_to_id'])
    errs += projs_errs

    remapped_annotations, annos_errs = _remap_model_data(AnnotatedEntity, 'annos', time_fields=['create_time', 'last_modified'],
                                                         foreign_key_fields=[('project', Project, 'FK', remapped_projects),
                                                                             ('user', User, 'FK', remapped_users),
                                                                             ('document', Document, 'FK', remapped_documents),
                                                                             ('entity', Entity, 'FK', remapped_entities)])
    errs += annos_errs

    remapped_meta_annos, meta_anno_errs = _remap_model_data(MetaAnnotation, 'meta_annos', time_fields=[],
                                                            foreign_key_fields=[('annotated_entity', AnnotatedEntity, 'FK', remapped_annotations),
                                                                                ('meta_task', MetaTask, 'FK', remapped_meta_tasks),
                                                                                ('meta_task_value', MetaTaskValue, 'FK', remapped_meta_values)])
    errs += meta_anno_errs
    return errs


def download(modeladmin, request, queryset):
    if not request.user.is_staff:
        raise PermissionDenied
    projects = queryset
    return download_projects_with_text(projects)


def download_projects_with_text(projects: QuerySet):
    all_projects = _retrieve_project_data(projects)

    sio = StringIO()
    json.dump(all_projects, sio)
    sio.seek(0)

    f_name = "MedCAT_Export_With_Text_{}.json".format(datetime.now().strftime('%Y-%m-%d:%H:%M:%S'))
    response = HttpResponse(sio, content_type='text/json')
    response['Content-Disposition'] = 'attachment; filename={}'.format(f_name)

    return response


def _retrieve_project_data(projects: QuerySet) -> Dict[str, List]:
    """
    A function to convert a list of projects and:
        - their associated documents,
        - their associated annotations,
        - their associated Meta annotations and Relation Annotations
    for serialization.
    :param projects: the projects to export data for.
    Output schema is as follows: ((optional) indicates this field isn't required for training a MedCAT model)
    {
    "projects": [
        {
            "name": "<project_name"  # name of the project
            "id": "<id>"  # the auto-generated id of the project (optional)
            "cuis": ["cui_1", "cui_2" ... ]  # the CUI filter for the project, includes those from file / and text-box
            "documents": [
                {
                "id": "<id>"  # the auto-generated id of the document (optional)
                "name": "<name>"  # the name of the document (optional), but used in stat printing during training
                "text": "<text>"  # the text of the document
                "last_modified": "<date time>"  # the last modified-time (optional)
                "annotations": [{
                    "id": "<id>"  # the auto-generated id of the document (optional)
                    "name": "<username string>"  # the user who made the annotation (optional)
                    "cui": "<cui string>"  # the cui label for this annotation
                    "value": "<string>"  # the text span for this annotation
                    "start": <integer>  # the start index of this annotation with respect to the document text
                    "end": <integer>  # the end index of this annotation with respect to the document text
                    "validated": <boolean>  # if the annotation has been marked by a human annotator
                    "correct": <boolean>  # if the text span is correctly linked to the CUI of this annotation
                    "deleted": <boolean>  # if the text span was incorrectly linked or 'not' linked by MedCAT due to low scores
                    "alternative": <boolean>  # if the text span was incorrectly linked by MedCAT, then correctly linked by a human annotator
                    "killed":  <boolean>  # if a human annotator 'terminated' this annotation
                    "irrelevant": <boolean>  # if a human annotator has marked an annotation as irrelvant (optional)
                    "acc": <float>  # accuracy provided by MedCAT (optional)
                    "comment": "<comment string>" # the text entered by an annotator during annotation (optional)
                    "meta_anns": [
                        # list of meta annotations if applicable to project
                        {
                            "name": <string>  # Meta anno task name, i.e. temporality
                            "value": <string>  # the selected meta anno task value for, ie. "past" or "present"
                            "acc":  <float>   # default 1, (optional)
                            "validated": <boolean>  # Meta annotation has been made by a human annotator, default (true)
                        },
                        ... <more meta annotations of the same as above structure>
                    ]},
                    ... <more annotations of the same above structure>
                ]
                "relations": [
                    {
                        "start_entity": <integer>  # id of above annotation that is the start of this relation
                        "start_entity_cui": "<string>" # the cui label of the start of this relation
                        "start_entity_value": <string>  # value of the start annotation for this relation
                        "start_entity_start_idx": <integer>  # start index of text span of start of relation
                        "start_entity_end_idx": <integer>  # end index of text span of start of relation
                        "end_entity": <integer>  # id of the above annotation that is the end of this relation
                        "end_entity_cui": "<string>" # the cui label of the end of this relation
                        "end_entity_value": <string>  # value of the end annotation for this relation
                        "end_entity_start_idx": <integer>  # end index of text span of end of relation
                        "end_entity_end_idx": <integer>  # end index of text span of end of relation
                        "user": <string>  # username of annotator for relation (optional)
                        "relation": <string>  # label for this relation
                        "validated": <boolean>  # if the annotation has been validated by a human annotator, default true.
                    }
                    ... < more relations of the samve above structure>
                ]

                ... <more documents of the same above structure>
            ]
    ]
    }

    :return: dict
    """
    all_projects = {'projects': []}
    for project in projects:
        out = {}
        out['name'] = project.name
        out['id'] = project.id
        out['cuis'] = project.cuis
        out['documents'] = []

        if project.cuis_file is not None and project.cuis_file:
            # Add cuis from json file if it exists
            cuis_from_file = ",".join(json.load(open(project.cuis_file.path)))
            all_cuis = out['cuis'] + "," + cuis_from_file if len(out['cuis']) > 0 else cuis_from_file
            out['cuis'] = all_cuis

        for doc in project.validated_documents.all():
            out_doc = {}
            out_doc['id'] = doc.id
            out_doc['name'] = doc.name
            out_doc['text'] = doc.text
            out_doc['last_modified'] = str(doc.last_modified)
            out_doc['annotations'] = []

            anns = AnnotatedEntity.objects.filter(project=project, document=doc)

            for ann in anns:
                out_ann = {}
                out_ann['id'] = ann.id
                out_ann['user'] = ann.user.username
                out_ann['cui'] = ann.entity.label
                out_ann['value'] = ann.value
                out_ann['start'] = ann.start_ind
                out_ann['end'] = ann.end_ind
                out_ann['validated'] = ann.validated
                out_ann['correct'] = ann.correct
                out_ann['deleted'] = ann.deleted
                out_ann['alternative'] = ann.alternative
                out_ann['killed'] = ann.killed
                out_ann['irrelevant'] = ann.irrelevant
                out_ann['last_modified'] = str(ann.last_modified)
                out_ann['manually_created'] = ann.manually_created
                out_ann['acc'] = ann.acc
                if ann.comment:
                    out_ann['comment'] = ann.comment
                if ann.icd_code:
                    out_ann['icd_code'] = ann.icd_code.code
                if ann.opcs_code:
                    out_ann['opcs_code'] = ann.opcs_code.code
                out_ann['meta_anns'] = {}

                # Get MetaAnnotations
                meta_anns = MetaAnnotation.objects.filter(annotated_entity=ann)
                for meta_ann in meta_anns:
                    o_meta_ann = {}
                    o_meta_ann['name'] = meta_ann.meta_task.name
                    o_meta_ann['value'] = meta_ann.meta_task_value.name
                    o_meta_ann['acc'] = meta_ann.acc
                    o_meta_ann['validated'] = meta_ann.validated

                    # Add annotation
                    key = meta_ann.meta_task.name
                    out_ann['meta_anns'][key] = o_meta_ann

                out_doc['annotations'].append(out_ann)

            # Add relations if they exist
            rels = EntityRelation.objects.filter(project=project, document=doc)
            out_rels = []
            out_rel = {}
            for rel in rels:
                out_rel['start_entity'] = rel.start_entity.id
                out_rel['start_entity_cui'] = rel.start_entity.cui
                out_rel['start_entity_value'] = rel.tart_entity.value
                out_rel['start_entity_start_idx'] = rel.start_entity.start_ind
                out_rel['start_entity_end_idx'] = rel.start_entity.end_ind
                out_rel['end_entity'] = rel.end_entity.id
                out_rel['end_entity_cui'] = rel.end_entity.cui
                out_rel['end_entity_value'] = rel.end_entity.value
                out_rel['end_entity_start_idx'] = rel.end_entity.start_ind
                out_rel['end_entity_end_idx'] = rel.end_entity.end_ind
                out_rel['user'] = rel.user.username
                out_rel['relation'] = rel.relation.label
                out_rel['validated'] = rel.validated

                out_rels.append(out_rel)
                out_rel = {}
            out_doc['relations'] = out_rels

            out['documents'].append(out_doc)
        all_projects['projects'].append(out)
    return all_projects


def clone_projects(modeladmin, request, queryset):
    if not request.user.is_staff:
        raise PermissionDenied

    projects = queryset
    for project in projects:
        project_copy = copy.copy(project)
        project_copy.id = None
        project_copy.pk = None
        project_copy.name = f'{project.name} (Clone)'
        project_copy.save()

        # Add M2M fields
        for m in project.members.all():
            project_copy.members.add(m)
        for c in project.cdb_search_filter.all():
            project_copy.cdb_search_filter.add(c)
        for t in project.tasks.all():
            project_copy.tasks.add(t)

        project_copy.save()


class ReportErrorModelAdminMixin:
    """Mixin to catch all errors in the Django Admin and map them to user-visible errors."""
    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        try:
            return super().changeform_view(request, object_id, form_url, extra_context)
        except Exception as e:
            self.message_user(request, f'Error with previous action: {e}', level=logging.ERROR)
            return HttpResponseRedirect(request.path)


class DatasetAdmin(ReportErrorModelAdminMixin, admin.ModelAdmin):
    model = Dataset
admin.site.register(Dataset, DatasetAdmin)


class ProjectAnnotateEntitiesAdmin(admin.ModelAdmin):
    model = ProjectAnnotateEntities
    actions = [download, download_without_text, download_without_text_with_doc_names, reset_project, clone_projects]

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "concept_db":
            kwargs["queryset"] = ConceptDB.objects.filter(use_for_training=True)
        return super(ProjectAnnotateEntitiesAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "cdb_search_filter":
            #kwargs["queryset"] = ConceptDB.objects.filter(use_for_training=False)
            kwargs["queryset"] = ConceptDB.objects.all()

        return super(ProjectAnnotateEntitiesAdmin, self).formfield_for_manytomany(db_field, request, **kwargs)
admin.site.register(ProjectAnnotateEntities, ProjectAnnotateEntitiesAdmin)


class AnnotatedEntityAdmin(admin.ModelAdmin):
    list_display = ('user', 'project', 'entity', 'value', 'deleted', 'validated')
    list_filter = ('user', 'project', 'deleted', 'validated')
    model = AnnotatedEntity
admin.site.register(AnnotatedEntity, AnnotatedEntityAdmin)


@background(schedule=5)
def _import_concepts(id):
    from medcat.cdb import CDB
    concept_db = ConceptDB.objects.get(id=id)
    cdb = CDB.load(concept_db.cdb_file.path)

    # Get all existing cuis for this CDB
    existing_cuis = set(Concept.objects.filter(cdb=id).values_list('cui', flat=True))

    for cui in cdb.cui2names.keys():
        if cui not in existing_cuis:
            concept = Concept()
            concept.pretty_name = cdb.get_name(cui)
            concept.cui = cui
            concept.type_ids = ','.join(list(cdb.cui2type_ids.get(cui, '')))
            concept.semantic_type = ','.join([cdb.addl_info['type_id2name'].get(type_id, '')
                                              for type_id in list(cdb.cui2type_ids.get(cui, ''))])
            concept.desc = cdb.addl_info['cui2description'].get(cui, '')
            concept.synonyms = ", ".join(cdb.addl_info['cui2original_names'].get(cui, []))
            concept.cdb = concept_db
            concept.save()


@background(schedule=5)
def _reset_cdb_filters(id):
    from medcat.cdb import CDB
    concept_db = ConceptDB.objects.get(id=id)
    cdb = CDB.load(concept_db.cdb_file.path)
    cdb.config.linking['filters'] = {'cuis': set()}
    cdb.save(concept_db.cdb_file.path)


def reset_cdb_filters(modeladmin, request, queryset):
    for concept_db in queryset:
        _reset_cdb_filters(concept_db.id)


def import_concepts(modeladmin, request, queryset):
    for concept_db in queryset:
        _import_concepts(concept_db.id)


def delete_concepts_from_cdb(modeladmin, request, queryset):
    for concept_db in queryset:
        Concept.objects.filter(cdb=concept_db).delete()
        ICDCode.objects.filter(cdb=concept_db).delete()
        OPCSCode.objects.filter(cdb=concept_db).delete()


class ConceptDBAdmin(admin.ModelAdmin):
    model = ConceptDB
    actions = [import_concepts, delete_concepts_from_cdb, reset_cdb_filters]

admin.site.register(ConceptDB, ConceptDBAdmin)


def remove_all_concepts(modeladmin, request, queryset):
    Concept.objects.all().delete()


class ConceptAdmin(admin.ModelAdmin):
    model = Concept
    list_filter = ('cdb',)
    actions = [remove_all_concepts]


admin.site.register(Concept, ConceptAdmin)
admin.site.register(ICDCode)
admin.site.register(OPCSCode)


class ProjectCuiCounterAdmin(admin.ModelAdmin):
    model = ProjectCuiCounter
    list_filter = ('project',)
    list_display = ['entity', 'count', 'project']
admin.site.register(ProjectCuiCounter, ProjectCuiCounterAdmin)

def remove_all_documents(modeladmin, request, queryset):
    Document.objects.all().delete()

class DocumentAdmin(admin.ModelAdmin):
    model = Document
    actions = [remove_all_documents]
    list_display = ['name', 'create_time', 'dataset', 'last_modified']

admin.site.register(Document, DocumentAdmin)
