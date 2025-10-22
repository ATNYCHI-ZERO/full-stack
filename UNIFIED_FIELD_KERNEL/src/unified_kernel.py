# Unified Field Kernel (simplified)
import numpy as np
from numpy.random import normal
from scipy.ndimage import gaussian_filter


def einstein_langevin(R, rho, dt, kappa=8*np.pi, noise_amp=1e-3):
    noise = normal(0, noise_amp, R.shape)
    dR = kappa * (rho - R) + noise
    return R + dR * dt


def evolve(n_steps=1000, grid=128, dt=1e-3):
    R = np.zeros((grid, grid))
    rho = gaussian_filter(normal(0, 1, (grid, grid)), 2)
    for _ in range(n_steps):
        R = einstein_langevin(R, rho, dt)
    return R


if __name__ == "__main__":
    R = evolve()
    np.save("data/curvature.npy", R)
    print("Simulation complete. Curvature field saved.")
