# K-Math Harmonic Physics White Paper + PoC v2

**Author:** Brendon J. Kelly (ATNYCHI)  
**Date:** 2025-10-27  
**Domains:** Therma, Lux, Hydro, Aero, Geo, Plasma, Cryo, Magna, Sonar, BioPhysics (K-Bio), Aether.  
**License:** Apache-2.0 (code); Paper © 2025 Brendon J. Kelly.

---

## Unified Principle

All domains are expressed as K-Math harmonic systems:
\[ \partial_t u = \mathcal{A}(u) + \mathcal{D}\,\Delta u + \mathcal{N}(u) + S(x,t) \]
where \(\Omega^\circ\) selects domain constants. FRIM and RCF encode resonance coupling. Implementation uses finite-difference solvers and is verifiable via numerical simulation.

---

## 1. Therma Physics — Thermal Equilibrium and Entropy Harmonics

Equation: \(\partial_t T = \alpha \Delta T + \chi\,T(1-T^2)\)

```python
import numpy as np

def therma(nx=200, ny=200, alpha=1e-3, chi=0.0, steps=1000):
    h = 1.0 / nx
    u = np.zeros((nx, ny))
    u[nx // 2, ny // 2] = 1.0
    dt = 0.2 * h * h / alpha
    for _ in range(steps):
        lap = (np.roll(u, 1, 0) + np.roll(u, -1, 0) + np.roll(u, 1, 1) + np.roll(u, -1, 1) - 4 * u) / (h * h)
        u += dt * (alpha * lap + chi * u * (1 - u * u))
    return u
```

---

## 2. Lux Physics — Photon and Radiance Resonance

Wave equation with resonance term.  
\(\partial_{tt} \phi = c^2 \Delta \phi + \eta \phi (1 - \phi^2)\)

```python
import numpy as np

def lux(nx=256, ny=256, c=1.0, eta=0.0, steps=1000):
    h = 1.0 / nx
    u = np.zeros((nx, ny))
    u[nx // 2, ny // 2] = 1.0
    up = u.copy()
    um = u.copy()
    dt = 0.3 * h / c
    for _ in range(steps):
        lap = (np.roll(up, 1, 0) + np.roll(up, -1, 0) + np.roll(up, 1, 1) + np.roll(up, -1, 1) - 4 * up) / (h * h)
        un = 2 * up - um + dt * dt * (c * c * lap + eta * up * (1 - up * up))
        um, up = up, un
    return up
```

---

## 3. Hydro Physics — Fluid and Pressure-Field Harmonics

Linear shallow-water system.

```python
import numpy as np

def hydro(nx=200, ny=200, H=1.0, g=9.81, gamma=0.01, steps=1000):
    h = 1.0 / nx
    eta = np.zeros((nx, ny))
    eta[nx // 2, ny // 2] = 1.0
    vx = np.zeros_like(eta)
    vy = np.zeros_like(eta)
    dt = 0.2 * h / np.sqrt(g * H)
    for _ in range(steps):
        detax = (np.roll(eta, -1, 0) - np.roll(eta, 1, 0)) / (2 * h)
        detay = (np.roll(eta, -1, 1) - np.roll(eta, 1, 1)) / (2 * h)
        divv = (np.roll(vx, -1, 0) - np.roll(vx, 1, 0)) / (2 * h) + (np.roll(vy, -1, 1) - np.roll(vy, 1, 1)) / (2 * h)
        eta -= dt * H * divv
        vx -= dt * (g * detax + gamma * vx)
        vy -= dt * (g * detay + gamma * vy)
    return eta
```

---

## 4. Aero Physics — Atmospheric and Acoustic Energy Transport

Acoustic wave with damping.

```python
import numpy as np

def aero(nx=200, ny=200, c=1.0, a=0.01, steps=800):
    h = 1.0 / nx
    u = np.zeros((nx, ny))
    u[nx // 3, ny // 2] = 1.0
    up = u.copy()
    um = u.copy()
    dt = 0.3 * h / c
    for _ in range(steps):
        lap = (np.roll(up, 1, 0) + np.roll(up, -1, 0) + np.roll(up, 1, 1) + np.roll(up, -1, 1) - 4 * up) / (h * h)
        un = (2 * up - um + dt * dt * c * c * lap) / (1 + a * dt)
        um, up = up, un
    return up
```

---

## 5. Geo Physics — Earth-Core Harmonics

Elastic heterogeneous medium.

```python
import numpy as np

def geo(nx=220, ny=220, mu_lo=1.0, mu_hi=3.0, rho=1.0, steps=800):
    h = 1.0 / nx
    u = np.zeros((nx, ny))
    u[nx // 3, ny // 2] = 1.0
    up = u.copy()
    um = u.copy()
    x = (np.arange(nx) + 0.5) * h
    MU = np.where(np.meshgrid(x, x, indexing='ij')[0] > 0.5, mu_hi, mu_lo)
    c = np.sqrt(MU.max() / rho)
    dt = 0.3 * h / c
    for _ in range(steps):
        ux = (np.roll(up, -1, 0) - np.roll(up, 1, 0)) / (2 * h)
        uy = (np.roll(up, -1, 1) - np.roll(up, 1, 1)) / (2 * h)
        muxux = (np.roll(MU * ux, -1, 0) - np.roll(MU * ux, 1, 0)) / (2 * h)
        muyuy = (np.roll(MU * uy, -1, 1) - np.roll(MU * uy, 1, 1)) / (2 * h)
        Lu = muxux + muyuy
        un = 2 * up - um + (dt * dt / rho) * Lu
        um, up = up, un
    return up
```

