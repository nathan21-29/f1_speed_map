# Continue here: animate the selected drivers

This guide starts from the code in `main.py` and `f1_utils.py` as of October 31, 2026. Work through one step at a time. The goal is to draw the track once, create one dot per selected driver, and move all those dots using one shared clock.

## Where you left off

You already have:

- Session loading and driver selection.
- The corrected selection index: `drivers["Name"].iloc[n - 1]`.
- A `load_lap_data()` helper that stores a driver abbreviation and telemetry data.
- A track heatmap and braking zones drawn from a reference lap.
- An animation that still moves only one dot.
- The `numpy` and `perf_counter` imports in `main.py`.

The remaining work is mainly connecting the prepared data to multiple dots. You do not need JSON files or a new storage system for this.

## 1. Finish preparing the telemetry

In `f1_utils.py`, replace `load_lap_data()` with:

```python
def load_lap_data(lap_data, lap):
    if lap is None:
        return

    telemetry = lap.get_telemetry()
    data = {
        "xy": telemetry[["X", "Y"]].to_numpy(),
        "speeds": telemetry["Speed"].to_numpy(),
        "times": telemetry["Time"].dt.total_seconds().to_numpy(),
        "color": fastf1.plotting.get_team_color(
            lap["Team"], lap.session
        ),
    }

    lap_data.append((lap["Driver"], data))
```

Keep the existing `import fastf1.plotting` at the top of that file.

Why these changes matter:

- `times` becomes numeric seconds, which makes interpolation straightforward.
- `xy`, `speeds`, and `times` must all have the same number of samples. Remove `[:-1]` from the animation data.
- Keep each driver's own timestamps. Drivers can have different numbers of telemetry samples.
- `Time` is relative to the lap; do not use the session's absolute clock for comparing these laps.

The structure remains a list of pairs:

```text
lap_data
    (driver abbreviation, dictionary of telemetry arrays and color)
    (driver abbreviation, dictionary of telemetry arrays and color)
    ...
```

For example, `for driver, data in lap_data:` unpacks each pair into two variables.

**Checkpoint:** after driver selection, temporarily print:

```python
for driver, data in lap_data:
    print(
        driver,
        len(data["xy"]),
        len(data["speeds"]),
        len(data["times"]),
        data["color"],
    )
```

Each driver's three lengths should match, and each selected driver should appear once.

## 2. Only keep valid selected laps

In the driver selection loop in `main.py`, replace the lines that obtain and append `curr_lap` with:

```python
curr_lap = session.laps.pick_drivers(
    drivers["Name"].iloc[n - 1]
).pick_fastest()

if curr_lap is None:
    print("No valid lap was found for that driver.")
    continue

laps.append(curr_lap)
load_lap_data(lap_data, curr_lap)
```

Keep this inside the existing valid-position branch. Keep `laps = list()` and `lap_data = list()` before the input loop.

To prevent duplicate dots when someone enters the same number twice, change:

```python
for n in sorted([int(n) for n in re.findall(r"\d+", input())]):
```

to:

```python
for n in sorted({int(n) for n in re.findall(r"\d+", input())}):
```

The set removes duplicates before sorting.

## 3. Keep the track drawing code

Keep your code from `reference_lap = laps[0]` through `plt.gca().set_axis_off()`.

That code draws the shared background: the speed heatmap, braking zones, and start/finish marker. It only needs one reference lap.

The `[:-1]` slices in this **track drawing block** are still appropriate: a path with N points has N - 1 segments. This is separate from the full sample arrays used to move the cars.

Your current reference is the first selected valid lap. It is only the pole lap if that selected driver and lap actually correspond to pole. Its speed colors describe that reference driver's lap.

## 4. Create a dot and label for each driver

In `main.py`, find `#draw running point`.

Delete the old code from that comment through the end of the existing `FuncAnimation(...)` call. Leave the axis formatting and `plt.show()` below it.

Insert the following code at the same indentation level as the old `start_time` line, inside `if reference_lap is not None:`:

```python
# Create each driver's plot objects once.
cars = []

for driver, data in lap_data:
    x, y = data["xy"][0]

    dot, = ax.plot(
        [x], [y],
        marker="o",
        linestyle="None",
        color=data["color"],
        zorder=10,
    )
    label = ax.text(x + 100, y, driver, zorder=11)

    cars.append((driver, data, dot, label))

# Everyone shares one playback clock and restarts together.
duration = max(data["times"][-1] for _, data in lap_data)
start_time = perf_counter()
```

`ax.plot()` creates the dot. `ax.text()` creates its label. Store these objects so you can move them later instead of creating more dots every frame.

