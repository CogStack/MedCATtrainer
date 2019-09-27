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
    for ent in spacy_doc.ents:
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

        if (not tuis or tui in tuis) and (not cuis or label in cuis):
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

def create_annotation(source_val, right_context, cui, user, project, document):
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
        ann_ent.save()
        id = ann_ent.id

    return id


def train_medcat(cat, project, document):
    # Get all annotations
    anns = AnnotatedEntity.objects.filter(project=project, document=document, validated=True)
    text = document.text
    doc = cat(text)

    if len(anns) > 0 and text is not None and len(text) > 5:
        for ann in anns:
            name, _ = prepare_name(cat=cat, name=ann.value, version='clean')
            cui = ann.entity.label

            # Does the concept exist
            if cui in cat.cdb.cui2names:
                text_inds = [ann.start_ind, ann.end_ind]
                tkn_inds = tkn_inds_from_doc(spacy_doc=doc,
                                             text_inds=text_inds,
                                             source_val=name)

                if name not in cat.cdb.name2cui or cui not in cat.cdb.name2cui[name]:
                    # If the name is not linked add the link 
                    cat.add_name(cui=cui,
                                 source_val=ann.value,
                                 spacy_doc=doc,
                                 tkn_inds=tkn_inds,
                                 lr=0.3)
                else:
                    print("HERE")
                    print(doc)
                    print(tkn_inds)
                    print(cui, tkn_inds, doc[tkn_inds[0]:tkn_inds[-1]])
                    print("SDF")
                    # Name is linked, just add training
                    cat.add_concept_cntx(cui, text, tkn_inds, spacy_doc=doc,
                                         lr=0.2, anneal=False, negative=ann.deleted)


def get_medcat(cat, CDB_MAP, VOCAB_MAP, project):
    cdb_id = project.medcat_models.cdb.id
    vocab_id = project.medcat_models.vocab.id

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

    if cat is None:
        cat = CAT(cdb=cdb, vocab=vocab)
    else:
        cat.cdb = cdb
        cat.vocab = vocab
    cat.train = False

    return cat