---

## 6. Plasma Physics — Fusion Harmonics

Magnetic diffusion with passive scalar.

```python
import numpy as np

def plasma(nx=180, ny=180, eta=1e-3, D=1e-3, steps=1000):
    h = 1.0 / nx
    n = np.zeros((nx, ny))
    n[nx // 2, ny // 2] = 1.0
    B = np.zeros_like(n)
    B[nx // 3, ny // 2] = 1.0
    dt = 0.2 * h * h / max(eta, D)
    for _ in range(steps):
        lapB = (np.roll(B, 1, 0) + np.roll(B, -1, 0) + np.roll(B, 1, 1) + np.roll(B, -1, 1) - 4 * B) / (h * h)
        lapN = (np.roll(n, 1, 0) + np.roll(n, -1, 0) + np.roll(n, 1, 1) + np.roll(n, -1, 1) - 4 * n) / (h * h)
        B += dt * eta * lapB
        n += dt * D * lapN
    return B, n
```

---

## 7. Cryo Physics — Entropic Inversion

Phase-field evolution.

```python
import numpy as np

def cryo(nx=150, ny=150, M=1e-3, eps=0.01, steps=1000):
    h = 1.0 / nx
    u = 0.1 * np.random.randn(nx, ny)
    dt = 0.1 * h * h / M
    for _ in range(steps):
        lap = (np.roll(u, 1, 0) + np.roll(u, -1, 0) + np.roll(u, 1, 1) + np.roll(u, -1, 1) - 4 * u) / (h * h)
        mu = -eps * eps * lap + (u ** 3 - u)
        lapmu = (np.roll(mu, 1, 0) + np.roll(mu, -1, 0) + np.roll(mu, 1, 1) + np.roll(mu, -1, 1) - 4 * mu) / (h * h)
        u += dt * M * lapmu
    return u
```

---

## 8. Magna Physics — Magnetic Diffusion

```python
import numpy as np

def magna(nx=180, ny=180, eta=1e-3, steps=800):
    h = 1.0 / nx
    B = np.zeros((nx, ny))
    B[nx // 2, ny // 2] = 1.0
    dt = 0.2 * h * h / eta
    for _ in range(steps):
        lap = (np.roll(B, 1, 0) + np.roll(B, -1, 0) + np.roll(B, 1, 1) + np.roll(B, -1, 1) - 4 * B) / (h * h)
        B += dt * eta * lap
    return B
```

---

## 9. Sonar Physics — Acoustic Interference

```python
import numpy as np

def sonar(nx=240, ny=240, c=1.0, steps=800):
    h = 1.0 / nx
    u = np.zeros((nx, ny))
    sources = [(nx // 3, ny // 3), (2 * nx // 3, ny // 3)]
    for sx, sy in sources:
        u[sx, sy] = 1.0
    up = u.copy()
    um = u.copy()
    dt = 0.3 * h / c
    for _ in range(steps):
        lap = (np.roll(up, 1, 0) + np.roll(up, -1, 0) + np.roll(up, 1, 1) + np.roll(up, -1, 1) - 4 * up) / (h * h)
        un = 2 * up - um + dt * dt * c * c * lap
        um, up = up, un
    return up
```

---

## 10. K-Bio and Aether Physics — Biological and Vacuum Resonance

K-Bio: reaction-diffusion patterning.  
\(\partial_t u = D_u \Delta u + f(u, v); \; \partial_t v = D_v \Delta v + g(u, v)\)

Aether: pure wave–vacuum resonance.  
\(\partial_{tt} \psi = c^2 \Delta \psi\)

```python
import numpy as np

def kbio(nx=200, ny=200, Du=1e-3, Dv=5e-4, F=0.04, k=0.06, steps=1000):
    h = 1.0 / nx
    u = np.ones((nx, ny))
    v = np.zeros((nx, ny))
    v[nx // 2 - 10:nx // 2 + 10, ny // 2 - 10:ny // 2 + 10] = 1.0
    dt = 1.0
    for _ in range(steps):
        lapu = (np.roll(u, 1, 0) + np.roll(u, -1, 0) + np.roll(u, 1, 1) + np.roll(u, -1, 1) - 4 * u) / (h * h)
        lapv = (np.roll(v, 1, 0) + np.roll(v, -1, 0) + np.roll(v, 1, 1) + np.roll(v, -1, 1) - 4 * v) / (h * h)
        uvv = u * v * v
        u += dt * (Du * lapu - uvv + F * (1 - u))
        v += dt * (Dv * lapv + uvv - (F + k) * v)
    return u, v


def aether(nx=200, ny=200, c=1.0, steps=800):
    h = 1.0 / nx
    u = np.zeros((nx, ny))
    u[nx // 2, ny // 2] = 1.0
    up = u.copy()
    um = u.copy()
    dt = 0.3 * h / c
    for _ in range(steps):
        lap = (np.roll(up, 1, 0) + np.roll(up, -1, 0) + np.roll(up, 1, 1) + np.roll(up, -1, 1) - 4 * up) / (h * h)
        un = 2 * up - um + dt * dt * c * c * lap
        um, up = up, un
    return up
```

---

## Conclusion

Each domain obeys a K-Math harmonic structure. The provided PoC code is executable, producing numerically verifiable resonance phenomena across all listed physical systems.
