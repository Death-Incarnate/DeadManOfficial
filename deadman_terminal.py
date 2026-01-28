#!/usr/bin/env python3
"""
DEADMAN Terminal Effects
========================
Advanced ASCII/ANSI animation engine with grayscale aesthetics.

Effects: Matrix rain, decrypt, glitch, pulse, scan, logo reveal
Colors: Grayscale only (232-255 ANSI range)

DEADMAN // DEATH INCARNATE
"""

import sys
import os
import time
import random
import math
import shutil
from dataclasses import dataclass
from typing import Iterator, Callable
from collections import deque

# ═══════════════════════════════════════════════════════════════════════════════
# ANSI ESCAPE SEQUENCES
# ═══════════════════════════════════════════════════════════════════════════════

class ANSI:
    """ANSI escape code constants"""
    ESC = "\033["
    RESET = f"{ESC}0m"
    BOLD = f"{ESC}1m"
    DIM = f"{ESC}2m"
    HIDE_CURSOR = f"{ESC}?25l"
    SHOW_CURSOR = f"{ESC}?25h"
    CLEAR_SCREEN = f"{ESC}2J"
    CLEAR_LINE = f"{ESC}2K"
    HOME = f"{ESC}H"

    @staticmethod
    def move(row: int, col: int) -> str:
        return f"\033[{row};{col}H"

    @staticmethod
    def gray(level: int) -> str:
        """Grayscale color (0-23 maps to ANSI 232-255)"""
        code = max(232, min(255, 232 + level))
        return f"\033[38;5;{code}m"

    @staticmethod
    def bg_gray(level: int) -> str:
        """Background grayscale"""
        code = max(232, min(255, 232 + level))
        return f"\033[48;5;{code}m"

# ═══════════════════════════════════════════════════════════════════════════════
# EASING FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def ease_in_out_sine(t: float) -> float:
    return -(math.cos(math.pi * t) - 1) / 2

def ease_out_cubic(t: float) -> float:
    return 1 - pow(1 - t, 3)

def ease_in_expo(t: float) -> float:
    return 0 if t == 0 else pow(2, 10 * t - 10)

def ease_out_bounce(t: float) -> float:
    n1, d1 = 7.5625, 2.75
    if t < 1 / d1:
        return n1 * t * t
    elif t < 2 / d1:
        t -= 1.5 / d1
        return n1 * t * t + 0.75
    elif t < 2.5 / d1:
        t -= 2.25 / d1
        return n1 * t * t + 0.9375
    else:
        t -= 2.625 / d1
        return n1 * t * t + 0.984375

# ═══════════════════════════════════════════════════════════════════════════════
# BRAILLE & BLOCK CHARACTERS
# ═══════════════════════════════════════════════════════════════════════════════

BLOCKS = " ░▒▓█"
BLOCKS_REVERSE = "█▓▒░ "
BRAILLE_DOTS = "⠁⠂⠄⡀⠈⠐⠠⢀"
BRAILLE_SPINNER = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
BRAILLE_WAVE = "⣀⣤⣶⣿⣶⣤⣀"
GLITCH_CHARS = "░▒▓█▄▀■□▪▫●○◌◎"
DECRYPT_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*"

# ═══════════════════════════════════════════════════════════════════════════════
# ASCII LOGO
# ═══════════════════════════════════════════════════════════════════════════════

DEADMAN_LOGO = r"""
██████╗ ███████╗ █████╗ ██████╗ ███╗   ███╗ █████╗ ███╗   ██╗
██╔══██╗██╔════╝██╔══██╗██╔══██╗████╗ ████║██╔══██╗████╗  ██║
██║  ██║█████╗  ███████║██║  ██║██╔████╔██║███████║██╔██╗ ██║
██║  ██║██╔══╝  ██╔══██║██║  ██║██║╚██╔╝██║██╔══██║██║╚██╗██║
██████╔╝███████╗██║  ██║██████╔╝██║ ╚═╝ ██║██║  ██║██║ ╚████║
╚═════╝ ╚══════╝╚═╝  ╚═╝╚═════╝ ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝
""".strip().split('\n')

DEADMAN_SMALL = "DEADMAN"
TAGLINE = "DEATH INCARNATE"
SIGNATURE = "DEADMAN // DEATH INCARNATE"

# ═══════════════════════════════════════════════════════════════════════════════
# CORE ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class TerminalSize:
    width: int
    height: int

