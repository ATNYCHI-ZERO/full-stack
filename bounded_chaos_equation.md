# Bounded Chaos Meta-System

We define the composite operator

\\[
\Phi(x, t) = \left[\frac{\mathrm{d}H}{\mathrm{d}t}\right]
             \left[x^{x-1}\right]
             \left[z^2 + \frac{1}{\overline{z}}\right]
             \left[-\frac{\mathrm{d}^2}{\mathrm{d}x^2} \ln P(x)\right]
             \left[\int_{-\infty}^{t} e^{i \psi(\tau)} \, \mathrm{d}\tau\right]
             \left[\int_{0}^{t} e^{i C(\tau)} \, \mathrm{d}\tau\right]
\\]

subject to the internal definitions

\\[
\frac{\mathrm{d}H}{\mathrm{d}t} = \frac{1}{2} \left(H + \frac{1}{H}\right), \quad
\psi_{n+1}(x) = \int_{-\infty}^{\infty} e^{i \psi_n(t)} \, \mathrm{d}t,\; \psi_0(x) = x,
\\]
\\[
C(t) = \int_{0}^{t} e^{i C(\tau)} \, \mathrm{d}\tau, \quad
P(x) > 0, \; \int_{-\infty}^{\infty} P(x) \, \mathrm{d}x = 1.
\\]

This construction entwines six dynamical components—harmonic relaxation, reflective exponentiation, complex inversion, entropic curvature, recursive eigenfunctions, and chrono-fold dynamics—into a single mixed-domain operator. Each factor injects its domain-specific dynamics, yielding an attractor that remains bounded yet never repeats.

To explore the system numerically, see `simulate_phi.py`.
