import logging
import os
from typing import Dict

import pkg_resources
from medcat.cat import CAT
from medcat.cdb import CDB
from medcat.vocab import Vocab

from api.models import ConceptDB

"""
Module level caches for CDBs, Vocabs and CAT instances.
"""
# Maps between IDs and objects
CDB_MAP = {}
VOCAB_MAP = {}
CAT_MAP = {}

_MAX_MODELS_LOADED = os.getenv("MAX_MEDCAT_MODELS", 1)

logger = logging.getLogger(__name__)


def _clear_models(cdb_map: Dict[str, CDB]=CDB_MAP,
                  vocab_map: Dict[str, Vocab]=VOCAB_MAP,
                  cat_map: Dict[str, CAT]=CAT_MAP):
    if len(cat_map) > _MAX_MODELS_LOADED:
        (k := next(iter(cat_map)), cat_map.pop(k))
    if len(cdb_map) > _MAX_MODELS_LOADED:
        (k := next(iter(cdb_map)), cdb_map.pop(k))
    if len(vocab_map) > _MAX_MODELS_LOADED:
        (k := next(iter(vocab_map)), vocab_map.pop(k))


def get_medcat_from_cdb_vocab(project,
                              cdb_map: Dict[str, CDB]=CDB_MAP,
                              vocab_map: Dict[str, Vocab]=VOCAB_MAP,
                              cat_map: Dict[str, CAT]=CAT_MAP) -> CAT:
    cdb_id = project.concept_db.id
    vocab_id = project.vocab.id
    cat_id = str(cdb_id) + "-" + str(vocab_id)
    if cat_id in cat_map:
        cat = cat_map[cat_id]
    else:
        if cdb_id in cdb_map:
            cdb = cdb_map[cdb_id]
        else:
            cdb_path = project.concept_db.cdb_file.path
            try:
                cdb = CDB.load(cdb_path)
            except KeyError as ke:
                mc_v = pkg_resources.get_distribution('medcat').version
                if int(mc_v.split('.')[0]) > 0:
                    logger.error('Attempted to load MedCAT v0.x model with MCTrainer v1.x')
                    raise Exception('Attempted to load MedCAT v0.x model with MCTrainer v1.x',
                                    'Please re-configure this project to use a MedCAT v1.x CDB or consult the '
                                    'MedCATTrainer Dev team if you believe this should work') from ke
                raise

            custom_config = os.getenv("MEDCAT_CONFIG_FILE")
            if custom_config is not None and os.path.exists(custom_config):
                cdb.config.parse_config_file(path=custom_config)
            else:
                logger.info("No MEDCAT_CONFIG_FILE env var set to valid path, using default config available on CDB")
            cdb_map[cdb_id] = cdb

        if vocab_id in vocab_map:
            vocab = vocab_map[vocab_id]
        else:
            vocab_path = project.vocab.vocab_file.path
            vocab = Vocab.load(vocab_path)
            vocab_map[vocab_id] = vocab
        cat = CAT(cdb=cdb, config=cdb.config, vocab=vocab)
        cat_map[cat_id] = cat
        _clear_models(cat_map=cat_map, cdb_map=cdb_map, vocab_map=vocab_map)
    return cat


def get_medcat_from_model_pack(project, cat_map: Dict[str, CAT]=CAT_MAP) -> CAT:
    model_pack_obj = project.model_pack
    cat_id = 'mp' + str(model_pack_obj.id)
    logger.info('Loading model pack from:%s', model_pack_obj.model_pack.path)
    cat = CAT.load_model_pack(model_pack_obj.model_pack.path)
    cat_map[cat_id] = cat
    _clear_models(cat_map=cat_map)
    return cat


def get_medcat(project,
               cdb_map: Dict[str, CDB]=CDB_MAP,
               vocab_map: Dict[str, Vocab]=VOCAB_MAP,
               cat_map: Dict[str, CAT]=CAT_MAP):
    try:
        if project.model_pack is None:
            cat = get_medcat_from_cdb_vocab(project, cdb_map, vocab_map, cat_map)
        else:
            cat = get_medcat_from_model_pack(project, cat_map)
        return cat
    except AttributeError:
        raise Exception('Failure loading Project ConceptDB, Vocab or Model Pack. Are these set correctly?')


def get_cached_medcat(project, cat_map: Dict[str, CAT]=CAT_MAP):
    if project.model_pack is not None:
        cat_id = 'mp' + str(project.model_pack.id)
    else:
        cdb_id = project.concept_db.id
        vocab_id = project.vocab.id
        cat_id = str(cdb_id) + "-" + str(vocab_id)
    return cat_map.get(cat_id)


def clear_cached_medcat(project, cat_map: Dict[str, CAT]=CAT_MAP):
    if project.model_pack is not None:
        model_pack_obj = project.model_pack
        cat_id = 'mp' + str(model_pack_obj.id)
    else:
        cdb_id = project.concept_db.id
        vocab_id = project.vocab.id
        clear_cached_cdb(cdb_id)
        clear_cached_vocab(vocab_id)
        cat_id = str(cdb_id) + "-" + str(vocab_id)
    if cat_id in cat_map:
        del cat_map[cat_id]


def get_cached_cdb(cdb_id: str, cdb_map: Dict[str, CDB]=CDB_MAP) -> CDB:
    if cdb_id not in cdb_map:
        cdb_obj = ConceptDB.objects.get(id=cdb_id)
        cdb = CDB.load(cdb_obj.cdb_file.path)
        cdb_map[cdb_id] = cdb
    return cdb_map[cdb_id]


def clear_cached_cdb(cdb_id, cdb_map: Dict[str, CDB]=CDB_MAP):
    if cdb_id in cdb_map:
        del cdb_map[cdb_id]


def clear_cached_vocab(vocab_id, vocab_map: Dict[str, Vocab]=VOCAB_MAP):
    if vocab_id in vocab_map:
        del vocab_map[vocab_id]


def is_model_loaded(project,
                    cdb_map: Dict[str, CDB]=CDB_MAP,
                    cat_map: Dict[str, CAT]=CAT_MAP):
    if project.concept_db is None:
        # model pack is used.
        return False if not project.model_pack else f'mp{project.model_pack.id}' in cat_map
    else:
        return False if not project.concept_db else project.concept_db.id in cdb_map