def get_terminal_size() -> TerminalSize:
    size = shutil.get_terminal_size((80, 24))
    return TerminalSize(size.columns, size.lines)

class Canvas:
    """Double-buffered terminal canvas for flicker-free rendering"""

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.buffer: list[list[str]] = []
        self.colors: list[list[int]] = []
        self.clear()

    def clear(self):
        self.buffer = [[' ' for _ in range(self.width)] for _ in range(self.height)]
        self.colors = [[8 for _ in range(self.width)] for _ in range(self.height)]

    def set(self, x: int, y: int, char: str, gray_level: int = 12):
        if 0 <= x < self.width and 0 <= y < self.height:
            self.buffer[y][x] = char
            self.colors[y][x] = gray_level

    def render(self) -> str:
        output = [ANSI.HOME]
        for y, row in enumerate(self.buffer):
            line = ""
            prev_color = -1
            for x, char in enumerate(row):
                color = self.colors[y][x]
                if color != prev_color:
                    line += ANSI.gray(color)
                    prev_color = color
                line += char
            output.append(line + ANSI.RESET)
        return '\n'.join(output)

# ═══════════════════════════════════════════════════════════════════════════════
# EFFECTS
# ═══════════════════════════════════════════════════════════════════════════════

def effect_matrix_rain(duration: float = 8.0, fps: int = 20):
    """Grayscale matrix rain effect"""
    term = get_terminal_size()
    canvas = Canvas(term.width, term.height - 1)

    # Rain drops: (x, y, speed, length, chars)
    drops: list[dict] = []
    chars = "01アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン"

    for x in range(0, term.width, 2):
        if random.random() < 0.4:
            drops.append({
                'x': x,
                'y': random.randint(-20, 0),
                'speed': random.uniform(0.3, 1.0),
                'length': random.randint(5, 15),
                'chars': [random.choice(chars) for _ in range(20)]
            })

    start = time.time()
    frame_delay = 1.0 / fps

    print(ANSI.HIDE_CURSOR + ANSI.CLEAR_SCREEN, end='')

    try:
        while time.time() - start < duration:
            canvas.clear()

            for drop in drops:
                drop['y'] += drop['speed']

                for i in range(drop['length']):
                    y = int(drop['y']) - i
                    if 0 <= y < canvas.height:
                        # Head is bright, tail fades
                        brightness = max(0, 23 - i * 2)
                        char = drop['chars'][i % len(drop['chars'])]
                        canvas.set(drop['x'], y, char, brightness)

                # Reset drop when off screen
                if drop['y'] - drop['length'] > canvas.height:
                    drop['y'] = random.randint(-15, -5)
                    drop['speed'] = random.uniform(0.3, 1.0)
                    drop['chars'] = [random.choice(chars) for _ in range(20)]

            # Spawn new drops occasionally
            if random.random() < 0.05:
                x = random.randint(0, term.width - 1)
                drops.append({
                    'x': x,
                    'y': -5,
                    'speed': random.uniform(0.3, 1.0),
                    'length': random.randint(5, 15),
                    'chars': [random.choice(chars) for _ in range(20)]
                })

            sys.stdout.write(canvas.render())
            sys.stdout.flush()
            time.sleep(frame_delay)

    finally:
        print(ANSI.SHOW_CURSOR + ANSI.CLEAR_SCREEN, end='')

