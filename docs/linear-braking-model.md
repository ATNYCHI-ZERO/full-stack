# Linear Mathematical Model of Braking Systems

## 1. Introduction
This document summarizes a linear model for vehicle braking that assumes a constant braking force and neglects non-linear effects such as aerodynamic drag. The goal is to derive closed-form expressions for velocity, stopping time, and stopping distance under those assumptions.

## 2. Fundamental Principles and Variables
The model relies on Newton's Second Law of Motion and a classical kinetic friction model.

| Symbol | Meaning |
| --- | --- |
| $m$ | Vehicle mass (kg) |
| $v_0$ | Initial velocity (m/s) |
| $v(t)$ | Velocity as a function of time (m/s) |
| $F_{\text{brake}}$ | Total braking force (N) |
| $\mu_k$ | Coefficient of kinetic friction (dimensionless) |
| $N$ | Normal force (N) |
| $g$ | Gravitational acceleration ($\approx 9.81\,\text{m/s}^2$) |
| $x(t)$ | Position as a function of time (m) |
| $t_{\text{stop}}$ | Stopping time (s) |
| $d_{\text{stop}}$ | Stopping distance (m) |

## 3. Derivation of the Equation of Motion
Newton's Second Law for motion along the direction of travel gives:

$$\sum F = ma = -F_{\text{brake}}$$

Using $F_{\text{brake}} = \mu_k N$ and $N = mg$ (for a level surface) produces the first-order differential equation:

$$m \frac{dv}{dt} = -\mu_k mg$$

which simplifies to a constant deceleration:

$$\frac{dv}{dt} = -\mu_k g.$$

## 4. Velocity, Position, and Stopping Metrics
Integrating the acceleration yields the velocity profile:

$$v(t) = v_0 - \mu_k g t.$$

Setting $v(t_{\text{stop}}) = 0$ gives the stopping time:

$$t_{\text{stop}} = \frac{v_0}{\mu_k g}.$$

Integrating velocity with respect to time provides the position:

$$x(t) = v_0 t - \frac{1}{2} \mu_k g t^2.$$

Substituting $t_{\text{stop}}$ into $x(t)$ yields the stopping distance:

$$d_{\text{stop}} = \frac{v_0^2}{2 \mu_k g}.$$

This expression is consistent with the work-energy interpretation in which initial kinetic energy is dissipated by the work done by friction.

## 5. Example Scenarios

### Scenario A: High-Speed Stop on Dry Asphalt
- $v_0 = 25\,\text{m/s}$
- $\mu_k = 0.8$

**Stopping time**
$$t_{\text{stop}} = \frac{25}{0.8 \times 9.81} \approx 3.18\,\text{s}$$

**Stopping distance**
$$d_{\text{stop}} = \frac{25^2}{2 \times 0.8 \times 9.81} \approx 39.82\,\text{m}$$

### Scenario B: Moderate-Speed Stop on Wet Asphalt
- $v_0 = 15\,\text{m/s}$
- $\mu_k = 0.45$

**Stopping time**
$$t_{\text{stop}} = \frac{15}{0.45 \times 9.81} \approx 3.40\,\text{s}$$

**Stopping distance**
$$d_{\text{stop}} = \frac{15^2}{2 \times 0.45 \times 9.81} \approx 25.48\,\text{m}$$

## 6. Discussion
- The model predicts constant deceleration that depends only on $\mu_k$ and $g$, making it mass-independent.
- Stopping distance scales with the square of initial speed, illustrating why modest increases in velocity dramatically increase braking distance.
- Lower friction coefficients—such as those encountered on wet roads—significantly extend stopping distance and can even yield longer stopping times despite reduced initial speeds.
- Real-world analyses should add reaction time, brake fade, aerodynamic drag, and road gradient to refine predictions.

## 7. References
- Classical mechanics textbooks covering Newtonian dynamics and friction models.
- Standard vehicle dynamics references for braking analysis.
