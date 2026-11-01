import os
os.environ["OPENBLAS_NUM_THREADS"] = "1"

import re
import random
from pathlib import Path
import fastf1
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.colors import Normalize
from matplotlib.animation import FuncAnimation
from datetime import datetime
from time import perf_counter
from f1_utils import get_current_season, get_sessions, list_drivers, load_lap_data, floor_in_sorted

#cache data instead of downloading it every time
Path("cache").mkdir(exist_ok=True)
fastf1.Cache.configure(cache_dir="cache") #param is relative path to cache folder

#select session
print("###################")
print("# F1 Quali Viewer #")
print("###################\n")

year = -1
track = str()
#get year input
while True:
    while True:
        try:
            year = int(input(f"Enter a season (2018 - {get_current_season()}): "))
        except TypeError:
            print(f"Please enter a valid integer from 2018 to {get_current_season()}!")
        else:
            break
    
    if year >= 2018 and year <= get_current_season():
        break
    else:
        print(f"Please enter a valid integer from 2018 to {get_current_season()}!")

#get round input
print(f"Quali sessions in {year}")
season_length = int(get_sessions(year)) #print the sessions
while True:
    while True:
        try:
            round_number = int(input("Please input the round number of the desired session: "))
        except TypeError:
            print(f"Please enter a valid integer from 1 to {season_length}!")
        else:
            break
        
    if round_number >= 1 and round_number <= season_length:
        break
    else:
        print(f"Please enter a valid integer from 1 to {season_length}!")

session = fastf1.get_session(year, round_number, "Q")
session.load()

#get driver selection
drivers = list_drivers(session)

laps = list()
lap_data = list()
while(True):
    print("Please enter the positions of the car(s) you would like to see separated by a space.")
    n1 = random.randint(0, 8)
    n2 = random.randint(n1 + 1, 9)
    #add one at the end because indexing is from zero but numbering is from one
    print(f"(e.g. to see {drivers["Name"].iloc[n1]} vs {drivers["Name"].iloc[n2]} then enter \"{n1 + 1} {n2 + 1}\")")
    for n in sorted({int(n) for n in re.findall(r"\d+", input())}): #for every number in the input
        if(n > 0 and n <= 10):
            curr_lap = session.laps.pick_drivers(drivers["Name"].iloc[n - 1]).pick_fastest() #add the lap
            if curr_lap is None:
                print(f"No valid lap was found for {drivers["Name"].iloc[n - 1]}")
                continue
            
            laps.append(curr_lap)
            load_lap_data(lap_data, curr_lap)
        else:
            print(f"{n} was not a valid number; lap was not added.")
    
    if len(laps) > 0:
        break
    
#lap_data = load_lap_data(laps)
#I want to see verstappen's pole lap!!!
reference_lap = laps[0] #use pole lap as reference for heatmap and brake zones

if reference_lap is not None:
    # print("Driver:", lap["Driver"])
    # print("Lap Time:", lap["LapTime"])
    #Lets get the data
    telemetry = reference_lap.get_telemetry()
    
    #sample data
    # print(telemetry.columns.tolist())
    # print(telemetry[["Time", "X", "Y", "Speed", "Brake"]].head())

    fig, ax = plt.subplots()
    # Color each track segment by its speed.
    xy = telemetry[["X", "Y"]].to_numpy()
    segments = list(zip(xy[:-1], xy[1:]))
    speeds = telemetry["Speed"].to_numpy()[:-1]
    braking = telemetry["Brake"].to_numpy()[:-1]
    times = telemetry["Time"].tolist()[:-1] #starting time for each segment
    car_path = LineCollection(
        segments,
        cmap="plasma",
        norm=Normalize(vmin=speeds.min(), vmax=speeds.max()),
        linewidth=3,
        zorder=1
    )
    car_path.set_array(speeds)
    
    braking_segments = [segments[i] for i in range(len(segments)) if braking[i]]
    braking_zones = LineCollection(
        braking_segments,
        color="cyan",
        alpha=0.3,
        linewidth = 8,
        zorder = 2
    )
    
    ax.add_collection(car_path)
    ax.add_collection(braking_zones)
    ax.autoscale()
    xmin, xmax = ax.get_xlim()
    ax.set_xlim(xmin, xmax + (xmin + xmax) * 0.15)
    fig.colorbar(car_path, ax=ax, label="Speed (km/h)", pad=0.1)
        
    ax.scatter(xy[0][0], xy[0][1], color="cyan", zorder=10) #plot start/finish line
    ax.text(xy[0][0] + 100, xy[0][1], "Start/Finish Line")
    plt.gca().set_axis_off()
    
    #make a list of all car dot objects
    cars = list()
    for driver, data in lap_data:
        x, y = data["xy"][0]
        
        dot, = ax.plot(
            [x], [y],
            marker="o",
            linestyle="None",
            color=data["color"],
            zorder=10,
        )
        label = ax.text(x + 100, y, driver, zorder=11, clip_on=True)
        
        cars.append((driver, data, dot, label))
    
    #delta data
    if len(lap_data) == 2: #if 1v1
        delta_label = ax.text(
            0.02, 0.98, 
            f"{lap_data[1][0]} delta to {lap_data[0][0]}: ", 
            transform=ax.transAxes,
            va="top",
            fontsize="large",
        )
        
    #duration is the largest 'last-time' point among the cars
    duration = max(data["times"][-1] for _, data in lap_data)
    start_time = perf_counter()
    
    def update(frame):
        elapsed = (perf_counter() - start_time) % duration
        elements = list()
        
        for driver, data, dot, label in cars:
            times = data["times"]
            
            x = np.interp(elapsed, times, data["xy"][:, 0])
            y = np.interp(elapsed, times, data["xy"][:, 1])
            speed = np.interp(elapsed, times, data["speeds"])
            
            dot.set_data([x], [y])
            label.set_position((x + 100, y))
            label.set_text(f"{driver}: {speed:.0f} km/h")
            
            elements.extend([dot, label])
            
        if len(lap_data) == 2:
            #distance covered by pole car
            distance = np.interp(
                elapsed, 
                lap_data[0][1]["times"],
                lap_data[0][1]["distance"]
            )
            #find the diff in times taken for both cars to reach distance
            ref_time = np.interp(
                distance,
                lap_data[0][1]["distance"],
                lap_data[0][1]["times"]
            )
            other_time = np.interp(
                distance,
                lap_data[1][1]["distance"],
                lap_data[1][1]["times"],
                left = np.nan, right = np.nan #don't allow extrapolation
            )
            
            delta = other_time - ref_time
            value = f"{delta:+.3f}s" if np.isfinite(delta) else "--"
            delta_label.set_text(
                f"{lap_data[1][0]} delta to {lap_data[0][0]}: {value}"
            )
            elements.append(delta_label)
            
        return elements
    
    animation = FuncAnimation(fig, update, interval=20, blit=False, cache_frame_data=False)
    
        
    ax.set_aspect("equal", adjustable="box")
    manager = plt.get_current_fig_manager()
    if manager is not None:
        manager.window.state("zoomed") #type: ignore
    fig.patch.set_facecolor("#A0A0A0")
    #title data
    plt.title(f"{year} {session.event["EventName"]} - {session.name}")
    plt.show()