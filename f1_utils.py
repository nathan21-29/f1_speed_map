import fastf1
import fastf1.plotting
import pandas as pd
from datetime import datetime, timezone

def get_current_season():
    now = pd.Timestamp.now(tz="UTC")
    curr_year = now.year
    
    schedule = fastf1.get_event_schedule(curr_year, include_testing=False)
    season_start = pd.to_datetime(schedule["Session1DateUtc"], utc=True)
    
    if(season_start > now).all(): #season hasn't started yet
        return (curr_year - 1)
    else:
        return curr_year
    
def get_sessions(year: int):
    now = pd.Timestamp.now(tz="UTC")
    
    schedule = fastf1.get_event_schedule(year, include_testing=False)
    quali_sessions = pd.to_datetime(schedule["Session4DateUtc"], utc=True)
    occurred = schedule.loc[quali_sessions <= now]
    print("Round Number\tEvent Name")
    print(occurred[["RoundNumber", "EventName"]].to_string(index=False, header=False))
    
    return len(occurred[["RoundNumber"]])

def list_drivers(session):
    drivers = session.results[["Position", "Abbreviation", "FullName", "TeamName", "Q3"]].copy()
    drivers = drivers[:10] #only show q3 drivers
    drivers["Position"] = drivers["Position"].astype("Int64") #cast position to int
    drivers = drivers.rename(columns={
        "Position": "Pos",
        "Abbreviation": "Name",
        "FullName": "Full Name",
        "Team Name": "Team Name",
        "Q3": "Q3 Time"
    })
    
    def format_time(time: pd.Timedelta):
        if pd.isna(time):
            return "-"
        milliseconds = time // pd.Timedelta(milliseconds=1)
        minutes = milliseconds // 60000
        milliseconds %= 60000
        seconds = milliseconds // 1000
        milliseconds %= 1000
        return f"{seconds:2}:{milliseconds:03}" if minutes <= 0 else f"{minutes}:{seconds:02}:{milliseconds:03}"
    
    pole_time = drivers["Q3 Time"].iloc[0]
    formatted = [format_time(pole_time)]
    
    for time in drivers["Q3 Time"].iloc[1:]:
        delta = time - pole_time
        formatted.append("-" if pd.isna(delta) else f"+{format_time(delta)}")
        
    drivers["Q3 Time"] = formatted
    
    print(drivers.to_string(index=False))
    return drivers

def load_lap_data(lap_data, lap):
    if lap is not None:
        telemetry = lap.get_telemetry()
        data = {
            "xy": telemetry[["X", "Y"]].to_numpy(),
            "speeds": telemetry["Speed"].to_numpy(),
            "times": telemetry["Time"].dt.total_seconds().to_numpy(),
            "color": fastf1.plotting.get_team_color(
                lap["Team"], lap.session
            ),
        }
        
        lap_data.append((lap["Driver"], data,))
    return

def draw_cars(lap_data):
    for lap in lap_data:
        telemetry = lap.get_telemetry()
    return

def floor_in_sorted(arr, target):
    left, right = 0, len(arr) - 1
    answer = None

    while left <= right:
        mid = (left + right) // 2

        if arr[mid] < target:
            answer = mid
            left = mid + 1      # look for a larger value still below target
        else:
            right = mid - 1

    return answer