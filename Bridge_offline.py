from deal import Deal
from copy import deepcopy
import random
from bridge_utils import *
import pickle
import os
import glob


class BridgeEnvOffline(object):
    def __init__(self, bidding_seats=[0, 2], debug=False, data_folder='../../data',
                 data_file_prefix='data', n_files_to_load=100):
        # deal is the state
        self.deal = None
        self.one_hot_deal = None
        self.cards = deepcopy(FULL_DECK)
        self.bidding_history = np.zeros(36, dtype=np.uint8) # pass is included in the history
        self.n_pass = 0
        self.max_bid = -1
        self.done = False
        self.debug = debug
        self.strain_declarer = {0: {}, 1: {}}
        self.group_declarer = -1
        self.rewards_table = None
        self.bidding_seats = sorted(list(set(bidding_seats)))
        self.scores_dicts = []
        self.pre_deals_dicts = []
        self.loading_data_order = []
        self.traverse_flag = False
        self.loading_count = 0
        for seat in self.bidding_seats:
            if seat not in Seat:
                raise Exception("illegal seats")
        self.turn = self.bidding_seats[0] # whose turn, start from the smallest one by default.
        self.files_names_in_folder = glob.glob(os.path.join(data_folder, data_file_prefix + '_*'))
        self.n_files_to_load = n_files_to_load if n_files_to_load is not None else len(self.files_names_in_folder)


    def set_mode(self, debug):
        self.debug = debug

    def reset_loaded_files(self):
        assert len(self.files_names_in_folder) >= self.n_files_to_load
        ids = random.sample(list(np.arange(len(self.files_names_in_folder))), self.n_files_to_load)
        files_names_to_load = np.asarray(self.files_names_in_folder)[ids]
        self.scores_dicts = []
        self.pre_deals_dicts = []
        self.traverse_flag = False
        for file in files_names_to_load:
            with open(file, 'rb') as f:
                # (x,h) and s [N, 88], [N, 36]
                card, score, _ = pickle.load(f)
                print('file %s loaded' % file)
                self.pre_deals_dicts.append(card)
                self.scores_dicts.append(score)
        self.pre_deals_dicts = np.concatenate(self.pre_deals_dicts)
        self.scores_dicts = np.concatenate(self.scores_dicts)
        self.loading_data_order = random.sample(list(np.arange(len(self.pre_deals_dicts))), len(self.pre_deals_dicts))
        self.loading_count = 0
        print('%i of data points loaded' % len(self.pre_deals_dicts))

    # Attention: Force predeal seats to be the same as bidding seats
    def reset(self):  # North and South
        """
        :param reshuffle: whether reshuffle the hands for the predeal seats
        :return: deal
        """
        if len(self.scores_dicts) == 0:
            raise Exception("Please set the data in adavance")

        self.bidding_history = np.zeros(36, dtype=np.uint8) # 1C 1D 1H 1S 1N ... 7N (PASS - not considered)
        self.max_bid = -1
        self.n_pass = 0
        self.turn = self.bidding_seats[0] # the first one.
        self.done = False
        self.strain_declarer = {0: {}, 1: {}}
        self.group_declarer = -1
        idx = self.loading_data_order[self.loading_count]
        predeal, self.rewards_table = self.pre_deals_dicts[idx], self.scores_dicts[idx]
        self.loading_count += 1
        self.one_hot_deal = np.zeros((len(Seat), len(FULL_DECK)), dtype=np.uint8)
        for seat, hands in predeal.items():
            self.one_hot_deal[seat] = one_hot_holding(hands) # one hot cards
        # update the deal
        self.deal = Deal.prepare(predeal)
        if self.loading_count >= len(self.loading_data_order):  # reshuffle the indices
                self.loading_count = 0
                self.loading_data_order = random.sample(list(np.arange(len(self.pre_deals_dicts))),
                                                        len(self.pre_deals_dicts))
                self.traverse_flag = True
        if self.debug:
            convert_hands2string(self.deal)
        # if not allocated, zero vector is returned.
        return (self.one_hot_deal[self.turn], self.bidding_history), {"turn": Seat[self.turn], "max_bid": self.max_bid,
                                                                      "traverse": self.traverse_flag}

    def step(self, action):
        """
        :param action: bid action
        :param tries: MC tries.
        :return: state, reward, done
        """
        if self.done:
            raise Exception("No more actions can be taken")

        if action < 0 or action > 35:
            raise Exception("illegal action")

        if action == 35:  # PASS
            self.bidding_history[action] = 1 # PASS
            self.n_pass += 1
        else:
            if action <= self.max_bid:
                raise Exception("illegal bidding.")
            self.bidding_history[action] = 1
            self.bidding_history[-1] = 0 # reset PASS
            self.n_pass = 0
            self.max_bid = action

            strain = convert_action2strain(action)
            group = Seat2Group[self.turn]
            if self.strain_declarer[group].get(strain, '') == '':
                self.strain_declarer[group][strain] = self.turn  # which one
            self.group_declarer = group # which group

        self.turn = (self.turn+1) % len(Seat)  # loop
        while True:  # move to the participant
            if self.turn not in self.bidding_seats:
                self.turn = (self.turn+1) % len(Seat)
                self.n_pass += 1
            else:
                break

        hand = self.one_hot_deal[self.turn]
        reward = 0
        # state is the next bidding player's state
        if self.n_pass >= 3 or self.max_bid == 34:
            if self.max_bid < 0:
                raise Exception("illegal bidding")
            # extract the declarer, strain , level
            strain = convert_action2strain(self.max_bid)
            declarer = self.strain_declarer[self.group_declarer][strain]
            reward = self.rewards_table[declarer][self.max_bid]
            self.done = True

        state = (hand, self.bidding_history)
        info = {"turn": Seat[self.turn], "max_bid": self.max_bid, "traverse": self.traverse_flag}
        if self.debug:
            log_state(state, reward, self.done, info)
        return state, reward, self.done, info