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
    fig.colorbar(car_path, ax=ax, label="Speed (km/h)")
        
    ax.scatter(xy[0][0], xy[0][1], color="cyan", zorder=10) #plot start/finish line
    ax.text(xy[0][0] + 100, xy[0][1], "Start/Finish Line")
    plt.gca().set_axis_off()
    
    #draw running point
    start_time = datetime.now()
    dot, = ax.plot([xy[0][0]], [xy[0][1]], "ro")
    speed_label = ax.text(xy[0][0], xy[0][1], f"{speeds[0]}")
    
    def update(frame):
        elapsed_time = (datetime.now() - start_time) % times[-1]
        reference = floor_in_sorted(times, elapsed_time)
        dt = float()
        dx = float()
        dy = float()
        if reference is not None:
            comparison = reference + 1 if reference < len(segments) - 1 else 0
            dt = float((elapsed_time - times[reference]) / (times[comparison] - times[reference])) #gives the progress of the current segment, should be 0 -> 1
            dx = (xy[comparison][0] - xy[reference][0]) * dt
            dy = (xy[comparison][1] - xy[reference][1]) * dt
            dv = (speeds[comparison] - speeds[reference]) * dt
        dot.set_data([xy[reference][0] + dx], [xy[reference][1] + dy])
        if(braking[reference]):
           dot.set_color("red") 
        else:
            dot.set_color("green")
        speed_label.set_text(f"{round(speeds[comparison] + dv, 1)}km/h") #type: ignore
        speed_label.set_position((xy[reference][0] + dx + 100, xy[reference][1] + dy))
        return dot, speed_label
        
    animation = FuncAnimation(
        fig,
        update,
        frames=len(xy),
        interval=10,
        blit=True
    )
    
    ax.set_aspect("equal", adjustable="box")
    manager = plt.get_current_fig_manager()
    if manager is not None:
        manager.window.state("zoomed") #type: ignore
    fig.patch.set_facecolor("#A0A0A0")
    plt.show()
