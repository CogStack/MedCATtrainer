from collections import defaultdict

from medcat.cdb import CDB


def ch2pt_from_pt2ch(cdb: CDB):
    ch2pt = defaultdict(list)
    for k, vals in cdb.addl_info['pt2ch'].items():
        for v in vals:
            ch2pt[v].append(k)
    return ch2pt
