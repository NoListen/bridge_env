from dds import solve, solve_all
from collections import defaultdict
from copy import deepcopy
from bridge_utils import convert_hands2string, convert_level_strain2action
from config import *
import random
from scoredd import IMP_TABLE

# def convert_id2seat(seat_id):
#     return Seat[seat_id]


class Deal(object):

    @classmethod
    def prepare(cls, predeal=None):
        predeal = {} if predeal is None else predeal.copy()
        dealer = defaultdict(list)

        for seat in Seat:
            try:
                pre = predeal.pop(seat)
            except KeyError:
                continue

            if isinstance(pre, list):
                dealer[seat] = pre
            else:
                raise Exception("Wrong format of predeal")

        if predeal:
            raise Exception("Unused predeal entries: {}".format(predeal))

        predealt = [card for hand_cards in dealer.values()
                    for card in hand_cards]
        predealt_set = set(predealt)
        if len(predealt_set) < len(predealt):
            raise Exception("Same card dealt twice.")
        dealer["_remaining"] = [card for card in FULL_DECK
                                if card not in predealt_set]
        return dealer  # a dictionary

    # single thread
    @classmethod
    def score_st(cls, dealer, level, strain, declarer, tries, mode=None):
        max_tricks = []
        # target = level + 6

        for _ in range(tries):
            tmp_dealer = deepcopy(dealer)
            cards = dealer["_remaining"]
            random.shuffle(cards)
            for seat in Seat:
                to_deal = len(Rank) - len(tmp_dealer[seat])
                tmp_dealer[seat] += cards[:to_deal]
                cards = cards[to_deal:]
            max_tricks.append(solve(tmp_dealer, strain, declarer))
            # score = max_trick - target
        if mode == "IMP":
            scores = [IMP_TABLE[(level, strain, trick)] for trick in max_tricks]
            print("IMP mode....")
        else:
            target = level + 6
            scores = [t - target for t in max_tricks]
        return np.mean(scores)

    @classmethod
    def score_all_st(cls, dealer, declarer, tries, mode=None):
        scores_for_all_strains = np.zeros((35, tries))
        idx_table = [[convert_level_strain2action(l, s) for l in range(1, 8)] for s in Strain]

        for t in range(tries):
            tmp_dealer = deepcopy(dealer)
            cards = dealer["_remaining"]
            random.shuffle(cards)
            for seat in Seat:
                to_deal = len(Rank) - len(tmp_dealer[seat])
                tmp_dealer[seat] += cards[:to_deal]
                cards = cards[to_deal:]
            for s in Strain:
                max_trick = solve(tmp_dealer, s ,declarer)
                for level in range(1, 8):
                    idx = idx_table[s][level-1]
                    if mode == "IMP":
                        score = IMP_TABLE[(level, s, max_trick)]
                    else:
                        score = max_trick - level - 6
                    scores_for_all_strains[idx][t] = score
        scores_for_all_strains = np.mean(scores_for_all_strains, axis=-1)
        return scores_for_all_strains


    @classmethod
    def score(cls, dealer, level, strain, declarer, tries, mode=None):
        # target = level + 6

        dealers = []
        declarers = [declarer] * tries
        strains = [strain] * tries

        for _ in range(tries):
            tmp_dealer = deepcopy(dealer)
            cards = dealer["_remaining"]
            random.shuffle(cards)
            for seat in Seat:
                to_deal = len(Rank) - len(tmp_dealer[seat])
                tmp_dealer[seat] += cards[:to_deal]
                cards = cards[to_deal:]
            dealers.append(tmp_dealer)
        max_tricks = solve_all(dealers, strains, declarers)
        if mode == "IMP":
            scores = [IMP_TABLE[(level, strain, trick)] for trick in max_tricks]
            # print("IMP mode....")
        else:
            target = level + 6
            scores = [t - target for t in max_tricks]
        return np.mean(scores)

    @classmethod
    # strain is not cared any longer
    def score_all(cls, dealer, declarer, tries, mode=None):
        dealers = []
        declarers = [declarer] * tries
        strains  = [[i] * tries for i in Strain] # cover strains from 0-4
        scores_for_all_strains = [0] * 35 # for 35 actions

        for _ in range(tries):
            tmp_dealer = deepcopy(dealer)
            cards = dealer["_remaining"]
            random.shuffle(cards)
            for seat in Seat:
                to_deal = len(Rank) - len(tmp_dealer[seat])
                tmp_dealer[seat] += cards[:to_deal]
                cards = cards[to_deal:]
            dealers.append(tmp_dealer)


        for i, s in enumerate(Strain): # 0-4
            max_tricks = solve_all(dealers, strains[i], declarers)

            for level in range(1, 8): # 1-7
                if mode == "IMP":
                    scores = [IMP_TABLE[(level, s, trick)] for trick in max_tricks]
                else:
                    target = level+6
                    scores = [t - target for t in max_tricks]

                idx = convert_level_strain2action(level, s) # find the action idx
                scores_for_all_strains[idx] = np.mean(scores)

        return scores_for_all_strains


