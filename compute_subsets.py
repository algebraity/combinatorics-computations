from itertools import chain, combinations
from ookami import *
import json
import time
import os
import multiprocessing as mp
import numpy as np
from fractions import Fraction

os.makedirs("data", exist_ok=True)

JOBS = mp.cpu_count()
N = 20
k = 10*JOBS

HEADER = ["set", "add_ds", "diff_ds", "mult_ds", "cardinality", "diameter", "density", "dc",
          "is_ap", "is_gp", "add_energy", "mult_energy"
]

def mask_to_subset(mask, n):
    out = []
    i = 1
    while mask:
        if mask & 1:
            out.append(i)
        mask >>= 1
        i+=1
    return tuple(out)

def compute_row(subset: tuple[int, ...]):
    S = CombSet(subset)
    info = S.info()
    return [
        str(S),
        json.dumps(info["add_ds"]._set),
        json.dumps(info["diff_ds"]._set),
        json.dumps(info["mult_ds"]._set),
        info["cardinality"],
        info["diameter"],
        info["density"],
        str(info["dc"]),
        info["is_ap"],
        info["is_gp"],
        info["add_energy"],
        info["mult_energy"],
    ]

def _worker(chunk_id: int):
    total = 1 << N
    rows = [HEADER]

    start = chunk_id if chunk_id != 0 else k
    for mask in range(start, total, k):
        subset = mask_to_subset(mask, N)
        rows.append(compute_row(subset))

    filename = f"set_info_{N}_{chunk_id:04d}.csv"
    path = os.path.join("data", filename)
    np.savetxt(path, rows, delimiter=",", fmt="%s")
    return path

def main():
    start = time.time()

    try:
        ctx = mp.get_context("fork")
    except ValueError:
        ctx = mp.get_context()

    with ctx.Pool(processes=JOBS) as pool:
        for path in pool.imap_unordered(_worker, range(k), chunksize=1):
            print("wrote " + str(path) + ", " + str(time.time() - start) + " seconds since start")

if __name__ == "__main__":
    main()
