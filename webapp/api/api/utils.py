import json
import logging
import os
from typing import Union, Dict, List, Type

import pkg_resources
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from medcat.cat import CAT
from medcat.cdb import CDB
from medcat.utils.filters import check_filters
from medcat.utils.helpers import tkns_from_doc
from medcat.vocab import Vocab

from .models import Entity, AnnotatedEntity, ICDCode, OPCSCode, ProjectAnnotateEntities, ProjectCuiCounter, \
    ConceptDB

log = logging.getLogger('trainer')


def remove_annotations(document, project, partial=False):
    try:
        if partial:
            # Removes only the ones that are not validated
            AnnotatedEntity.objects.filter(project=project,
                                           document=document,
                                           validated=False).delete()
            log.debug(f"Unvalidated Annotations removed for:{document.id}")
        else:
            # Removes everything
            AnnotatedEntity.objects.filter(project=project, document=document).delete()
            log.debug(f"All Annotations removed for:{document.id}")
    except Exception as e:
        log.debug(f"Something went wrong: {e}")


def add_annotations(spacy_doc, user, project, document, existing_annotations, cat):
    spacy_doc._.ents.sort(key=lambda x: len(x.text), reverse=True)

    tkns_in = []
    ents = []
    existing_annos_intervals = [(ann.start_ind, ann.end_ind) for ann in existing_annotations]

    def check_ents(ent):
        return any((ea[0] < ent.start_char < ea[1]) or
                   (ea[0] < ent.end_char < ea[1]) for ea in existing_annos_intervals)

    for ent in spacy_doc._.ents:
        if not check_ents(ent) and check_filters(ent._.cui, cat.config.linking['filters']):
            to_add = True
            for tkn in ent:
                if tkn in tkns_in:
                    to_add = False
            if to_add:
                for tkn in ent:
                    tkns_in.append(tkn)
                ents.append(ent)

    for ent in ents:
        label = ent._.cui

        if not Entity.objects.filter(label=label).exists():
            # Create the entity
            entity = Entity()
            entity.label = label
            entity.save()
        else:
            entity = Entity.objects.get(label=label)

        cui_count_limit = cat.config.general.get("cui_count_limit", -1)
        pcc = ProjectCuiCounter.objects.filter(project=project, entity=entity).first()
        if pcc is not None:
            cui_count = pcc.count
        else:
            cui_count = 1

        if cui_count_limit < 0 or cui_count <= cui_count_limit:
            if AnnotatedEntity.objects.filter(project=project,
                                              document=document,
                                              start_ind=ent.start_char,
                                              end_ind=ent.end_char).count() == 0:
                # If this entity doesn't exist already
                ann_ent = AnnotatedEntity()
                ann_ent.user = user
                ann_ent.project = project
                ann_ent.document = document
                ann_ent.entity = entity
                ann_ent.value = ent.text
                ann_ent.start_ind = ent.start_char
                ann_ent.end_ind = ent.end_char
                ann_ent.acc = ent._.context_similarity

                MIN_ACC = cat.config.linking.get('similarity_threshold_trainer', 0.2)
                if ent._.context_similarity < MIN_ACC:
                    ann_ent.deleted = True
                    ann_ent.validated = True

                ann_ent.save()


def _create_linked_codes(mod: Union[Type[ICDCode], Type[OPCSCode]], linked_codes: List[Dict], cdb_model: ConceptDB):
    """
    Expects the cui2icd10, cui2opcs4 dicts to include code and name.
    """
    for code in linked_codes:
        if len(mod.objects.filter(code=code['code'])) == 0:
            code_mod = mod()
            code_mod.code = code['code']
            code_mod.desc = code['name']
            code_mod.cdb = cdb_model
            code_mod.save()


def create_linked_icd_codes(codes: List, cdb_model):
    _create_linked_codes(ICDCode, codes, cdb_model)


def create_linked_opcs_codes(codes: List, cdb_model):
    _create_linked_codes(OPCSCode, codes, cdb_model)


