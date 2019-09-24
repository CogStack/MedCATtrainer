from .models import Entity, AnnotatedEntity, Concept
from medcat.cdb import CDB
from medcat.utils.vocab import Vocab
from medcat.cat import CAT

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
    print(spacy_doc)
    print(spacy_doc.ents)
    print(spacy_doc._.ents)
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
                ann_ent.correct = True
                ann_ent.save()


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

    return cat
