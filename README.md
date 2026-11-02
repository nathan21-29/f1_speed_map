# F1 Speed Map

Visualize and compare Formula 1 qualifying laps using an animated track map.

## Features

- Track heatmap showing speed and highlighted braking zones.
- Animated cars with driver labels and live speed readings.
- Compare the fastest qualifying laps of drivers in the top 10.
- Time delta display when comparing exactly two drivers.
- Local data caching to speed up repeat sessions.

## Setup and usage

Requires Python 3.12 or newer, as well as an internet connection / F1 account to access FastF1 data.

```sh
python -m pip install -r requirements.txt
python main.py
```

Follow the prompts to select a season (2018 onward), a completed qualifying session, and drivers. Enter driver positions separated by spaces, such as `1 2`, to compare their laps. The visualization opens in a separate window.

## Libraries used

- **FastF1** — F1 session data, telemetry, and team colors.
- **NumPy** — numerical calculations and interpolation.
- **pandas** — tabular data and time handling.
- **Matplotlib** — track plotting and animation.

## Screenshots

<img width="1059" height="1013" alt="image" src="https://github.com/user-attachments/assets/a4e55700-6165-4629-b61a-898ef80adcf4" />
<img width="1500" height="1462" alt="image" src="https://github.com/user-attachments/assets/ef153f90-e81d-4e64-8857-a61962e007a9" />
