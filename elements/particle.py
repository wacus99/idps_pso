import numpy as np
import random


class Particle:
    def __init__(self, area_radius):
        self.position = np.array([
            random.randint((-1)*area_radius, area_radius),
            random.randint((-1)*area_radius, area_radius),
        ])
        self.pbest_position = self.position
        self.pbest_value = float('inf')
        self.velocity = np.array([0, 0])

    def move(self):
        self.position += self.velocity