def effect_decrypt(text: str = SIGNATURE, duration: float = 4.0, fps: int = 30):
    """Movie-style decrypt effect - characters resolve from random to final"""
    term = get_terminal_size()
    text_len = len(text)
    start_x = (term.width - text_len) // 2
    start_y = term.height // 2

    # State: -1 = not started, 0-1 = decrypting, 1 = done
    char_states = [-1.0] * text_len
    frame_delay = 1.0 / fps
    start = time.time()

    print(ANSI.HIDE_CURSOR + ANSI.CLEAR_SCREEN, end='')

    try:
        while time.time() - start < duration:
            elapsed = time.time() - start
            progress = elapsed / duration

            output = ANSI.move(start_y, start_x)

            for i, char in enumerate(text):
                # Staggered start based on position
                char_start = i * 0.08
                char_progress = max(0, min(1, (elapsed - char_start) / 1.5))
                char_states[i] = char_progress

                if char == ' ':
                    output += ' '
                elif char_progress >= 1.0:
                    # Fully decrypted - bright
                    output += f"{ANSI.gray(20)}{char}"
                elif char_progress > 0:
                    # Decrypting - random chars with varying brightness
                    if random.random() < char_progress * 0.3:
                        output += f"{ANSI.gray(int(char_progress * 20))}{char}"
                    else:
                        rand_char = random.choice(DECRYPT_CHARS)
                        brightness = int(5 + char_progress * 10)
                        output += f"{ANSI.gray(brightness)}{rand_char}"
                else:
                    output += f"{ANSI.gray(3)}{'░'}"

            output += ANSI.RESET
            sys.stdout.write(output)
            sys.stdout.flush()
            time.sleep(frame_delay)

    finally:
        # Final clean display
        final = ANSI.move(start_y, start_x) + ANSI.gray(20) + text + ANSI.RESET
        sys.stdout.write(final)
        sys.stdout.flush()
        time.sleep(0.5)
        print(ANSI.SHOW_CURSOR, end='')

def effect_logo_reveal(duration: float = 5.0, fps: int = 24):
    """Reveal DEADMAN logo with scanning effect"""
    term = get_terminal_size()
    logo = DEADMAN_LOGO
    logo_height = len(logo)
    logo_width = max(len(line) for line in logo)

    start_y = (term.height - logo_height) // 2
    start_x = (term.width - logo_width) // 2

    frame_delay = 1.0 / fps
    start = time.time()

    print(ANSI.HIDE_CURSOR + ANSI.CLEAR_SCREEN, end='')

    try:
        while time.time() - start < duration:
            elapsed = time.time() - start
            progress = min(1.0, elapsed / (duration * 0.7))
            scan_pos = int(progress * logo_width * 1.5) - logo_width // 4

            output = ""
            for y, line in enumerate(logo):
                output += ANSI.move(start_y + y, start_x)

                for x, char in enumerate(line):
                    if char == ' ':
                        output += ' '
                        continue

                    dist_from_scan = abs(x - scan_pos)

                    if dist_from_scan < 3:
                        # Scan line - bright
                        brightness = 23 - dist_from_scan * 4
                        output += f"{ANSI.gray(brightness)}{char}"
                    elif x < scan_pos - 3:
                        # Already revealed - medium bright with slight variation
                        brightness = 14 + int(math.sin(elapsed * 3 + x * 0.2) * 3)
                        output += f"{ANSI.gray(brightness)}{char}"
                    else:
                        # Not yet revealed
                        output += f"{ANSI.gray(3)}░"

                output += ANSI.RESET

            sys.stdout.write(output)
            sys.stdout.flush()
            time.sleep(frame_delay)

        # Hold final frame
        output = ""
        for y, line in enumerate(logo):
            output += ANSI.move(start_y + y, start_x) + ANSI.gray(16) + line + ANSI.RESET
        sys.stdout.write(output)
        sys.stdout.flush()
        time.sleep(1.0)

    finally:
        print(ANSI.SHOW_CURSOR, end='')

def effect_glitch_text(text: str = SIGNATURE, duration: float = 4.0, fps: int = 15):
    """Glitchy text effect with random disruptions"""
    term = get_terminal_size()
    start_x = (term.width - len(text)) // 2
    start_y = term.height // 2

    frame_delay = 1.0 / fps
    start = time.time()

    print(ANSI.HIDE_CURSOR + ANSI.CLEAR_SCREEN, end='')

    try:
        while time.time() - start < duration:
            output = ""

            # Occasional horizontal offset glitch
            x_offset = random.choice([0, 0, 0, 0, -2, -1, 1, 2]) if random.random() < 0.2 else 0

            # Main line
            output += ANSI.move(start_y, start_x + x_offset)
            for char in text:
                if random.random() < 0.1:
                    # Glitch this character
                    output += f"{ANSI.gray(random.randint(5, 23))}{random.choice(GLITCH_CHARS)}"
                else:
                    output += f"{ANSI.gray(random.randint(12, 20))}{char}"

            # Ghost lines above/below
            if random.random() < 0.3:
                ghost_y = start_y + random.choice([-1, 1])
                ghost_x = start_x + random.randint(-3, 3)
                output += ANSI.move(ghost_y, ghost_x)
                output += f"{ANSI.gray(5)}{text[:random.randint(3, len(text))]}"

            output += ANSI.RESET
            sys.stdout.write(output)
            sys.stdout.flush()
            time.sleep(frame_delay)

    finally:
        # Clean exit
        clean = ANSI.move(start_y, start_x) + ANSI.gray(16) + text + ANSI.RESET
        sys.stdout.write(ANSI.CLEAR_SCREEN + clean)
        sys.stdout.flush()
        time.sleep(0.5)
        print(ANSI.SHOW_CURSOR, end='')

