from pathlib import Path
import fastf1

#cache data instead of downloading it every time
Path("cache").mkdir(exist_ok=True)
fastf1.Cache.enable_cache("cache") #param is relative path to cache folder

session = fastf1.get_session(2025, "Suzuka", "Q")
session.load()

#I want to see verstappen's pole lap!!!
lap = session.laps.pick_driver("VER").pick_fastest()

print("Driver:", lap["Driver"])
print("Lap Time:", lap["LapTime"])