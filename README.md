# Fruit Ninja with Your Hands

A webcam version of Fruit Ninja: swipe your index finger through the air to slice fruit flying across the screen.

Built with Python, OpenCV and MediaPipe.

## How to play

- Fruit launches from the bottom of the screen. Swipe your index finger through it **quickly** to slice it.
- Both hands work, and each one leaves its own blade trail.
- Each fruit you slice is worth 1 point.
- Let 3 fruits fall without slicing them and it's game over.

## Features

- Real-time tracking of both index fingertips with MediaPipe Hands
- Glowing blade trail that tapers behind your finger
- Swipe detection that only counts fast movements, so resting your finger on a fruit doesn't slice it
- Fruit splits into two halves along the direction of your swipe
- Juice splatter that matches each fruit's colour
- Five fruit types (orange, apple, watermelon, lime and plum), each with its own colour and size

## How it works

1. **Hand tracking:** each webcam frame is mirrored and passed to MediaPipe, which finds landmark 8 (the index fingertip) on each hand.
2. **Blade trail:** the last 8 fingertip positions for each hand are kept in a `deque` and drawn as a line that gets thicker toward the newest point.
3. **Physics:** each fruit has a position and velocity. Gravity is added to its vertical speed every frame, which makes it arc up and fall back down.
4. **Slice detection:** each frame, the most recent piece of the trail is treated as a line segment. If the finger moved fast enough and the segment passes within a fruit's radius of its center (point-to-segment distance), the fruit is sliced.
5. **Splitting:** the swipe angle is calculated with `atan2`. The two halves are drawn as half circles rotated to match it and pushed apart perpendicular to the cut.

## Setup

Requires **Python 3.12** (newer versions don't work with this version of MediaPipe).

```bash
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Run it

```bash
python fruit_ninja.py
```

## Controls

- **R** restarts after game over
- **Q** quits

Click the game window first so it receives the key presses.

## Mac permissions

In System Settings → Privacy & Security → **Camera**, give access to the app you're running it from (e.g. VS Code or Terminal), then restart that app.

## Tuning

At the top of `fruit_ninja.py`:

- `SLICE_SPEED` controls how fast your finger must move to slice. Lower it to make slicing easier.
- `GRAVITY` controls how fast fruit falls. Lower it for floatier fruit.