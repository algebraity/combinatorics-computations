# This is just an example used to validate `ads_size` with explicit examples.
# Not used for data generation.
for n in range(1, 201):
    s = set([i * (2**j) for i in range(1, n+1) for j in range(1, n+1)])
    ads = set([x + y for x in s for y in s])
    print(f"{n}, {len(s)}, {len(ads)}")
