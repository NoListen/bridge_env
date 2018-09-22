import numpy as np

Seat = list(range(4))
Suit = list(range(4))
Strain = list(range(5))
Rank = list(range(2, 15))
FULL_DECK = list(range(52))

Seat2Group = {0: 0, 1: 1, 2: 0, 3: 1} # or s%2

Seat2str = {0: "N", 1: "E", 2: "S", 3: "W"}
Strain2str = {0: "S", 1: "H", 2: "D", 3: "C", 4: "N"}
Suit2str = {0: "S", 1: "H", 2: "D", 3: "C"}
Rank2str = {2: '2', 3: '3', 4: '4', 5: '5', 6: '6', 7: '7', 8: '8', 9: '9', 10: 'T', 11: 'J', 12: 'Q', 13: 'K', 14: 'A'}

# Convenient for parallel processing
# ScoreScale = {0: 30, 1: 30, 2: 20, 3: 20, 4: 30}
ScoreScale = np.array([30, 30, 20, 20, 30])
# ScoreBias = {0: 0, 1: 0, 2: 0, 3: 0, 4: 10}
ScoreBias = np.array([0, 0, 0, 0, 10])

MAXNOOFBOARDS = 200