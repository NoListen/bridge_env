from deal import Deal
import time
start = time.time()

# Strain 0: "C", 1: "D", 2: "H", 3: "S", 4: "N"
# Suit 0: "S", 1: "H", 2: "D", 3: "C"
predeal = {0: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]}
deal1 = Deal.prepare(predeal)
Deal.score(dealer=deal1, level=5, strain=0, declarer=3, tries=100)

print("%.2f seconds elapsed" % (time.time()-start))