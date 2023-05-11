from collections import defaultdict

from medcat.cdb import CDB


def ch2pt_from_pt2ch(cdb: CDB):
    ch2pt = defaultdict(list)
    for k, vals in cdb.addl_info['pt2ch'].items():
        for v in vals:
            ch2pt[v].append(k)
    cdb.addl_info['ch2pt'] = ch2pt
    return ch2pt