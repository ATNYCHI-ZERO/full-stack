# full-stack

Utilities implementing the TRI-CROWN annexes: process-matrix discretisation,
finite-horizon LQR, robust regression, text/cipher helpers, and Kalman filters
for the falling-body model.

## Python package

Install the dependencies (only NumPy is required; SciPy is optional for the
matrix exponential) and import the utilities:

```python
from tri_crown import (
    process_matrix,
    van_loan_discretization,
    mean_squared_deviation,
    huber_irls,
    caesar_cipher,
    discretize_falling_body,
    kalman_step,
)
```

See the docstrings for detailed behaviour.