def get_create_cdb_infos(cdb, concept, cui, cui_info_prop, code_prop, desc_prop, model_clazz):
    codes = [c[code_prop] for c in cdb.cui2info.get(cui, {}).get(cui_info_prop, []) if code_prop in c]
    existing_codes = model_clazz.objects.filter(code__in=codes)
    codes_to_create = set(codes) - set([c.code for c in existing_codes])
    for code in codes_to_create:
        new_code = model_clazz()
        new_code.code = code
        descs = [c[desc_prop] for c in cdb.cui2info[cui][cui_info_prop]
                 if c[code_prop] == code]
        if len(descs) > 0:
            new_code.desc = [c[desc_prop] for c in cdb.cui2info[cui][cui_info_prop]
                             if c[code_prop] == code][0]
            new_code.cdb = concept.cdb
            new_code.save()
    return model_clazz.objects.filter(code__in=codes)


def _remove_overlap(project, document, start, end):
    anns = AnnotatedEntity.objects.filter(project=project, document=document)

    for ann in anns:
        if (start <= ann.start_ind <= end) or (start <= ann.end_ind <= end):
            log.debug("Removed %s ", str(ann))
            ann.delete()


def create_annotation(source_val: str, selection_occurrence_index: int, cui: str, user: User,
                      project: ProjectAnnotateEntities, document, cat: CAT, icd_code=None,
                      opcs_code=None):
    text = document.text
    id = None

    all_occurrences_start_idxs = []
    idx = 0
    while idx != -1:
        idx = text.find(source_val, idx)
        if idx != -1:
            all_occurrences_start_idxs.append(idx)
            idx += len(source_val)

    start = all_occurrences_start_idxs[selection_occurrence_index]

    if start is not None and len(source_val) > 0 and len(cui) > 0:
        # Remove overlaps
        end = start + len(source_val)
        _remove_overlap(project, document, start, end)

        cnt = Entity.objects.filter(label=cui).count()
        if cnt == 0:
            # Create the entity
            entity = Entity()
            entity.label = cui
            entity.save()
        else:
            entity = Entity.objects.get(label=cui)

        ann_ent = AnnotatedEntity()
        ann_ent.user = user
        ann_ent.project = project
        ann_ent.document = document
        ann_ent.entity = entity
        ann_ent.value = source_val
        ann_ent.start_ind = start
        ann_ent.end_ind = end
        ann_ent.acc = 1
        ann_ent.validated = True
        ann_ent.manually_created = True
        ann_ent.correct = True

        if icd_code:
            ann_ent.icd_code = icd_code
        if opcs_code:
            ann_ent.opcs_code = opcs_code

        ann_ent.save()
        id = ann_ent.id

    # upload icd / opcs codes if available
    # also expects icd / opcs addl info dicts to include:
    # {code: <the code>: name: <human readable desc>}
    icd_codes = cat.cdb.addl_info.get('cui2icd10', {}).get(cui, None)
    if icd_codes is not None:
        create_linked_icd_codes(icd_codes, project.concept_db)
    opcs_codes = cat.cdb.addl_info.get('cui2opcs4', {}).get(cui, None)
    if opcs_codes is not None:
        create_linked_opcs_codes(opcs_codes, project.concept_db)

    return id


def train_medcat(cat, project, document):
    # Get all annotations
    anns = AnnotatedEntity.objects.filter(project=project, document=document, validated=True, killed=False)
    text = document.text
    spacy_doc = cat(text)

    if len(anns) > 0 and text is not None and len(text) > 5:
        for ann in anns:
            cui = ann.entity.label
            # Indices for this annotation
            spacy_entity = tkns_from_doc(spacy_doc=spacy_doc, start=ann.start_ind, end=ann.end_ind)
            # This will add the concept if it doesn't exist and if it 
            #does just link the new name to the concept, if the namee is
            #already linked then it will just train.
            manually_created = False
            if ann.manually_created or ann.alternative:
                manually_created = True

            cat.add_and_train_concept(cui=cui,
                          name=ann.value,
                          spacy_doc=spacy_doc,
                          spacy_entity=spacy_entity,
                          negative=ann.deleted,
                          devalue_others=manually_created)

            # Add entity to cui_counter
            pcc = ProjectCuiCounter.objects.filter(project=project, entity=ann.entity).first()
            if pcc is not None:
                pcc.count = pcc.count + 1
                pcc.save()
            else:
                pcc = ProjectCuiCounter()
                pcc.project = project
                pcc.entity = ann.entity
                pcc.count = 1
                pcc.save()

    # Completely remove concept names that the user killed
    killed_anns = AnnotatedEntity.objects.filter(project=project, document=document, killed=True)
    for ann in killed_anns:
        cui = ann.entity.label
        name = ann.value
        cat.unlink_concept_name(cui=cui, name=name)

    # Add irrelevant cuis to cui_exclude
    irrelevant_anns = AnnotatedEntity.objects.filter(project=project, document=document, irrelevant=True)
    for ann in irrelevant_anns:
        cui = ann.entity.label
        if 'cuis_exclude' not in cat.config.linking['filters']:
            cat.config.linking['filters']['cuis_exclude'] = set()
        cat.config.linking['filters'].get('cuis_exclude').update([cui])


