import fastf1
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
    print(len(occurred[["RoundNumber"]]))
    
    return len(occurred[["RoundNumber"]])
    

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