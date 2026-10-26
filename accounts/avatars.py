"""
Avatar definitions for DRAW & DECEIVE.
"""

AVATARS = [
    {"key": "fox", "name": "Clever Fox", "emoji": "🦊", "bg": "#f97316"},
    {"key": "cat", "name": "Mischief Cat", "emoji": "🐱", "bg": "#ec4899"},
    {"key": "dog", "name": "Happy Pup", "emoji": "🐶", "bg": "#eab308"},
    {"key": "panda", "name": "Chill Panda", "emoji": "🐼", "bg": "#14b8a6"},
    {"key": "lion", "name": "Brave Lion", "emoji": "🦁", "bg": "#f59e0b"},
    {"key": "owl", "name": "Wise Owl", "emoji": "🦉", "bg": "#8b5cf6"},
    {"key": "frog", "name": "Peppy Frog", "emoji": "🐸", "bg": "#10b981"},
    {"key": "dragon", "name": "Mystic Dragon", "emoji": "🐲", "bg": "#ef4444"},
    {"key": "koala", "name": "Sleepy Koala", "emoji": "🐨", "bg": "#64748b"},
    {"key": "monkey", "name": "Playful Monkey", "emoji": "🐵", "bg": "#d97706"},
    {"key": "rabbit", "name": "Speedy Bunny", "emoji": "🐰", "bg": "#f43f5e"},
    {"key": "alien", "name": "Cosmic Alien", "emoji": "👽", "bg": "#06b6d4"},
    {"key": "wizard", "name": "Grand Wizard", "emoji": "🧙", "bg": "#a855f7"},
    {"key": "robot", "name": "Robo Artist", "emoji": "🤖", "bg": "#3b82f6"},
    {"key": "unicorn", "name": "Dream Unicorn", "emoji": "🦄", "bg": "#d946ef"},
    {"key": "ninja", "name": "Shadow Ninja", "emoji": "🥷", "bg": "#334155"},
]

AVATAR_MAP = {a["key"]: a for a in AVATARS}
DEFAULT_AVATAR = "fox"

def get_avatar_info(key):
    return AVATAR_MAP.get(key, AVATAR_MAP[DEFAULT_AVATAR])
