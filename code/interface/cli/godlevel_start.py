#!/usr/bin/env python3
import os
import sys
import time
import random
import shutil

# ========== ANSI CONSTANTS ==========
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"

GREEN = "\033[92m"
DARK_GREEN = "\033[32m"
BRIGHT_GREEN = "\033[38;5;46m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"

# ========== YOUR FINAL BANNER ==========
BANNER_LARGE = r"""
▄▄ ▄▄   ▄▄░▒ ▄▄▄▄▄▄░▒ ▄▄▄▄░▒  ▄▄ ▄▄░▒ ▄▄ ▄▄░▒ ▄▄░▒  ▄▄▄░▒  ▄▄░▒▄▄░▒      ▄▄▄▄░▒ ▄▄░▒ ▄▄▄▄░▒  ▄▄ ▄▄░▒ ▄▄▄▄▄░▒ ▄▄▄▄░▒
██▄██   ██░▒   ██░▒   ██▄█▄░▒ ██ ██░▒ ██▄██░▒ ██░▒ ██▀██░▒ ███▄██░▒ ▄▄▄ ██▀▀▀░▒ ██░▒ ██▄█▀░▒ ██▄██░▒ ██▄▄░▒  ██▄█▄░▒
 ▀█▀░▒  ██░▒   ██░▒   ██ ██░▒ ▀███▀░▒  ▀█▀░▒  ██░▒ ██▀██░▒ ██ ▀██░▒     ▀████░▒ ██░▒ ██░▒    ██ ██░▒ ██▄▄▄░▒ ██ ██░▒
"""

# ========== BASIC TERMINAL UTILS ==========
def clear():
    os.system("cls" if os.name == "nt" else "clear")

def term_size():
    try:
        cols, rows = shutil.get_terminal_size(fallback=(80, 24))
    except Exception:
        cols, rows = 80, 24
    return cols, rows

# ========== STATIC / GLITCH BOOT ==========
def static_noise(width=70, density=0.10):
    chars = [' ', '░', '▒', '▓', '█']
    return "".join(
        random.choice(chars) if random.random() < density else " "
        for _ in range(width)
    )

def glitchy_print(text, delay=0.015):
    for ch in text:
        if ch != " " and random.random() < 0.06:
            sys.stdout.write(random.choice([" ", "░", "▒", ch.lower(), ch.upper()]))
        else:
            sys.stdout.write(ch)
        sys.stdout.flush()
        time.sleep(delay)
    print()

def boot_sequence():
    clear()
    cols, _ = term_size()
    width = min(cols - 2, 100)

    messages = [
        "[BOOT] Waking vitruvian-cipher neural lattice...",
        "[CORE] Locking rotational symmetry of keyspace...",
        "[RAG ] Splicing cryptographic corpus into memory...",
        "[LINK] Binding terminal to cipher daemon channel..."
    ]

    # STATIC TV NOISE
    for _ in range(12):
        print(DIM + GREEN + static_noise(width) + RESET)
        time.sleep(0.035)

    time.sleep(0.15)

    # GLITCHED STATUS LINES
    print()
    for msg in messages:
        sys.stdout.write(BRIGHT_GREEN)
        glitchy_print(msg)
        sys.stdout.write(RESET)
        time.sleep(0.12)

    time.sleep(0.4)

# ========== CRAZY MATRIX RAIN ==========
def matrix_rain(duration=5.0, speed=0.03):
    clear()
    cols, rows = term_size()
    cols = max(60, cols)
    rows = max(20, rows)

    rain_chars = list("01{}[]<>|/=+*#&$")  # tweak if you want more/less noise
    num_cols = cols // 2
    drops = [random.randint(-rows, 0) for _ in range(num_cols)]

    start = time.time()
    while time.time() - start < duration:
        lines = []
        for row in range(rows):
            line_parts = []
            for i in range(num_cols):
                col_pos = i * 2
                head = drops[i]

                if row == head:
                    ch = random.choice(rain_chars)
                    style = BRIGHT_GREEN + BOLD
                elif head - 3 <= row < head:
                    ch = random.choice(rain_chars)
                    style = GREEN
                elif head - 7 <= row < head - 3:
                    ch = random.choice(rain_chars)
                    style = DARK_GREEN + DIM
                else:
                    ch = " "
                    style = ""

                line_parts.append(style + ch + " " + RESET)
            lines.append("".join(line_parts))

        frame = "\n".join(lines)
        clear()
        sys.stdout.write(frame)

        # Occasionally inject a "shockwave" line
        if random.random() < 0.12:
            shock_row = random.randint(0, rows - 1)
            sys.stdout.write(
                "\033[%d;1H" % (shock_row + 1) +
                MAGENTA + DIM +
                ("-" * (cols // 2)) +
                RESET
            )

        sys.stdout.flush()

        for i in range(num_cols):
            drops[i] += 1 if random.random() < 0.9 else 0
            if drops[i] > rows + random.randint(3, 15):
                drops[i] = random.randint(-rows, -1)

        time.sleep(speed)

# ========== BANNER CORRUPTION / PULSE ==========
def corrupt_banner(text: str, corruption: float = 0.15) -> str:
    noise_chars = ["░", "▒", "▓", "█", "Ø", "Ψ", "Δ", "Ξ"]
    out_lines = []
    for line in text.splitlines():
        new_line = []
        for ch in line:
            if ch != " " and random.random() < corruption:
                new_line.append(random.choice(noise_chars))
            else:
                new_line.append(ch)
        out_lines.append("".join(new_line))
    return "\n".join(out_lines)

def pulse_banner_frames(banner: str, pulses: int = 5):
    for i in range(pulses):
        clear()
        corruption = max(0.02, 0.4 - i * 0.07)  # gradually stabilizes
        corrupted = corrupt_banner(banner, corruption=corruption)
        color = BRIGHT_GREEN if i % 2 == 0 else CYAN
        print(color + BOLD + corrupted + RESET)
        time.sleep(0.25)

# ========== FINAL CLEAN BANNER ==========
def final_banner():
    clear()
    print(BRIGHT_GREEN + BOLD + BANNER_LARGE + RESET)
    print(
        DIM + CYAN +
        "   vitruvian-cipher • AI-augmented cryptographic operations console" +
        RESET
    )
    print(
        DIM + GREEN +
        "   commands: 'help'  to list incantations • 'exit' to close the sigil" +
        RESET
    )
    print()

# ========== MAIN ==========
if __name__ == "__main__":
    boot_sequence()
    matrix_rain(duration=6.0, speed=0.028)
    pulse_banner_frames(BANNER_LARGE, pulses=6)
    final_banner()
    input(BRIGHT_GREEN + ">>> press enter to awaken the agent... " + RESET)
    # from here, drop into your actual CLI / REPL
    # main_cli_loop()


