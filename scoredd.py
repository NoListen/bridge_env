from json import load, dump
from multiprocessing import Pool
from argparse import ArgumentParser
from numpy import zeros, round
from config import ScoreBias, ScoreScale
import time

def convert2IMP(diff):
	imp = 0
	if diff >= 20 and diff < 50:
		imp = 1
	elif diff >= 50 and diff < 90:
		imp = 2
	elif diff >= 90 and diff < 130:
		imp = 3
	elif diff >= 130 and diff < 170:
		imp = 4
	elif diff >= 170 and diff < 220:
		imp = 5
	elif diff >= 220 and diff < 270:
		imp = 6
	elif diff >= 270 and diff < 320:
		imp = 7
	elif diff >= 320 and diff < 370:
		imp = 8
	elif diff >= 370 and diff < 430:
		imp = 9
	elif diff >= 430 and diff < 500:
		imp = 10
	elif diff >= 500 and diff < 600:
		imp = 11
	elif diff >= 600 and diff < 750:
		imp = 12
	elif diff >= 750 and diff < 900:
		imp = 13
	elif diff >= 900 and diff < 1100:
		imp = 14
	elif diff >= 1100 and diff < 1300:
		imp = 15
	elif diff >= 1300 and diff < 1500:
		imp = 16
	elif diff >= 1500 and diff < 1750:
		imp = 17
	elif diff >= 1750 and diff < 2000:
		imp = 18
	elif diff >= 2000 and diff < 2250:
		imp = 19
	elif diff >= 2250 and diff < 2500:
		imp = 20
	elif diff >= 2500 and diff < 3000:
		imp = 21
	elif diff >= 3000 and diff < 3500:
		imp = 22
	elif diff >= 3500 and diff < 4000:
		imp = 23
	elif diff >= 4000:
		imp = 24
	return imp

def score(input_tuple):
	# bid_tricks range from 1 - 7
	# max_tricks range from 0 - 13
	bid_tricks, trump, max_tricks = input_tuple
	declarer_score = 0
	defender_score = 0

	# Major suit trump.
	# Suit2str = {0: "S", 1: "H", 2: "D", 3: "C"}
	# Did the declarer make at least 6 tricks?
	if max_tricks > 6:
		contract_tricks = min(max_tricks-6, bid_tricks)
		declarer_score += (ScoreScale[trump] * contract_tricks + ScoreBias[trump])

	# Were there overtricks?
	if max_tricks > (bid_tricks+6):
		over_tricks = max_tricks - bid_tricks - 6
		declarer_score += ScoreScale[trump] * over_tricks

	# Were there penalty points?
	if max_tricks < (bid_tricks+6):
		under_tricks = bid_tricks + 6 - max_tricks
		defender_score += 50 * under_tricks

	# Was there a slam?
	if max_tricks == 12:
		declarer_score += 500
	elif max_tricks == 13:
		declarer_score += 1000

	# Converting to IMP
	diff = abs(declarer_score - defender_score)
	imp = convert2IMP(diff)

	if declarer_score > defender_score:
		return imp
	else:
		return (-1) * imp 


# calculate the table
def precompute_scores():
	input_space = [(bid_tricks, trump, max_tricks)  for bid_tricks in range(1,8)
				   									for trump in range(5)
				   									for max_tricks in range(14)]

	score_space = [score(t) for t in input_space]
	scorer = dict(zip(input_space, score_space))
	del input_space, score_space
	return scorer

start  = time.time()
print("Calculating IMP_TABLE")
IMP_TABLE = precompute_scores()
print("IMP_TABLE CALCULATION COMPLETED")
