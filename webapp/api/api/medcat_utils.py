from collections import defaultdict
from typing import List

from medcat.cdb import CDB


def ch2pt_from_pt2ch(cdb: CDB):
    ch2pt = defaultdict(list)
    for k, vals in cdb.addl_info['pt2ch'].items():
        for v in vals:
            ch2pt[v].append(k)
    return ch2pt


def get_all_ch(parent_cui: str, cdb: CDB):
    all_ch = [parent_cui]
    for cui in cdb.addl_info['pt2ch'].get(parent_cui, []):
        cui_chs = get_all_ch(cui, cdb)
        all_ch += cui_chs
    return dedupe_preserve_order(all_ch)


def dedupe_preserve_order(items: List[str]) -> List[str]:
    seen = set()
    deduped_list = []
    for item in items:
        if item not in seen:
            seen.add(item)
            deduped_list.append(item)
    return deduped_list
