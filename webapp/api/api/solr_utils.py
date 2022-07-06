import json
import logging
import re
from typing import List

import requests
from background_task import background
from django.http import HttpResponseServerError
from medcat.cdb import CDB
from rest_framework.response import Response

from api.models import ConceptDB
from core.settings import SOLR_HOST, SOLR_PORT

SOLR_INDEX_SCHEMA = {}

logger = logging.getLogger(__name__)


def _cache_solr_collection_schema_types(collection):
    url = f'http://{SOLR_HOST}:{SOLR_PORT}/solr/{collection}/schema'
    logger.info(f'Retrieving solr schema: {url}')
    resp = json.loads(requests.get(url).text)
    cui_type = [n for n in resp['schema']['fields'] if n['name'] == 'cui'][0]['type']
    # just store cui type for the time being
    SOLR_INDEX_SCHEMA[collection] = {'cui': cui_type}


def collections_available(cdbs: List[int]):
    url = f'http://{SOLR_HOST}:{SOLR_PORT}/solr/admin/collections?action=LIST'
    resp = requests.get(url)
    if resp.status_code == 200:
        collections = json.loads(resp.text)['collections']
        # cache schema field types
        for col in collections:
            _cache_solr_collection_schema_types(col)
        current_collections_cdb_ids = [c.split('_id_')[-1] for c in collections]
        return Response({'results': {cdb_id: cdb_id in current_collections_cdb_ids for cdb_id in cdbs}})
    else:
        return HttpResponseServerError('Error requesting solr concept search collection list')


def search_collection(cdbs: List[int], query: str):
    query = query.strip().replace(r'\s+', r'\s').split(' ')
    if len(query) == 1 and query[0] == '':
        return Response({'results': []})
    query = [f'{query[i]}~1' if i < len(query) - 1 else f'{query[i]}*' for i in range(len(query))]

    res = []
    if len(cdbs) > 0:
        uniq_results_map = {}
        for cdb in cdbs:
            cdb_model = ConceptDB.objects.get(id=cdb)
            collection_name = f'{cdb_model.name}_id_{cdb_model.id}'
            if collection_name not in SOLR_INDEX_SCHEMA:
                _cache_solr_collection_schema_types(collection_name)
            try:
                query_num = int(query[0][:-1])
                query_str = f'cui:{query_num}'
            except ValueError:
                if len(query) > 1:  # cannot be a cui if multi-word
                    query_str = ''.join([f' name:{q}' for q in query])
                elif SOLR_INDEX_SCHEMA[collection_name]['cui'] != 'plongs':  # single word could be alphanumeric cui
                    query_str = f'cui:{query[0][:-1]} OR name:{query[0][:-1]} OR name:{query[0]}'
                else:  # single word, numeric cui.
                    query_str = f'name:{query[0][:-1]} OR name:{query[0]}'

            solr_url = f'http://{SOLR_HOST}:{SOLR_PORT}/solr/{collection_name}/select?q.op=OR&q={query_str}&rows=15'
            logger.info(f'Searching solr collection: {solr_url}')
            resp = json.loads(requests.get(solr_url).text)
            if 'error' in resp:
                return HttpResponseServerError(f'Concept Search Index {collection_name} not available, '
                                               f'import concept DB first before trying to search it.')
            else:
                docs = [d for d in resp['response']['docs']]
                for d in docs:
                    if d['cui'][0] not in uniq_results_map:
                        parsed_doc = {'cui': str(d['cui'][0]), 'pretty_name': d['pretty_name'][0]}
                        if d.get('icd10'):
                            parsed_doc['icd10'] = d['icd10'][0]
                        if d.get('opcs4'):
                            parsed_doc['opcs4'] = d['opcs4'][0]
                        uniq_results_map[d['cui'][0]] = parsed_doc
        res = sorted(uniq_results_map.values(), key=lambda r: len(r['pretty_name']))
    return Response({'results': res})


def import_concepts_to_solr(cdb: CDB, cdb_model: ConceptDB):
    collection_name = f'{cdb_model.name}_id_{cdb_model.id}'
    base_url = f'http://{SOLR_HOST}:{SOLR_PORT}/solr'

    # check if solr collections already exists.
    url = f'{base_url}/admin/collections?action=LIST'
    resp = requests.get(url)
    if resp.status_code != 200:
        logger.error("Error connecting to Solr to retrieve current collection list")
        raise Exception("Error connecting to Solr to retrieve current collection list")

    collections = json.loads(resp.text)['collections']
    if collection_name in collections:
        # delete collection
        url = f'{base_url}/admin/collections?action=DELETE&name={collection_name}'
        requests.get(url)

    # create solr collections.
    url = f'{base_url}/admin/collections?action=CREATE&name={collection_name}&numShards=1'
    resp = requests.get(url)
    if resp.status_code != 200:
        _solr_error_response(resp, 'Failure creating collection')

    cui2name_iter = iter(cdb.cui2names.items())

    def _upload_payload(data, cn, commit=False):
        update_url = f'{base_url}/{collection_name}/update'
        update_url = f'{update_url}?commit=true' if commit else update_url
        logger.info(f'Uploading {len(data)} to solr collection {cn}')
        resp = requests.post(update_url, json=data)
        if resp.status_code == 200:
            logger.info(f'Successfully uploaded {len(data)} concepts to solr collection {cn}')
        elif resp.status_code != 200:
            _solr_error_response(resp, f'error updating {cn}')

    payload = []
    try:
        while True:
            for i in range(5000):
                cui, name = next(cui2name_iter)
                concept_dct = {
                    'cui': str(cui),
                    'pretty_name': cdb.get_name(cui),
                    'name': re.sub(r'\([\w+\s]+\)', '', cdb.get_name(cui)).strip(),
                }
                # upload icd / opcs codes if available
                # also expects icd / opcs addl info dicts to include:
                # {code: <the code>: name: <human readabled desc>}
                icd_codes = cdb.addl_info.get('cui2icd10', {}).get(cui, None)
                if icd_codes is not None:
                    concept_dct['icd10'] = ', '.join([f'{code["code"]} : {code["name"]}'
                                                      for code in icd_codes])
                opcs_codes = cdb.addl_info.get('cui2opcs4', {}).get(cui, None)
                if opcs_codes is not None:
                    concept_dct['opcs4'] = ', '.join([f'{code["code"]} : {code["name"]}'
                                                      for code in opcs_codes])
                payload.append(concept_dct)
            _upload_payload(payload, collection_name)
            payload = []
    except StopIteration:
        # upload last update
        _upload_payload(payload, collection_name, commit=True)

    # get final collection size
    logger.info(f'Successfully uploaded {cdb_model.name} cuis / names to solr collection {collection_name}')

    resp = requests.get(f'{base_url}/{collection_name}/select?q=*:*&rows=0')
    logger.info(f'{json.loads(resp.text)["response"]["numFound"]} Concepts now searchable')


def _solr_error_response(resp, error_msg):
    try:
        error = json.loads(resp.text)['error']
    except Exception as e:
        logger.error(f'{error_msg}: unknown error')
        raise e
    error_msg = f'{error_msg}: solr error: {error}'
    logger.error(error_msg)
    raise Exception(error_msg)
