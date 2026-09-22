"""Conjunto inicial de gestos (TechSpecs Seção 28)."""
from enum import Enum


class Gesture(str, Enum):
    IDLE = "idle"
    LOOK_UP = "look_up"
    LOOK_DOWN = "look_down"
    LOOK_LEFT = "look_left"
    LOOK_RIGHT = "look_right"
    NOD = "nod"
    SMALL_SHAKE = "small_shake"
    PAUSE = "pause"
    LEAN_FORWARD = "lean_forward"
    LEAN_BACK = "lean_back"
