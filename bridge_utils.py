from collections import defaultdict
from config import *
import numpy as np
import pickle


def convert_id2suit(card_id):
    return card_id//13


def convert_id2rank(card_id):
    return card_id%13+2


def convert_hands2string(deal):
    for seat, hand in deal.items():
        if seat not in Seat:
            continue
        holding = defaultdict(list)
        for card in hand:
            suit = Suit2str[convert_id2suit(card)]
            rank = Rank2str[convert_id2rank(card)]
            holding[suit].append(rank)

        print("Seat ", Seat2str[seat],":")
        for suit in Suit2str.values():
            print(suit, " ".join(holding[suit]))


def one_hot_holding(holding):
    one_hot_res = np.zeros(len(FULL_DECK), dtype=np.float32)
    one_hot_res[holding] = 1
    return one_hot_res

# 0: "S", 1: "H", 2: "D", 3: "C", 4: "N"
# Bid C D H S


def convert_action2strain(action):
    bid_strain = action%5
    return {3:0, 2:1, 1: 2, 0: 3, 4: 4}[bid_strain]


def convert_action2level(action):
    return action//len(Strain) + 1


def convert_level_strain2action(level, strain):
    return len(Strain)*(level-1) + {0: 3, 1: 2, 2: 1, 3: 0, 4: 4}[strain]


def log_state(state, reward, done, info):
    print("Hand: ", state[0])
    print("History: ", state[1])
    print("reward: ", reward)
    print("Finished: ", done)
    print("Whose Turn: ", info["turn"],'\n')


def print_args(args):
    max_length = max([len(k) for k, _ in vars(args).items()])
    for k, v in vars(args).items():
        print(' ' * (max_length-len(k)) + k + ': ' + str(v))


def get_bid_mask(max_bid):
    if max_bid >= 35:
        raise Exception("illegal max bid action, the max_bid must be integers less than 35")
    mask = np.zeros((36,))
    if max_bid >= 0:
        mask[: max_bid+1] = -np.inf # this will set the masked logits to negative inifinity
    return mask


def convert_hands2string_from_obs(obs, seat):
    hand = np.nonzero(obs[:52])[0]
    holding = defaultdict(list)
    for card in hand:
        suit = Suit2str[convert_id2suit(card)]
        rank = Rank2str[convert_id2rank(card)]
        holding[suit].append(rank)
    print(seat)
    for suit in Suit2str.values():
        print(suit, " ".join(holding[suit]))


def convert_action2string(action):
    if action == 35:
        print('bid: PASS')
    else:
        strain = Strain2str[convert_action2strain(action)]
        level = convert_action2level(action)
        print('bid: %i%s' % (level, strain))


def load_deal_data(fn):
    with open(fn, "rb") as f:
        predeals, score, _ =  pickle.load(f)
        score = score/12
        return list(zip(predeals, score))

def load_full_deal_data(fn):
    with open(fn, "rb") as f:
        predeals, score, oh_holdings =  pickle.load(f)
        return predeals, score, oh_holdings