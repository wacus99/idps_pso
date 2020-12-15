import numpy as np
from scipy import integrate
import random
import copy
from typing import *


class Solver:

    def __init__(self, num_swarm: int, num_iterations: int, locations: List
                 , resturant_location: List, petrol_locations: List):
        self.num_swarm = num_swarm
        self.num_iterations = num_iterations
        self.locations = locations
        self.resturant_location = resturant_location
        self.speed = []
        self.fuel = 2.5
        self.fuel_cons_per_100km = 9
        self.petrol_locations = petrol_locations
        self.gBest = []
        self.gBest_cost = 0

    def swap(self, lst, n, m):
        buff = lst[n-1]
        lst[n-1] = lst[m-1]
        lst[m-1] = buff
        return lst

    def diff(self, a, b):
        list_of_diff = []
        b_buff = b[:]
        if len(a) != len(b):
            print("Blad! Różne długości tablic")
            return -1
        for i in range(len(a)-1):
            if a == b_buff:
                break
            else:
                if a[i] != b_buff[i]:
                    ind = b_buff.index(a[i])
                    if ind == -1:
                        return -1
                    list_of_diff.append([i+1, ind])
                    self.swap(b_buff, i+1, ind)
        return list_of_diff

    def generate_speed(self, t):
        time = []
        speed = []
        vel = 60*1000/3600          # m/s
        time = np.linspace(0, t, t*10)
        speed = np.abs(np.sin(0.5*time))*vel

        return speed, time

    def calculate_time(self, route):
        speed, time = self.generate_speed(int(route*100))
        pos = integrate.cumtrapz(speed, time, initial=0)
        t = np.interp(route, pos, time)

        return t

    def route_between_points(self, point1, point2):
        route = np.sqrt(np.power(point1[0] - point2[0], 2) + np.power(point1[1] - point2[1], 2))
        return route

    def calculate_part_cost(self, part, lst_of_points, petrol_locations = []):
        route = 0
        for i in range(len(part)):
            if i == 0:
                if part[i] < 10:
                    route += self.route_between_points(lst_of_points[part[i]-1], self.resturant_location)
                else:
                    route += self.route_between_points(petrol_locations[part[i] - 10], self.resturant_location)

            if i == len(part) - 1:
                if part[i] < 10:
                    route += self.route_between_points(lst_of_points[part[i]-1], self.resturant_location)
                else:
                    route += self.route_between_points(petrol_locations[part[i] - 10], self.resturant_location)
            else:
                if part[i] < 10:
                    if part[i+1] >= 10:
                        route += self.route_between_points(lst_of_points[part[i] - 1], petrol_locations[part[i + 1] - 10])
                    else:
                        route += self.route_between_points(lst_of_points[part[i]-1], lst_of_points[part[i+1]-1])
                else:
                    route += self.route_between_points(petrol_locations[part[i] - 10], lst_of_points[part[i + 1] - 1])
        return route

    def calculate_full_cost(self, lst_of_part, lst_of_points):
        lst_of_cost = []
        for i in range(len(lst_of_part)):
            cal = self.calculate_part_cost(lst_of_part[i], lst_of_points)
            lst_of_cost.append(cal)
        return lst_of_cost

    def check_diff(self, diff, dict):
        check = False
        if diff:
            for p1 in range(len(diff)):  # Dodawanie powyższych predkosci do predkosci wcześniejszej
                for c1 in range(len(dict)):  # Wedlug wzoru: v(i+1) = v(i) + [x(i) - pBest] + [x(i) - g Best]
                    check = False
                    if dict[c1]:
                        if dict[c1][0] == diff[p1][0] and dict[c1][1] == diff[p1][1]:
                            dict[c1].clear()  # Sprawdzanie powtorzenia dla diff 1
                            check = True
                        elif dict[c1][0] == diff[p1][1] and dict[c1][1] == diff[p1][0]:
                            dict[c1].clear()
                            check = True
                if not check:
                    dict.append(diff[p1])

    def is_fuel_enough(self, particle):
        if particle:
            particle_cost = self.calculate_part_cost(particle, self.locations)
            fuel_need = particle_cost / 100 * self.fuel_cons_per_100km

            route = particle
            if fuel_need + 2 < self.fuel:
                return len(particle)

            del route[-1]
            return self.is_fuel_enough(route)
        else:
            return 0

    def count_time(self):
        delivery_time = []
        route = 0
        time = 0
        for i in range(len(self.gBest)):
            if i == 0:
                if self.gBest[i] < 10:
                    route += 1000 * self.route_between_points(self.resturant_location, self.locations[self.gBest[i] - 1])
                else:
                    route += 1000 * self.route_between_points(self.resturant_location, self.petrol_locations[self.gBest[i] - 10])
                time = self.calculate_time(route)
                delivery_time.append(time/60)
            else:
                if self.gBest[i] >= 10:
                    route += 1000 * self.route_between_points(self.locations[self.gBest[i-1] - 1], self.petrol_locations[self.gBest[i] - 10])
                elif self.gBest[i-1] >= 10:
                    route += 1000 * self.route_between_points(self.petrol_locations[self.gBest[i - 1] - 10], self.locations[self.gBest[i] - 1])
                else:
                    route += 1000 * self.route_between_points(self.locations[self.gBest[i - 1] - 1], self.locations[self.gBest[i] - 1])

                time = self.calculate_time(route)
                delivery_time.append(time/60)

        return delivery_time


    def solve(self):
        list_of_particle = []
        dict_of_vel = {}
        list_of_pBest = []

        l = len(self.locations)

        self.gBest = 0

        for i in range(self.num_swarm):                                     #   Losowanie stada i predkosci
            list_of_particle.append(random.sample(range(1, l+1), k=l))
            dict_of_vel[i] = [(random.sample(range(1, l+1), k=2))]

        list_of_pBest = copy.deepcopy(list_of_particle)                     #   Obliczanie kosztu dla wylosowanego stada
        lst_of_pBest_cost = self.calculate_full_cost(
            list_of_pBest, self.locations)
        self.gBest_cost = min(lst_of_pBest_cost)
        index_gBest = lst_of_pBest_cost.index(self.gBest_cost)
        self.gBest = list_of_pBest[index_gBest]

        for i in range(self.num_iterations):
            for it in range(self.num_swarm):
                diff1 = self.diff(list_of_particle[it], list_of_pBest[it])  #   Wyznaczanie różnic: cząsteczka - pBest [x(i) - pBest]
                diff2 = self.diff(list_of_particle[it], self.gBest)         #                       cząsteczka - gBest [x(i) - gBest]
                self.check_diff(diff1, dict_of_vel[it])
                self.check_diff(diff2, dict_of_vel[it])
                for el in range(len(dict_of_vel[it])):
                    if dict_of_vel[it][el]:                         #   Zastosowanie predkosci dla stada
                        list_of_particle[it] = self.swap(
                                            list_of_particle[it], dict_of_vel[it][el][0], dict_of_vel[it][el][1])
            costs = self.calculate_full_cost(list_of_particle, self.locations)
            for it in range(self.num_swarm):                        #   Aktualizowanie pBest oraz gBest
                if costs[it] < lst_of_pBest_cost[it]:
                    list_of_pBest[it] = list_of_particle[it]
                    lst_of_pBest_cost[it] = costs[it]
                if costs[it] < self.gBest_cost:
                    self.gBest = list_of_particle[it]

        fuel_enough = self.is_fuel_enough(copy.copy(self.gBest))

        if fuel_enough < len(self.gBest):
            best = []
            current_cost = np.inf
            for i in range(fuel_enough + 1):
                for p in range(len(self.petrol_locations)):
                    route = copy.copy(self.gBest)
                    route.insert(i, p+10)
                    cost = self.calculate_part_cost(route, self.locations, self.petrol_locations)
                    if current_cost == np.inf or cost < current_cost:
                        current_cost = cost
                        best = route
            self.gBest = best
            self.gBest_cost = current_cost



        del_time = self.count_time()
        print(del_time)