def effect_pulse_logo(duration: float = 6.0, fps: int = 20):
    """Breathing/pulse effect on the logo"""
    term = get_terminal_size()
    logo = DEADMAN_LOGO
    logo_height = len(logo)
    logo_width = max(len(line) for line in logo)

    start_y = (term.height - logo_height) // 2
    start_x = (term.width - logo_width) // 2

    frame_delay = 1.0 / fps
    start = time.time()

    print(ANSI.HIDE_CURSOR + ANSI.CLEAR_SCREEN, end='')

    try:
        while time.time() - start < duration:
            elapsed = time.time() - start

            # Sine wave for breathing (0 to 1)
            pulse = (math.sin(elapsed * 2) + 1) / 2
            base_brightness = int(6 + pulse * 14)  # 6-20 range

            output = ""
            for y, line in enumerate(logo):
                output += ANSI.move(start_y + y, start_x)

                for x, char in enumerate(line):
                    if char == ' ':
                        output += ' '
                        continue

                    # Add some wave variation across characters
                    wave = math.sin(elapsed * 3 + x * 0.15 + y * 0.3) * 3
                    brightness = int(max(4, min(23, base_brightness + wave)))
                    output += f"{ANSI.gray(brightness)}{char}"

                output += ANSI.RESET

            # Tagline
            tag_x = (term.width - len(SIGNATURE)) // 2
            tag_y = start_y + logo_height + 2
            tag_brightness = int(8 + pulse * 8)
            output += ANSI.move(tag_y, tag_x) + ANSI.gray(tag_brightness) + SIGNATURE + ANSI.RESET

            sys.stdout.write(output)
            sys.stdout.flush()
            time.sleep(frame_delay)

    finally:
        print(ANSI.SHOW_CURSOR + ANSI.CLEAR_SCREEN, end='')

def effect_typewriter(text: str = SIGNATURE, duration: float = 3.0):
    """Typewriter effect with cursor"""
    term = get_terminal_size()
    start_x = (term.width - len(text)) // 2
    start_y = term.height // 2

    print(ANSI.HIDE_CURSOR + ANSI.CLEAR_SCREEN, end='')

    try:
        # Type each character
        for i, char in enumerate(text):
            output = ANSI.move(start_y, start_x)
            output += ANSI.gray(14) + text[:i]
            output += ANSI.gray(20) + char
            output += ANSI.gray(20) + "█" + ANSI.RESET  # Cursor
            sys.stdout.write(output)
            sys.stdout.flush()

            # Variable delay for rhythm
            delay = 0.12 if char == ' ' else random.uniform(0.04, 0.08)
            time.sleep(delay)

        # Blink cursor at end
        for _ in range(6):
            output = ANSI.move(start_y, start_x) + ANSI.gray(14) + text
            sys.stdout.write(output + ANSI.gray(20) + "█" + ANSI.RESET)
            sys.stdout.flush()
            time.sleep(0.4)
            sys.stdout.write(output + " " + ANSI.RESET)
            sys.stdout.flush()
            time.sleep(0.4)

    finally:
        print(ANSI.SHOW_CURSOR, end='')

