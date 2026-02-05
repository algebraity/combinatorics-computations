import os
import csv
import time
import random as rand
import multiprocessing as mp
from typing import Any, List, Tuple, Union

HEADER = [
    "n", "|A|", "|A+A|"
]

def A_ads_size(n: int) -> tuple[int, int]:
    """
    A_n = { i*2^j : 1<=i<=n, 1<=j<=n }.

    Returns (|A_n|, |A_n + A_n|) exactly using a dyadic (odd-part/exponent) method:
      - represent sums as u*2^t with u odd
      - store achievable exponents t per odd u as a bitmask

    Complexity is about O((#odds)^2 * n) = O(n^3) / 4, which is usually far faster
    than enumerating all |A|^2 sums in Python for moderate n.
    """

    odds = list(range(1, n + 1, 2))
    # L[m] = floor(log2(n//m))  (max r such that m*2^r <= n)
    L = {}
    Emax = {}  # Emax[m] = max exponent e for elements m*2^e that appear in A_n
    for m in odds:
        q = n // m
        lm = q.bit_length() - 1  # since q>=1
        L[m] = lm
        Emax[m] = n + lm

    # |A| = sum over odd m of number of exponents e in [1..Emax[m]]
    A_size = sum(Emax[m] for m in odds)

    # helper: v2(x) for positive int x (number of trailing zeros in base-2)
    def v2(x: int) -> int:
        return (x & -x).bit_length() - 1

    # map odd u -> bitmask of achievable exponents t
    # bit t is 1 <=> u*2^t is in A+A
    u_to_mask: dict[int, int] = {}

    # maximum d we ever need to consider (if Emax[m2]-d >= 1)
    # crude safe bound:
    d_max = max(Emax.values()) - 1

    for a in odds:
        Ea = Emax[a]
        La = L[a]
        for b in odds:
            Eb = Emax[b]
            Lb = L[b]

            # For each d>=0: need e1 in [1..Ea] and e2=e1+d in [1..Eb]
            # so e1 <= Eb - d
            # Let E1max(d) = min(Ea, Eb - d). If <1, skip.
            # Also K = a + (b<<d) changes with d.

            # We can stop once Eb - d < 1
            # i.e. d > Eb-1
            max_d_here = Eb - 1
            if max_d_here < 0:
                continue
            # Iterate d from 0..max_d_here
            # (This is the main cost; still typically much cheaper than |A|^2.)
            for d in range(0, max_d_here + 1):
                E1max = Ea
                limit = Eb - d
                if limit < E1max:
                    E1max = limit
                if E1max < 1:
                    break

                K = a + (b << d)
                tz = v2(K)
                u = K >> tz  # odd part

                # t runs from (1 + tz) up to (E1max + tz), inclusive
                t_lo = 1 + tz
                t_hi = E1max + tz

                # set bits t_lo..t_hi in the mask
                interval_mask = ((1 << (t_hi + 1)) - 1) ^ ((1 << t_lo) - 1)

                prev = u_to_mask.get(u, 0)
                u_to_mask[u] = prev | interval_mask

    # popcount of Python int
    AA_size = sum(mask.bit_count() for mask in u_to_mask.values())
    return A_size, AA_size


def _worker(ns: list[int]) -> list[list[int]]:
    out = []
    for i in ns:
        A_size, AA_size = A_ads_size(i)
        out.append([i, A_size, AA_size])
    return out


def compute_ads(n: int, out_dir: str = "data", k: int = 40, jobs: int | None = None, mp_context: str | None = "fork"):
    os.makedirs(out_dir, exist_ok=True)
    jobs = jobs or os.cpu_count() or 1

    t0 = time.time()

    ctx = mp.get_context(mp_context) if mp_context else mp.get_context()

    chunks = [list(range(i * n // k + 1, (i + 1) * n // k + 1)) for i in range(k)]

    all_rows: list[list[int]] = []

    with ctx.Pool(processes=jobs) as pool:
        done = 0
        for chunk_rows in pool.imap_unordered(_worker, chunks, chunksize=1):
            all_rows.extend(chunk_rows)
            done += 1
            print(f"{(100*done)//k}% done, {time.time()-t0:.1f}s since start")

    all_rows.sort(key=lambda r: r[0])  # sort by n

    out_path = os.path.join(out_dir, f"ads_sizes_{n}.csv")
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(HEADER)
        w.writerows(all_rows)

    return out_path