The comma in `dot, = ax.plot(...)` unpacks the one line object returned inside Matplotlib's list.

At this stage, you can run the program to check that the dots and labels appear. They may overlap at the start because the cars begin at roughly the same location.

## 5. Move every car inside one update function

Immediately after the code from step 4, insert:

```python
def update(frame):
    elapsed = (perf_counter() - start_time) % duration
    artists = []

    for driver, data, dot, label in cars:
        times = data["times"]

        x = np.interp(elapsed, times, data["xy"][:, 0])
        y = np.interp(elapsed, times, data["xy"][:, 1])
        speed = np.interp(elapsed, times, data["speeds"])

        dot.set_data([x], [y])
        label.set_position((x + 100, y))
        label.set_text(f"{driver}: {speed:.0f} km/h")

        artists.extend([dot, label])

    return artists


animation = FuncAnimation(
    fig,
    update,
    interval=20,
    blit=True,
    cache_frame_data=False,
)
```

Keep both imports already present in `main.py`:

```python
import numpy as np
from time import perf_counter
```

### What interpolation does

Suppose a driver has these two samples:

| Time | X |
| --- | --- |
| 1.0 seconds | 100 |
| 1.2 seconds | 120 |

At 1.1 seconds, `np.interp()` gives X = 110. It finds the surrounding samples and estimates a position between them. That replaces the manual search and `dt`, `dx`, and `dy` calculations in your old update function.

`data["xy"][:, 0]` means all X coordinates; `[:, 1]` means all Y coordinates.

### Why there is one clock

Calculate `elapsed` once outside the loop so every driver is shown at the same elapsed lap time. Do not wrap time separately using each driver's lap duration: faster drivers would restart while slower drivers were still finishing.

Here, a car stays at its last telemetry position after its samples end because `np.interp()` clamps to the final value. All cars restart when the longest telemetry timeline ends. This uses telemetry endpoints, which can differ slightly from official recorded lap times.

`interval=20` requests an update about every 20 milliseconds. Actual playback progress comes from `perf_counter()`, so a delayed frame does not slow the playback clock.

### Why return artists

With `blit=True`, Matplotlib needs the objects that changed. `artists` contains every updated dot and label. Keep the `animation` variable so the animation object stays alive.

## 6. Try it in small steps

Run from the project directory in PowerShell:

```powershell
.\.venv\Scripts\python.exe main.py
```

Use a completed session with available telemetry, then check:

- [ ] One selected driver moves around the track with a speed label.
- [ ] Two selected drivers each have a dot and abbreviation.
- [ ] Different teams use their respective colors.
- [ ] A faster car waits near the finish while the other completes its lap.
- [ ] All cars restart together.
- [ ] Selecting position 10 works without an indexing error.

Teammates share a team color. Their abbreviations distinguish them for now; different markers can come later.

If you get an error about array lengths, revisit step 1 and check that all animation arrays retain their final sample. If only one dot moves, check that `set_data()` is inside the `for ... in cars` loop. Labels can overlap when cars are close; that does not mean data is missing.

## 7. Clean up after the animation works

These changes can wait until the moving dots work:

- Remove the unused `datetime` import and `floor_in_sorted` import from `main.py` if nothing else uses them.
- Remove the unfinished `draw_cars()` helper in `f1_utils.py`, or implement it later. Currently it treats `(driver, data)` tuples as Lap objects, so calling it would fail. The loop in step 4 already creates the cars.
- Remove the old `times = telemetry["Time"].tolist()[:-1]` line in the track block if it is no longer used.
- In the year and round input handlers, change `except TypeError:` to `except ValueError:` so nonnumeric input is caught correctly.
- Remove temporary debug prints after checking the data.

## Later: add braking indicators

Once multiple cars move correctly, you can add this entry to the data dictionary in `load_lap_data()`:

```python
"braking": telemetry["Brake"].to_numpy(),
```

Inside the update loop, find the latest sample at or before the playback time:

```python
sample = np.searchsorted(times, elapsed, side="right") - 1
sample = int(np.clip(sample, 0, len(times) - 1))
is_braking = bool(data["braking"][sample])

label.set_text(
    f"{driver}: {speed:.0f} km/h"
    + (" BRAKE" if is_braking else "")
)
```

Replace the earlier `label.set_text(...)` line with this version. Braking is a boolean state, so use a sample lookup rather than interpolating between true and false. This keeps the dot's team color visible.

## Your first task when you return

Start with **step 1 only**: finish `load_lap_data()` and print the array lengths. Once the data matches, move on to creating the dots. There is no need to solve every part at once.