def effect_spinner_showcase(duration: float = 8.0, fps: int = 12):
    """Showcase multiple spinner styles"""
    term = get_terminal_size()
    center_y = term.height // 2

    spinners = [
        ("BRAILLE", BRAILLE_SPINNER),
        ("BLOCKS ", "▁▂▃▄▅▆▇█▇▆▅▄▃▂▁"),
        ("DOTS   ", "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"),
        ("PIPE   ", "┤┘┴└├┌┬┐"),
        ("CIRCLE ", "◐◓◑◒"),
        ("WAVE   ", "⣀⣤⣶⣿⣶⣤⣀"),
    ]

    frame_delay = 1.0 / fps
    start = time.time()
    frame = 0

    print(ANSI.HIDE_CURSOR + ANSI.CLEAR_SCREEN, end='')

    try:
        while time.time() - start < duration:
            output = ""

            # Title
            title = "DEADMAN SPINNERS"
            output += ANSI.move(center_y - len(spinners) - 2, (term.width - len(title)) // 2)
            output += ANSI.gray(18) + title + ANSI.RESET

            for i, (name, chars) in enumerate(spinners):
                y = center_y - len(spinners)//2 + i
                char = chars[frame % len(chars)]

                line = f"  {name}  {char}  "
                x = (term.width - len(line)) // 2

                # Brightness varies by distance from selection
                brightness = 12 + int(math.sin(frame * 0.2 + i) * 6)

                output += ANSI.move(y, x)
                output += f"{ANSI.gray(brightness)}{line}{ANSI.RESET}"

            sys.stdout.write(output)
            sys.stdout.flush()

            frame += 1
            time.sleep(frame_delay)

    finally:
        print(ANSI.SHOW_CURSOR + ANSI.CLEAR_SCREEN, end='')

# ═══════════════════════════════════════════════════════════════════════════════
# DEMO RUNNER
# ═══════════════════════════════════════════════════════════════════════════════

def demo_sequence():
    """Run full demo sequence"""
    effects = [
        ("LOGO REVEAL", effect_logo_reveal, 5.0),
        ("PULSE", effect_pulse_logo, 5.0),
        ("DECRYPT", lambda d, f: effect_decrypt(SIGNATURE, d), 4.0),
        ("GLITCH", lambda d, f: effect_glitch_text(SIGNATURE, d), 4.0),
        ("TYPEWRITER", lambda d, f: effect_typewriter(SIGNATURE, d), 4.0),
        ("MATRIX RAIN", effect_matrix_rain, 6.0),
        ("SPINNERS", effect_spinner_showcase, 5.0),
    ]

    term = get_terminal_size()

    for name, effect_func, duration in effects:
        # Show effect name
        print(ANSI.CLEAR_SCREEN, end='')
        title = f"═══ {name} ═══"
        x = (term.width - len(title)) // 2
        y = term.height // 2
        print(ANSI.move(y, x) + ANSI.gray(16) + title + ANSI.RESET, end='')
        sys.stdout.flush()
        time.sleep(1.0)

        # Run effect
        try:
            effect_func(duration, 20)
        except TypeError:
            effect_func(duration)

        time.sleep(0.3)

    # Final signature
    print(ANSI.CLEAR_SCREEN, end='')
    sig_x = (term.width - len(SIGNATURE)) // 2
    sig_y = term.height // 2
    print(ANSI.move(sig_y, sig_x) + ANSI.gray(16) + SIGNATURE + ANSI.RESET)
    time.sleep(2.0)

def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="DEADMAN Terminal Effects Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Effects:
  demo      Run full demo sequence
  matrix    Matrix rain effect
  decrypt   Decrypt text reveal
  logo      Logo reveal with scan
  pulse     Breathing logo
  glitch    Glitchy text
  type      Typewriter effect
  spinners  Spinner showcase

DEADMAN // DEATH INCARNATE
        """
    )
    parser.add_argument('effect', nargs='?', default='demo',
                       choices=['demo', 'matrix', 'decrypt', 'logo', 'pulse', 'glitch', 'type', 'spinners'],
                       help='Effect to run (default: demo)')
    parser.add_argument('-d', '--duration', type=float, default=5.0,
                       help='Duration in seconds (default: 5.0)')
    parser.add_argument('-t', '--text', type=str, default=SIGNATURE,
                       help='Text for text-based effects')

    args = parser.parse_args()

    effects_map = {
        'demo': lambda: demo_sequence(),
        'matrix': lambda: effect_matrix_rain(args.duration),
        'decrypt': lambda: effect_decrypt(args.text, args.duration),
        'logo': lambda: effect_logo_reveal(args.duration),
        'pulse': lambda: effect_pulse_logo(args.duration),
        'glitch': lambda: effect_glitch_text(args.text, args.duration),
        'type': lambda: effect_typewriter(args.text, args.duration),
        'spinners': lambda: effect_spinner_showcase(args.duration),
    }

    try:
        effects_map[args.effect]()
    except KeyboardInterrupt:
        print(ANSI.SHOW_CURSOR + ANSI.RESET + ANSI.CLEAR_SCREEN, end='')
        sys.exit(0)

if __name__ == "__main__":
    main()
