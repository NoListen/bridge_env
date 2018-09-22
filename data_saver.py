from deal import Deal
from copy import deepcopy
from config import *
import random
import numpy as np
from bridge_utils import *
import pickle
import os
from tqdm import tqdm


def store_sample_evaluation(nf, nd, data_path, bidding_seats=[0, 2], nmc=20):
    """
    :param nf: number of files
    :param nd: number of deals per file
    :param prefix: file name prefix
    :param bidding_seats:
    :param nmc:
    """
    if not os.path.exists(data_path):
        os.mkdir(data_path)

    sampler = SampleEvaluation(bidding_seats, nmc)
    for i in range(nf):
        samples = []

        for _ in tqdm(range(nd)):
            eval = sampler.evaluate_new_sample()
            samples.append(eval)

        with open(data_path+"/sample_%i.p" % i, "wb") as f:
            pickle.dump(samples, f)
        print("--- %i data generated ---" % ((i+1)*nd))


# Randomly Sample bidding seats' hands and evaluates all 35 actions.
class SampleEvaluation(object):
    def __init__(self, bidding_seats=[0, 2], nmc=20, debug=False, score_mode="IMP", single_thread=True):
        # deal is the state
        self.deal = None
        self.one_hot_deal = None
        self.cards = deepcopy(FULL_DECK)
        self.nmc = nmc  # MC times
        self.done = False
        self.debug = debug
        self.score_mode = score_mode
        self.bidding_seats = sorted(list(set(bidding_seats)))
        for seat in self.bidding_seats:
            if seat not in Seat:
                raise Exception("illegal seats")
        if single_thread:
            self.score_fn = Deal.score_all_st
        else:
            self.score_fn = Deal.score_all


    def set_mode(self, debug):
        self.debug = debug

    def set_nmc(self, n):
        self.nmc = n
        
    def evaluate_new_sample(self, predeal_seats=None, declarer=None):  # North and South
        """
        :param predeal_seats: if not None, allocate cards to those seats. e.g. [0, 1] stands for North and East
        :param reshuffle: whether reshuffle the hands for the predeal seats
        :return: deal
        """
        if predeal_seats is None:
            predeal_seats = self.bidding_seats

        predeal = {}
        random.shuffle(self.cards)
        i = 0
        self.one_hot_deal = np.zeros((len(Seat), len(FULL_DECK)), dtype=np.uint8)
        for seat in sorted(predeal_seats):
            predeal[seat] = self.cards[i: i+len(Rank)]
            self.one_hot_deal[seat] = one_hot_holding(predeal[seat])  # one hot cards
            i += len(Rank)  # shift the index

        self.deal = Deal.prepare(predeal)
        if self.debug:
            convert_hands2string(self.deal)

        rewards_dict = {}
        if declarer is not None:
            rewards = self.score_fn(dealer=self.deal, declarer=declarer, tries=self.nmc, mode=self.score_mode)
            rewards_dict[declarer] = rewards
        else:
            for s in self.bidding_seats:
                rewards = self.score_fn(dealer=self.deal, declarer=s, tries=self.nmc, mode=self.score_mode)
                rewards_dict[s] = rewards
        return predeal, rewards_dict, self.one_hot_deal[self.bidding_seats]


def test_data():
    store_sample_evaluation(2, 10, "data", nmc=1)


def test_load_data():
    with open("data/sample_0.p", "rb") as f:
        print(pickle.load(f))

