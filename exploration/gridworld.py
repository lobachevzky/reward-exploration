#! /usr/bin/env python
# stdlib
from collections import namedtuple
import sys
import time
from typing import Dict, Iterable, Tuple, Container

# third party
from gym import utils
from gym.envs.toy_text.discrete import DiscreteEnv
import numpy as np
from six import StringIO

Transition = namedtuple('Transition', 'probability new_state reward terminal')


class Gridworld(DiscreteEnv):
    def __init__(self,
                 desc: Iterable[Iterable[str]],
                 terminal: Container[str],
                 rewards: Dict[str, float],
                 start_states: Container[str] = '',
                 actions: Iterable[np.ndarray] = np.array([
                     [0, 1],
                     [1, 0],
                     [0, -1],
                     [-1, 0],
                 ]),
                 action_strings: Iterable[str] = "▶▼◀▲"):

        self.action_strings = np.array(tuple(action_strings))
        self.desc = _desc = np.array(
            [list(r) for r in desc])  # type: np.ndarray
        nrows, ncols = _desc.shape
        self._transition_matrix = None
        self._reward_matrix = None

        def transition_tuple(i: int, j: int) -> Tuple[float, int, float, bool]:
            i = np.clip(i, 0, nrows - 1)  # type: int
            j = np.clip(j, 0, ncols - 1)  # type: int
            letter = str(_desc[i, j])
            return Transition(
                probability=1.,
                new_state=self.encode(i, j),
                reward=rewards.get(letter, 0),
                terminal=letter in terminal)

        transitions = {
            self.encode(i, j): {
                a: [transition_tuple(*np.array([i, j]) + action)]
                for a, action in enumerate(actions)
            }
            for i in range(nrows) for j in range(ncols)
        }
        isd = np.isin(_desc, tuple(start_states))
        isd = isd / isd.sum()
        super().__init__(
            nS=_desc.size,
            nA=len(actions),
            P=transitions,
            isd=isd.flatten(),
        )

    def render(self, mode='human'):
        outfile = StringIO() if mode == 'ansi' else sys.stdout
        out = self.desc.copy().tolist()
        i, j = self.decode(self.s)

        out[i][j] = utils.colorize(out[i][j], 'blue', highlight=True)

        for row in out:
            print("".join(row))
        if self.lastaction is not None:
            print(f"({self.action_strings[self.lastaction]})\n")
        else:
            print("\n")
        # No need to return anything for human
        if mode != 'human':
            return outfile
        out[i][j] = self.desc[i, j]

    def encode(self, i: int, j: int) -> int:
        nrow, ncol = self.desc.shape
        assert 0 <= i < nrow
        assert 0 <= j < ncol
        return i * ncol + j

    def decode(self, s: int) -> Tuple[int, int]:
        nrow, ncol = self.desc.shape
        assert 0 <= s < nrow * ncol
        return s // nrow, s % ncol

    def generate_matrices(self):
        self._transition_matrix = np.zeros((self.nS, self.nA, self.nS))
        self._reward_matrix = np.zeros((self.nS, self.nA, self.nS))
        for s1, action_P in self.P.items():
            for a, transitions in action_P.items():
                trans: Transition
                for trans in transitions:
                    self._transition_matrix[s1, a, trans.
                                            new_state] = trans.probability
                    self._reward_matrix[s1, a] = trans.reward
                    if trans.terminal:
                        for a in range(self.nA):
                            self._transition_matrix[trans.new_state, a, trans.
                                                    new_state] = 1
                            self._reward_matrix[trans.new_state, a] = 0
                            assert not np.any(self._transition_matrix > 1)

    @property
    def transition_matrix(self) -> np.ndarray:
        if self._transition_matrix is None:
            self.generate_matrices()
        return self._transition_matrix

    @property
    def reward_matrix(self) -> np.ndarray:
        if self._reward_matrix is None:
            self.generate_matrices()
        return self._reward_matrix


if __name__ == '__main__':
    env = Gridworld(
        desc=['_t', '__'], rewards=dict(t=1), terminal=dict(t=True))
    env.reset()
    while True:
        env.render()
        time.sleep(1)
        env.step(env.action_space.sample())
