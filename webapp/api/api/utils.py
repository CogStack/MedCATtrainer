import os
from .models import Entity, AnnotatedEntity, Concept
from medcat.cdb import CDB
from medcat.utils.vocab import Vocab
from medcat.cat import CAT
from medcat.utils.helpers import tkn_inds_from_doc, prepare_name
from medcat.utils.loggers import basic_logger
log = basic_logger("api.utils")

def remove_annotations(document, project, partial=False):
    try:
        if partial:
            # Remvoves only the ones that are not validated
            AnnotatedEntity.objects.filter(project=project,
                                           document=document,
                                           validated=False).delete()
        else:
            # Removes everything
            AnnotatedEntity.objects.filter(project=project, document=document).delete()
        return "Annotations removed"
    except Exception as e:
        return "Something went wrong: " + str(e)

def add_annotations(spacy_doc, user, project, document, cdb, tuis=[], cuis=[]):
    spacy_doc._.ents.sort(key=lambda x: len(x.text), reverse=True)

    tkns_in = []
    ents = []
    for ent in spacy_doc._.ents:
        if (not cuis and not tuis) or (ent._.tui in tuis) or (ent._.cui in cuis):
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
        tui = ent._.tui

        # Add the concept info to the Concept table if it doesn't exist
        cnt = Concept.objects.filter(cui=label).count()
        if cnt == 0:
            concept = Concept()
            concept.pretty_name = cdb.cui2pretty_name.get(label, '')
            concept.cui = label
            concept.tui = tui
            concept.semantic_type = cdb.tui2name.get(tui, '')
            concept.desc = cdb.cui2desc.get(label, '')
            concept.synonyms = ",".join(cdb.cui2original_names.get(label, []))
            concept.cdb = project.medcat_models.cdb
            #concept.vocab = cdb.cui2ontos.get(label, '')
            icd10 = ''
            try:
                for pair in cdb.cui2info[label]['icd10']:
                    icd10 += pair['chapter'] + " | " + pair['name']
                    icd10 += '\n'
                icd10.strip()
            except:
                pass
            concept.icd10 = icd10
            concept.save()

        cnt = Entity.objects.filter(label=label).count()
        if cnt == 0:
            # Create the entity
            entity = Entity()
            entity.label = label
            entity.save()
        else:
            entity = Entity.objects.get(label=label)

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
            ann_ent.acc = ent._.acc
            ann_ent.save()


def _remove_overlap(project, document, start, end):
    anns = AnnotatedEntity.objects.filter(project=project, document=document)

    for ann in anns:
        if ann.start_ind >= start and ann.start_ind <= end:
            log.debug("Removed")
            log.debug(str(ann))
            ann.delete()
        elif ann.end_ind >= start and ann.end_ind <= end:
            ann.delete()
            log.debug("Removed")
            log.debug(str(ann))

def create_annotation(source_val, right_context, cui, user, project, document, cat):
    text = document.text
    id = None

    start = None
    end = None
    if right_context in text:
        start = text.index(right_context)
    elif source_val in text:
        start = text.index(source_val)

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
        ann_ent.save()
        id = ann_ent.id

        # Add this annotation to CUIs for this project
        #if it is not already included
        if project.cuis or project.tuis:
            if cui not in project.cuis:
                tui = cat.cdb.cui2tui.get(cui, 'unk')
                if tui not in project.tuis:
                    project.cuis = project.cuis + "," + str(cui)
                    project.save()

    return id


def train_medcat(cat, project, document):
    lr = float(os.getenv("LR", 1))
    anneal = os.getenv("ANNEAL", 'false').lower() == 'true'

    # Just in case, disable unsupervised training
    cat.train = False
    # Get all annotations
    anns = AnnotatedEntity.objects.filter(project=project, document=document, validated=True)
    text = document.text
    doc = cat(text)

    if len(anns) > 0 and text is not None and len(text) > 5:
        for ann in anns:
            cui = ann.entity.label
            # Indices for this annotation
            text_inds = [ann.start_ind, ann.end_ind]
            # This will add the concept if it doesn't exist and if it 
            #does just link the new name to the concept, if the namee is
            #already linked then it will just train.
            cat.add_name(cui=cui,
                         source_val=ann.value,
                         text=text,
                         spacy_doc=doc,
                         text_inds=text_inds,
                         lr=lr,
                         anneal=anneal,
                         negative=ann.deleted)


def get_medcat(CDB_MAP, VOCAB_MAP, CAT_MAP, project):
    cdb_id = project.medcat_models.cdb.id
    vocab_id = project.medcat_models.vocab.id
    cat_id = str(cdb_id) + "-" + str(vocab_id)

    if cat_id in CAT_MAP:
        cat = CAT_MAP[cat_id]
    else:
        if cdb_id in CDB_MAP:
            cdb = CDB_MAP[cdb_id]
        else:
            cdb_path = project.medcat_models.cdb.cdb_file.path
            cdb = CDB()
            cdb.load_dict(cdb_path)
            CDB_MAP[cdb_id] = cdb

        if vocab_id in VOCAB_MAP:
            vocab = VOCAB_MAP[vocab_id]
        else:
            vocab_path = project.medcat_models.vocab.vocab_file.path
            vocab = Vocab()
            vocab.load_dict(vocab_path)
            VOCAB_MAP[vocab_id] = vocab

        cat = CAT(cdb=cdb, vocab=vocab)
        cat.train = False
        CAT_MAP[cat_id] = cat
    return cat
