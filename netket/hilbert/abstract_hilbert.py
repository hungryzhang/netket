import abc


class AbstractHilbert(abc.ABC):
    """Abstract class for NetKet hilbert objects"""

    @property
    @abc.abstractmethod
    def hilbert(self):
        r"""AbstractHilbert: The Hilbert space associated with this operator."""
        return NotImplementedError

    @abc.abstractmethod
    def random_vals(self, rgen=None):
        r"""Member function generating uniformely distributed local random states.

        Args:
            state: A reference to a visible configuration, in output this
                  contains the random state.
            rgen: The random number generator. If None, the global
                 NetKet random number generator is used.

        Examples:
           Test that a new random state is a possible state for the hilbert
           space.

           >>> import netket as nk
           >>> import numpy as np
           >>> hi = nk.hilbert.Boson(n_max=3, graph=nk.graph.Hypercube(length=5, n_dim=1))
           >>> rstate = np.zeros(hi.size)
           >>> rg = nk.utils.RandomEngine(seed=1234)
           >>> hi.random_vals(rstate, rg)
           >>> local_states = hi.local_states
           >>> print(rstate[0] in local_states)
           True
           """
        pass