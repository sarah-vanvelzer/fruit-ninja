import cv2
import mediapipe as mp
from collections import deque
import random
import time
import math

cap = cv2.VideoCapture(0)

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.6)
trails = {}

GRAVITY = 0.6
SLICE_SPEED = 25
fruits = []
halves = []
particles = []
score = 0
lives = 3
game_over = False
next_spawn = time.time()

FRUITS = [
    # (outside colour, inside colour, radius) in BGR
    ((0, 140, 255), (100, 200, 255), 50), # orange
    ((40, 40, 210), (190, 235, 245), 45), # apple
    ((60, 140, 40), (80, 60, 235), 65), # watermelon
    ((40, 200, 120), (150, 245, 190), 40), # lime
    ((120, 40, 110), (120, 150, 230), 42), # plum
]

def make_fruit(w, h):
    colour, inner, r = random.choice(FRUITS)
    return {
        "x": random.randint(int(w * 0.2), int(w * 0.8)),
        "y": h + 50,
        "vx": random.uniform(-4, 4),
        "vy": random.uniform(-30, -24),
        "sliced": False,
        "colour": colour,
        "inner": inner,
        "r": r,
    }

# px & py = fruit centre, the line goes from a-coordinates to b-coordinates
def dist_to_segment(px, py, ax, ay, bx, by):
    dx = bx - ax
    dy = by - ay
    length_sq = dx * dx + dy * dy
    # Finger didn't move at all
    if length_sq == 0:
        return ((px - ax) ** 2 + (py - ay) ** 2) ** 0.5
    t = ((px - ax) * dx + (py - ay) * dy) / length_sq
    t = max(0, min(1, t))
    closest_x = ax + t * dx
    closest_y = ay + t * dy
    return ((px - closest_x) ** 2 + (py - closest_y) ** 2) ** 0.5

while True:
    success, frame = cap.read()
    frame = cv2.flip(frame, 1)

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb)

    h, w, _ = frame.shape

    now = time.time()
    if not game_over and now >= next_spawn:
        fruits.append(make_fruit(w, h))
        next_spawn = now + random.uniform(0.6, 1.5)

    for fruit in fruits:
        fruit["vy"] += GRAVITY
        fruit["x"] += fruit["vx"]
        fruit["y"] += fruit["vy"]
        cv2.circle(frame, (int(fruit["x"]), int(fruit["y"])), fruit["r"], fruit["colour"], -1)

    for f in fruits:
        if f["y"] > h + 100 and f["vy"] > 0:
            lives -= 1

    # Make list of fruits only if haven't fallen off
    fruits = [f for f in fruits if not (f["y"] > h + 100 and f["vy"] > 0)]

    for half in halves:
        half["vy"] += GRAVITY
        half["x"] += half["vx"]
        half["y"] += half["vy"]
        center = (int(half["x"]), int(half["y"]))
        cv2.ellipse(frame, center, (half["r"], half["r"]), half["angle"], 0, 180, half["colour"], -1)
        cv2.ellipse(frame, center, (half["r"] - 8, half["r"] - 8), half["angle"], 0, 180, half["inner"], -1)
    
    # Halves clean up
    halves = [hf for hf in halves if hf["y"] < h + 100]

    for p in particles:
        p["vy"] += GRAVITY * 0.5
        p["x"] += p["vx"]
        p["y"] += p["vy"]
        p["life"] -= 1
        size = max(1, p["life"] // 3)
        cv2.circle(frame, (int(p["x"]), int(p["y"])), size, p["colour"], -1)

    # Particles clean up
    particles = [p for p in particles if p["life"] > 0]

    if lives <= 0:
        game_over = True
        fruits = []

    seen = set()

    if results.multi_hand_landmarks:
        for hand, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
            label = handedness.classification[0].label
            seen.add(label)
            tip = hand.landmark[8]
            x = int(tip.x * w)
            y = int(tip.y * h)

            if label not in trails:
                trails[label] = deque(maxlen=8)
            trails[label].append((x, y))

            cv2.circle(frame, (x, y), 10, (255, 255, 255), -1)

    for label in list(trails.keys()):
        if label not in seen:
            del trails[label]

    for trail in trails.values():
        if len(trail) >= 2:
            ax, ay = trail[-2]
            bx, by = trail[-1]
            speed = ((bx - ax) ** 2 + (by - ay) ** 2) ** 0.5
            if speed > SLICE_SPEED:
                for fruit in fruits:
                    if dist_to_segment(fruit["x"], fruit["y"], ax, ay, bx, by) < fruit["r"]:
                        fruit["sliced"] = True
                        score += 1

                        angle = math.degrees(math.atan2(by - ay, bx - ax))
                        a = math.radians(angle)
                        nx, ny = -math.sin(a), math.cos(a)
                        # side is -1 the first iteration & 1 the second
                        for side in (-1, 1):
                            halves.append({
                                "x": fruit["x"],
                                "y": fruit["y"],
                                "vx": fruit["vx"] + nx * side * 6,
                                "vy": fruit["vy"] * 0.5 + ny * side * 6,
                                "r": fruit["r"],
                                "angle": angle if side == 1 else angle + 180,
                                "colour": fruit["colour"],
                                "inner": fruit["inner"],
                            })

                        for _ in range(20):
                            direction = random.uniform(0, 2 * math.pi)
                            speed = random.uniform(2, 12)
                            particles.append({
                                "x": fruit["x"],
                                "y": fruit["y"],
                                "vx": math.cos(direction) * speed,
                                "vy": math.sin(direction) * speed,
                                "life": 20,
                                "colour": fruit["inner"],
                            })

    fruits = [f for f in fruits if not f["sliced"]]

    for trail in trails.values():
        points = list(trail)
        for i in range(1, len(points)):
            thickness = 2 + i * 2
            cv2.line(frame, points[i - 1], points[i], (255, 255, 255), thickness)

    cv2.putText(frame, str(score), (30, 80), cv2.FONT_HERSHEY_DUPLEX, 2.5, (0, 230, 255), 4)
    cv2.putText(frame, "Lives: " + str(lives), (w - 400, 80), cv2.FONT_HERSHEY_DUPLEX, 2.5, (0, 230, 255), 4)

    if game_over:
        cv2.putText(frame, "GAME OVER", (w // 2 - 270, h // 2), cv2.FONT_HERSHEY_DUPLEX, 3, (0, 0, 255), 6)
        cv2.putText(frame, "Press R to restart", (w // 2 - 230, h // 2 + 80), cv2.FONT_HERSHEY_DUPLEX, 1.2, (0, 0, 255), 2)

    cv2.imshow("Fruit Ninja", frame)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    if key == ord('r'):
        score = 0
        lives = 3
        fruits = []
        halves = []
        particles = []
        game_over = False

cap.release()
cv2.destroyAllWindows()