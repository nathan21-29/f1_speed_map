import os
os.environ["OPENBLAS_NUM_THREADS"] = "1"

import math
from pathlib import Path
import fastf1
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.colors import Normalize
from matplotlib.animation import FuncAnimation
from datetime import datetime
from f1_utils import get_current_season, get_sessions, floor_in_sorted

#cache data instead of downloading it every time
Path("cache").mkdir(exist_ok=True)
fastf1.Cache.enable_cache("cache") #param is relative path to cache folder

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
    
    if year >- 2018 and year <= get_current_season():
        break

#get round input
print(f"Quali sessions in {year}")
get_sessions(year) #print the sessions
print("Please input the round number of the desired session: ")

session = fastf1.get_session(2025, "random", "Q")
session.load()

#I want to see verstappen's pole lap!!!
lap = session.laps.pick_driver("VER").pick_fastest()

if lap is not None:
    print("Driver:", lap["Driver"])
    print("Lap Time:", lap["LapTime"])
    #Lets get the data
    telemetry = lap.get_telemetry()
    
    #sample data
    print(telemetry.columns.tolist())
    print(telemetry[["Time", "X", "Y", "Speed", "Brake"]].head())

    fig, ax = plt.subplots()
    # Color each track segment by its speed.
    xy = telemetry[["X", "Y"]].to_numpy()
    segments = list(zip(xy[:-1], xy[1:]))
    speeds = telemetry["Speed"].to_numpy()[:-1]
    braking = telemetry["Brake"].to_numpy()[:-1]
    times = telemetry["Time"].tolist()[:-1] #starting time for each segment
    points = LineCollection(
        segments,
        cmap="plasma",
        norm=Normalize(vmin=speeds.min(), vmax=speeds.max()),
        linewidth=3,
        zorder=1
    )
    points.set_array(speeds)
    
    braking_segments = [segments[i] for i in range(len(segments)) if braking[i]]
    braking_points = LineCollection(
        braking_segments,
        color="cyan",
        alpha=0.3,
        linewidth = 8,
        zorder = 2
    )
    
    ax.add_collection(points)
    ax.add_collection(braking_points)
    ax.autoscale()
    fig.colorbar(points, ax=ax, label="Speed (km/h)")
        
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