def get_cached_medcat(CAT_MAP, project):
    if project.concept_db is None or project.vocab is None:
        return None
    cdb_id = project.concept_db.id
    vocab_id = project.vocab.id
    cat_id = str(cdb_id) + "-" + str(vocab_id)
    return CAT_MAP.get(cat_id)


def clear_cached_medcat(CAT_MAP, project):
    cdb_id = project.concept_db.id
    vocab_id = project.vocab.id
    cat_id = str(cdb_id) + "-" + str(vocab_id)
    if cat_id in CAT_MAP:
        del CAT_MAP[cat_id]


def get_medcat(CDB_MAP, VOCAB_MAP, CAT_MAP, project):
    try:
        cdb_id = project.concept_db.id
        vocab_id = project.vocab.id
    except AttributeError:
        raise Exception('Failure loading Project Concept Database or Vocabulary. Are these set correctly?')
    cat_id = str(cdb_id) + "-" + str(vocab_id)

    if cat_id in CAT_MAP:
        cat = CAT_MAP[cat_id]
    else:
        if cdb_id in CDB_MAP:
            cdb = CDB_MAP[cdb_id]
        else:
            cdb_path = project.concept_db.cdb_file.path
            try:
                cdb = CDB.load(cdb_path)
            except KeyError as ke:
                mc_v = pkg_resources.get_distribution('medcat').version
                if int(mc_v.split('.')[0]) > 0:
                    log.error('Attempted to load MedCAT v0.x model with MCTrainer v1.x')
                    raise Exception('Attempted to load MedCAT v0.x model with MCTrainer v1.x',
                                    'Please re-configure this project to use a MedCAT v1.x CDB or consult the '
                                    'MedCATTrainer Dev team if you believe this should work') from ke
                raise

            custom_config = os.getenv("MEDCAT_CONFIG_FILE")
            if custom_config is not None and os.path.exists(custom_config):
                cdb.config.parse_config_file(path=custom_config)
            else:
                log.info("No MEDCAT_CONFIG_FILE env var set to valid path, using default config available on CDB")
            CDB_MAP[cdb_id] = cdb

        if vocab_id in VOCAB_MAP:
            vocab = VOCAB_MAP[vocab_id]
        else:
            vocab_path = project.vocab.vocab_file.path
            vocab = Vocab.load(vocab_path)
            VOCAB_MAP[vocab_id] = vocab

        cat = CAT(cdb=cdb, config=cdb.config, vocab=vocab)
        CAT_MAP[cat_id] = cat
    return cat


@receiver(post_save, sender=ProjectAnnotateEntities)
def save_project_anno(sender, instance, **kwargs):
    if instance.cuis_file:
        post_save.disconnect(save_project_anno, sender=ProjectAnnotateEntities)
        cuis_from_file = json.load(open(instance.cuis_file.path))
        cui_list = [c.strip() for c in instance.cuis.split(',')]
        instance.cuis = ','.join(set(cui_list) - set(cuis_from_file))
        instance.save()
        post_save.connect(save_project_anno, sender=ProjectAnnotateEntities)


def env_str_to_bool(var: str, default: bool):
    val = os.environ.get(var, default)
    if isinstance(val, str):
        if val.lower() in ('1', 'true', 't', 'y'):
            return True
        elif val.lower() in ('0', 'false', 'f', 'n'):
            return False
    return val
