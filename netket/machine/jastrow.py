# Copyright 2020 The Simons Foundation, Inc. - All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from .abstract_machine import AbstractMachine
import numpy as _np
from numba import jit


class Jastrow(AbstractMachine):
    r"""
    A Jastrow wavefunction Machine. This machine defines the following
    wavefunction:

    .. math:: \Psi(s_1,\dots s_N) = e^{\sum_{ij} s_i W_{ij} s_j + \sum_{i} a_i s_i}

    where :math:` W_{ij}` are the two-body Jastrow parameters and a_i are optional
    visible bias (single-body effective potential).
    The weights can be taken to be complex-valued (default option) or real-valued.
    """

    def __init__(
        self, hilbert, use_visible_bias=False, dtype=complex,
    ):
        r"""
        Constructs a new ``Jastrow`` machine:

        Args:
         hilbert: Hilbert space object for the system.
         use_visible_bias (bool): Whether to use the visible bias a_i.
         dtype: either complex or float, it is the type used for the weights and biases.

        Examples:
            A ``Jastrow`` machine for a one-dimensional L=20 spin 1/2
            system:


            >>> from netket.machine import Jastrow
            >>> from netket.hilbert import Spin
            >>> from netket.graph import Hypercube
            >>> g = Hypercube(length=20, n_dim=1)
            >>> hi = Spin(s=0.5, total_sz=0, graph=g)
            >>> ma = Jastrow(hilbert=hi)
            >>> print(ma.n_par)
            190

        """

        n = hilbert.size

        if dtype is not float and dtype is not complex:
            raise TypeError("dtype must be either float or complex")

        self._dtype = dtype
        self._npdtype = _np.complex128 if dtype is complex else _np.float64

        if n < 2:
            raise ValueError(
                "Cannot construct a Jastrow factor with less than two visible units."
            )

        n_sym = int((n * (n - 1)) // 2)

        # The symmetric part of J is stored in a 1d array
        self._J = _np.zeros(n_sym, dtype=self._npdtype)

        # Visible bias
        self._a = _np.empty(n, dtype=self._npdtype) if use_visible_bias else None

        self._npar = n_sym + (self._a.size if self._a is not None else 0)

        super().__init__(hilbert)

    @property
    def n_par(self):
        r"""The number of variational parameters in the machine."""
        return self._npar

    def log_val(self, x, out=None):
        r"""Computes the logarithm of the wave function for a batch of visible
        configurations `x` and stores the result into `out`.

        Args:
            x: A matrix of `float64` of shape `(*, self.n_visible)`.
            out: Destination vector of `complex128`. The
                 length of `out` should be `x.shape[0]`.

        Returns:
            A complex number when `x` is a vector and vector when `x` is a
            matrix.
            """
        x = x.astype(dtype=self._npdtype)

        return self._log_val_kernel(x, out, self._J, self._a)

    @staticmethod
    @jit(nopython=True)
    def _log_val_kernel(x, out, J, a):
        if out is None:
            out = _np.empty(x.shape[0], dtype=_np.complex128)

        n = x.shape[1]

        for b in range(x.shape[0]):
            out[b] = 0.0
            k = 0
            for i in range(n):
                for j in range(i + 1, n, 1):
                    out[b] += x[b, i] * J[k] * x[b, j]
                    k += 1

        if a is not None:
            out = out + x.dot(a)

        return out

    def der_log(self, x, out=None):
        r"""Computes the gradient of the logarithm of the wavefunction for a
        batch of visible configurations `x` and stores the result into `out`.

        Args:
            x: A matrix of `float64` of shape `(*, self.n_visible)`.
            out: Destination tensor of `complex128`.
                `out` should be a matrix of shape `(v.shape[0], self.n_par)`.

        Returns:
            `out`
            """
        x = x.astype(dtype=self._npdtype)

        return self._der_log_kernel(x, out, self._a, self._J, self._npar)

    @staticmethod
    @jit(nopython=True)
    def _der_log_kernel(x, out, a, J, n_par):
        batch_size = x.shape[0]

        if out is None:
            out = _np.empty((batch_size, n_par), dtype=_np.complex128)

        n = x.shape[1]

        if a is not None:
            out[:, 0:n] = x

        for b in range(batch_size):
            k = 0 if a is None else n
            for i in range(n):
                for j in range(i + 1, n, 1):
                    out[b, k] = x[b, i] * x[b, j]
                    k += 1

        return out

    @property
    def is_holomorphic(self):
        r"""Complex valued Jastrow is a holomorphic function.
        """
        return self._dtype is complex

    @property
    def state_dict(self):
        r"""A dictionary containing the parameters of this machine"""
        from collections import OrderedDict

        od = OrderedDict()
        if self._dtype is complex:
            if self._a is not None:
                od["a"] = self._a.view()

            od["J"] = self._J.view()
        else:
            if self._a is not None:
                self._ac = self._a.astype(_np.complex128)
                self._a = self._ac.real.view()
                od["a"] = self._ac.view()

            self._Jc = self._J.astype(_np.complex128)
            self._J = self._Jc.real.view()
            od["J"] = self._Jc.view()

        return od