"""
Visuomotor rotation reaching task (mini motor-learning experiment).

How it works
- Move the cursor into the white start circle and hold still briefly.
- A target appears in one of 8 directions. Move to it as fast and straight as you can.
- Phases: baseline (normal cursor) -> rotation (cursor rotated by ROTATION_DEG) -> washout (normal again).
- During the return to the start circle the cursor is shown normally.

Output (in ./data/)
- trials_<session>.csv : one row per trial (phase, target angle, reaction time, movement time)
- samples_<session>.csv: one row per frame during the reach (time, raw mouse, displayed cursor)

Controls: ESC = quit (data collected so far is saved).
"""

import csv
import math
import os
import random
import time

import pygame

# ---------------- Settings ----------------
WIDTH, HEIGHT = 1000, 800
FPS = 120
START_RADIUS = 18
TARGET_RADIUS = 22
TARGET_DISTANCE = 300          # pixels from start to target
HOLD_TIME = 0.5                # seconds to hold in start circle
ROTATION_DEG = 45              # cursor rotation during the rotation phase
N_DIRECTIONS = 8
PHASES = [                     # (phase name, number of trials, rotation in degrees)
    ("baseline", 24, 0),
    ("rotation", 160, ROTATION_DEG),
    ("washout", 24, 0),
]
SEED = None                    # set an int for a reproducible target order
# ------------------------------------------

BG = (20, 20, 24)
WHITE = (235, 235, 235)
GREEN = (60, 200, 120)
YELLOW = (240, 200, 60)
GRAY = (110, 110, 120)


def rotate(dx, dy, deg):
    a = math.radians(deg)
    return dx * math.cos(a) - dy * math.sin(a), dx * math.sin(a) + dy * math.cos(a)


def build_trials(rng):
    trials = []
    for phase, n, rot in PHASES:
        angles = []
        while len(angles) < n:  # shuffle all 8 directions in blocks
            block = [i * 360 / N_DIRECTIONS for i in range(N_DIRECTIONS)]
            rng.shuffle(block)
            angles.extend(block)
        trials.extend((phase, a, rot) for a in angles[:n])
    return trials


def main():
    rng = random.Random(SEED)
    trials = build_trials(rng)
    session = time.strftime("%Y%m%d_%H%M%S")
    os.makedirs("data", exist_ok=True)
    trials_path = os.path.join("data", f"trials_{session}.csv")
    samples_path = os.path.join("data", f"samples_{session}.csv")

    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Reach task - ESC to quit")
    font = pygame.font.SysFont(None, 28)
    clock = pygame.time.Clock()
    pygame.mouse.set_visible(False)
    cx, cy = WIDTH // 2, HEIGHT // 2

    with open(trials_path, "w", newline="") as ft, open(samples_path, "w", newline="") as fs:
        tw, sw = csv.writer(ft), csv.writer(fs)
        tw.writerow(["trial", "phase", "rotation_deg", "target_angle_deg",
                     "target_x", "target_y", "reaction_time_s", "movement_time_s"])
        sw.writerow(["trial", "t_s", "mouse_x", "mouse_y", "cursor_x", "cursor_y"])

        trial_idx = 0
        state = "return"            # return -> hold -> reach
        hold_start = None
        running = True

        while running and trial_idx < len(trials):
            phase, angle, rot = trials[trial_idx]
            tx = cx + TARGET_DISTANCE * math.cos(math.radians(angle))
            ty = cy - TARGET_DISTANCE * math.sin(math.radians(angle))

            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    running = False

            mx, my = pygame.mouse.get_pos()
            now = time.perf_counter()

            # Cursor shown to the participant
            if state == "reach" and rot != 0:
                dx, dy = rotate(mx - cx, my - cy, rot)
                cur_x, cur_y = cx + dx, cy + dy
            else:
                cur_x, cur_y = mx, my

            dist_start = math.hypot(cur_x - cx, cur_y - cy)

            if state == "return":
                if dist_start < START_RADIUS:
                    state, hold_start = "hold", now
            elif state == "hold":
                if dist_start >= START_RADIUS:
                    state = "return"
                elif now - hold_start >= HOLD_TIME:
                    state = "reach"
                    go_time = now
                    move_onset = None
            elif state == "reach":
                t = now - go_time
                sw.writerow([trial_idx, f"{t:.4f}", mx, my, f"{cur_x:.1f}", f"{cur_y:.1f}"])
                if move_onset is None and dist_start > START_RADIUS:
                    move_onset = t
                if math.hypot(cur_x - tx, cur_y - ty) < TARGET_RADIUS:
                    rt = move_onset if move_onset is not None else 0.0
                    tw.writerow([trial_idx, phase, rot, angle, f"{tx:.1f}", f"{ty:.1f}",
                                 f"{rt:.4f}", f"{t - rt:.4f}"])
                    ft.flush(); fs.flush()
                    trial_idx += 1
                    state = "return"

            # Draw
            screen.fill(BG)
            pygame.draw.circle(screen, WHITE if state != "reach" else GRAY, (cx, cy), START_RADIUS, 2)
            if state == "reach":
                pygame.draw.circle(screen, GREEN, (int(tx), int(ty)), TARGET_RADIUS)
            pygame.draw.circle(screen, YELLOW, (int(cur_x), int(cur_y)), 6)
            label = font.render(f"Trial {trial_idx + 1}/{len(trials)}   phase: {phase}", True, GRAY)
            screen.blit(label, (20, 20))
            pygame.display.flip()
            clock.tick(FPS)

    pygame.quit()
    print(f"Saved {trial_idx} trials to {trials_path}")
    print(f"Saved samples to {samples_path}")


if __name__ == "__main__":
    main()
