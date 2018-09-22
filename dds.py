# vim: set fileencoding=utf-8
from __future__ import division, print_function
# for pypy compatibility we do not use unicode_literals in this module
from ctypes import *
import os
import sys
import warnings
import numpy as np
from config import *
from bridge_utils import convert_id2rank, convert_id2suit


class Deal(Structure):
    """The deal struct.
    """

    _fields_ = [("trump", c_int), # 0=S, 1=H, 2=D, 3=C, 4=NT
                ("first", c_int), # leader: 0=N, 1=E, 2=S, 3=W
                ("currentTrickSuit", c_int * 3),
                ("currentTrickRank", c_int * 3), # 2-14, up to 3 cards; 0=unplayed
                ("remainCards", c_uint * 4 * 4)]

    @classmethod
    def from_deal(cls, deal, strain, leader):
        self = cls(trump=strain,
                   first=leader,
                   currentTrickSuit=(c_int * 3)(0, 0, 0),
                   currentTrickRank=(c_int * 3)(0, 0, 0))
        # bit #i (2 ≤ i ≤ 14) is set if card of rank i (A = 14) is held
        for seat in Seat:
            holding = np.zeros(4 ,dtype=np.int32)
            for card in deal[seat]:
                suit = convert_id2suit(card)
                rank = convert_id2rank(card)
                holding[suit] += (1 << rank)
            for suit in Suit:
                self.remainCards[seat][suit] = holding[suit]
        return self


class Boards(Structure):

    _fields_ = [("noOfBoards", c_int),
                ("deals", Deal * MAXNOOFBOARDS),
                ("target", c_int * MAXNOOFBOARDS),
                ("solutions", c_int * MAXNOOFBOARDS),
                ("mode", c_int * MAXNOOFBOARDS)]

    @classmethod
    def from_board(cls, n, deals, strains, leaders, targets, solutions, modes):
        # deals here is a list of dictionary

        self = cls(noOfBoards=n)
        # TO Save the wasted spaces in the process, you need to modify the MAXNOOFBOARDS in
        # the C++ code
        # Deal_Array_MAXNOOFBOARDS or c_int_Array_MAXNOOFBOARDS
        for i in range(n):
            self.deals[i] = Deal.from_deal(deals[i], strains[i], leaders[i])
            self.target[i] = targets[i]
            self.solutions[i] = solutions[i]
            self.mode[i] = modes[i]
        return self


class FutureTricks(Structure):
    """The futureTricks struct.
    """

    _fields_ = [("nodes", c_int),
                ("cards", c_int),
                ("suit", c_int * 13),
                ("rank", c_int * 13),
                ("equals", c_int * 13),
                ("score", c_int * 13)]


class solvedBoards(Structure):
    _fields_ = [("noOfBoards", c_int),
                ("solvedBoard", FutureTricks * MAXNOOFBOARDS)]

    @classmethod
    def init_n_futps(cls, n):
        self = cls(noOfBoards=n)
        for i in range(n):
            self.solvedBoard[i] = FutureTricks()
        return self

SolveBoardStatus = {
    1: "No fault",
    -1: "Unknown fault",
    -2: "Zero cards",
    -3: "Target > tricks left",
    -4: "Duplicated cards",
    -5: "Target < -1",
    -7: "Target > 13",
    -8: "Solutions < 1",
    -9: "Solutions > 3",
    -10: "> 52 cards",
    -12: "Invalid deal.currentTrick{Suit,Rank}",
    -13: "Card played in current trick is also remaining",
    -14: "Wrong number of remaining cards in a hand",
    -15: "threadIndex < 0 or >=noOfThreads, noOfThreads is the configured "
         "maximum number of threads"}


def _solve_board(deal, strain, leader, target, sol, mode):
    c_deal = Deal.from_deal(deal, strain, leader)
    futp = FutureTricks()
    status = dll.SolveBoard(c_deal, target, sol, mode, byref(futp), 0)
    if status != 1:
        raise Exception("SolveBoard({}, ...) failed with status {} ({}).".
                        format(deal, status, SolveBoardStatus[status]))
    return futp


def solve(deal, strain, declarer):
    """Return the number of tricks for declarer; wraps SolveBoard.
    """
    leader = (declarer + 1)%4
    # find one optimal card with its score, even if only one card
    futp = _solve_board(deal, strain, leader, -1, 1, 1)
    best_score = len(Rank) - futp.score[0]
    return best_score


def _solve_all_boards(n, deals, strains, leaders, targets, solutions, modes):
    c_boards = Boards.from_board(n, deals, strains, leaders, targets, solutions, modes)
    # print("prepare board done")
    n_futps = solvedBoards.init_n_futps(n)
    #  https://github.com/dds-bridge/dds/blob/7af2b0ca801cb54b9d742ed4593b1809c7c5da61/src/SolveBoard.cpp#L265
    # SolveAllBoardsN is not externed.
    status = dll.SolveAllChunksBin(byref(c_boards), byref(n_futps), 1)
    #  https://github.com/dds-bridge/dds/blob/7af2b0ca801cb54b9d742ed4593b1809c7c5da61/src/SolveBoard.cpp#L418
    if status != 1:
        raise Exception("SolveAllBoard({}, ...) failed with status {} ({}).".
                        format(deals, status, SolveBoardStatus[status]))
    return n_futps


def solve_all(deals, strains, decalers):
    n = len(deals)
    # You can only change MAXNOOFBOARDS in the C++ code before you build the libdds.so.
    # https://github.com/dds-bridge/dds/blob/7af2b0ca801cb54b9d742ed4593b1809c7c5da61/include/dll.h#L38
    if n > MAXNOOFBOARDS:
        raise Exception("The number of boards exceeds the limit.")

    leaders = [(d + 1)%4 for d in decalers]
    targets = [-1]*n
    sols = [1]*n
    modes = [1]*n
    # print("Preparation done")
    n_futp = _solve_all_boards(n, deals, strains, leaders, targets, sols, modes)
    best_scores = [len(Rank)-n_futp.solvedBoard[i].score[0] for i in range(n)]
    return best_scores


# assume Unix by default
os.name = "posix"
dll_name = "libdds.so"
DLL = CDLL
# absolute path
dll_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        dll_name)

if dll_name and os.path.exists(dll_path):
    dll = DLL(dll_path)
    dll.SolveBoard.argtypes = [
        Deal, c_int, c_int, c_int, POINTER(FutureTricks), c_int]
    if os.name == "posix":
        dll.SetMaxThreads(0)
else:
    def solve(deal, strain, declarer):
        raise Exception("Unable to load DDS.  `solve` is unavailable.")

    def valid_cards(deal, strain, leader):
        raise Exception("Unable to load DDS.  `valid_cards` is unavailable.")

    def solve_all(deals, strains, declarers):
        raise Exception("Unable to load DDS.  `solve_all` is unavailable.")
