# TRI-CROWN Math/Process Annex Reference

This repository contains a compact Python package that implements the
analytical bindings described in the TRI-CROWN 1.1 Math/Process Annex.
The helpers stay clear of the cryptographic core and instead provide the
numerical ingredients – discretised process dynamics, wave propagation,
robust regression and contextual feature extraction – that are combined
into the `s_math` salt folded into the TRI-CROWN handshake.

## Layout

```
tri_crown/
    __init__.py          # Convenience exports.
    math_process.py      # Annex implementation.
tests/
    test_math_process.py # Behavioural smoke tests.
```

## Quick start

1. Install dependencies (NumPy is required; SciPy is optional but used
   when available):

   ```bash
   pip install numpy scipy pytest
   ```

2. Run the test-suite:

   ```bash
   pytest
   ```

3. Import and use the helpers:

   ```python
   import numpy as np
   from tri_crown import green_convolution, math_salt

   A = np.array([[0.0, 1.0], [0.0, 0.0]])
   B = np.eye(2)
   controls = np.ones((4, 2))
   disc = green_convolution(A, B, controls, dt=0.1)

   salt, features = math_salt(disc.phi, disc.gamma, np.eye(2), "example")
   print(salt.hex())
   ```

Each helper is documented in-place and mirrors the corresponding section
of the annex (A–H).  They are intended as a rigorous, testable reference
for integrating the annex with the broader TRI-CROWN stack.
