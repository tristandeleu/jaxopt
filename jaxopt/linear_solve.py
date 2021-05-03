# Copyright 2021 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Linear system solvers."""

from typing import Any
from typing import Callable

import jax
import jax.numpy as jnp


def _materialize_array(matvec, shape):
  if len(shape) == 1:
    I = jnp.eye(shape[0])
    return jax.vmap(matvec)(I).T
  elif len(shape) == 2:
    I = jnp.eye(shape[0] * shape[1])
    I = I.reshape(-1, shape[0], shape[1])
    return jax.vmap(matvec)(I).reshape(-1, shape[0] * shape[1]).T
  else:
    raise NotImplementedError


def solve_lax(matvec: Callable, b: jnp.ndarray) -> jnp.ndarray:
  """Solves ``A x = b`` using ``jax.lax.solve``.

  This solver is based on an LU decomposition.
  It will materialize the matrix ``A`` in memory.

  Args:
    matvec: product between ``A`` and a vector.
    b: array.

  Returns:
    array with same structure as ``b``.
  """
  if len(b.shape) == 1:
    return jax.numpy.linalg.solve(_materialize_array(matvec, b.shape), b)
  elif len(b.shape) == 2:
    A = _materialize_array(matvec, b.shape)
    return jax.numpy.linalg.solve(A, b.ravel()).reshape(*b.shape)
  else:
    raise NotImplementedError


def solve_cg(matvec: Callable, b: Any) -> Any:
  """Solves ``A x = b`` using conjugate gradient.

  It assumes that ``A`` is  a Hermitian, positive definite matrix.

  Args:
    matvec: product between ``A`` and a vector.
    b: pytree.

  Returns:
    pytree with same structure as ``b``.
  """
  return jax.scipy.sparse.linalg.cg(matvec, b)[0]


def _rmatvec(matvec, x):
  """Computes rmatvec(x) = A^T x, given matvec(x) = A x."""
  transpose = jax.linear_transpose(matvec, x)
  return transpose(x)[0]


def solve_normal_cg(matvec: Callable, b: Any) -> Any:
  """Solves the normal equation ``A^T A x = A^T b`` using conjugate gradient.

  This can be used to solve Ax=b using conjugate gradient when A is not
  hermitian, positive definite.

  Args:
    matvec: product between ``A`` and a vector.
    b: pytree.

  Returns:
    pytree with same structure as ``b``.
  """
  def _matvec(x):
    """Computes A^T A x."""
    return _rmatvec(matvec, matvec(x))

  Ab = _rmatvec(matvec, b)
  return jax.scipy.sparse.linalg.cg(_matvec, Ab)[0]


def solve_gmres(matvec: Callable, b: Any) -> Any:
  """Solves ``A x = b`` using gmres.

  Args:
    matvec: product between ``A`` and a vector.
    b: pytree.

  Returns:
    pytree with same structure as ``b``.
  """
  return jax.scipy.sparse.linalg.gmres(matvec, b)[0]
