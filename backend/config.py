"""
Persistent config stored in config.json.
Handles both dev mode (next to main.py) and PyInstaller frozen mode (userData dir).
"""
import json
import os
import sys
from pathlib import Path

_DEFAULTS = {
    "hero_nickname": "",
    "hh_path": "",
    "recent_window": 50,
}


def _data_dir() -> str:
    """
    Returns the directory where config.json and zhud.db are stored.
    Priority: ZHUD_DATA_DIR env var (set by Electron in packaged mode)
              → next to exe (PyInstaller)
              → next to main.py (dev)
    """
    env = os.environ.get("ZHUD_DATA_DIR", "").strip()
    if env:
        os.makedirs(env, exist_ok=True)
        return env
    if getattr(sys, "frozen", False):
        # PyInstaller: exe dir
        return os.path.dirname(sys.executable)
    # Dev mode: backend/ folder
    return os.path.dirname(os.path.abspath(__file__))


def _config_file() -> str:
    return os.path.join(_data_dir(), "config.json")


def load() -> dict:
    f = _config_file()
    if os.path.exists(f):
        try:
            with open(f, "r", encoding="utf-8") as fp:
                return {**_DEFAULTS, **json.load(fp)}
        except Exception:
            pass
    return dict(_DEFAULTS)


def save(data: dict):
    with open(_config_file(), "w", encoding="utf-8") as fp:
        json.dump(data, fp, indent=2, ensure_ascii=False)


def get_hero() -> str:
    return load().get("hero_nickname", "")


def set_hero(nickname: str):
    cfg = load()
    cfg["hero_nickname"] = nickname.strip()
    save(cfg)


def get_hh_path() -> str:
    return load().get("hh_path", "")


def set_hh_path(path: str):
    cfg = load()
    cfg["hh_path"] = path.strip()
    save(cfg)


def is_configured() -> bool:
    cfg = load()
    return bool(cfg.get("hero_nickname") and cfg.get("hh_path"))


def find_hh_dirs() -> list:
    """
    Multi-strategy search for PokerStars HandHistory player folders.
    Returns [{nick, path, file_count}] sorted by most active first.
    """
    bases: set[Path] = set()
    home = Path.home()
    username = os.environ.get("USERNAME", home.name)

    for variant in ["Local", "Roaming"]:
        bases.add(home / "AppData" / variant / "PokerStars" / "HandHistory")
        bases.add(Path(f"C:/Users/{username}/AppData/{variant}/PokerStars/HandHistory"))

    for ini_path in [
        home / "AppData" / "Local" / "PokerStars" / "user.ini",
        home / "AppData" / "Roaming" / "PokerStars" / "user.ini",
    ]:
        try:
            if ini_path.exists():
                import configparser
                cfg = configparser.RawConfigParser()
                cfg.read(str(ini_path), encoding="utf-8")
                for section in cfg.sections():
                    for key in ["HandHistoryPath", "handhistorypath"]:
                        if cfg.has_option(section, key):
                            val = cfg.get(section, key).strip('"').strip()
                            if val:
                                bases.add(Path(val))
        except Exception:
            pass

    try:
        import winreg
        for hive in [winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE]:
            for reg_path in [r"SOFTWARE\PokerStars", r"SOFTWARE\WOW6432Node\PokerStars"]:
                try:
                    key = winreg.OpenKey(hive, reg_path)
                    for val_name in ["InstallDir", "Path", "HandHistoryPath"]:
                        try:
                            val, _ = winreg.QueryValueEx(key, val_name)
                            if val:
                                p = Path(val)
                                bases.add(p / "HandHistory")
                                bases.add(p)
                        except Exception:
                            pass
                except Exception:
                    pass
    except Exception:
        pass

    for drive in ["C:", "D:", "E:"]:
        bases.add(Path(f"{drive}/PokerStars/HandHistory"))
        bases.add(Path(f"{drive}/Users/{username}/AppData/Local/PokerStars/HandHistory"))

    dirs = []
    seen: set[str] = set()
    for base in bases:
        try:
            if not base.exists() or not base.is_dir():
                continue
            for d in base.iterdir():
                if not d.is_dir():
                    continue
                nick = d.name.strip()
                key  = str(d).lower().strip()
                if not nick or key in seen:
                    continue
                seen.add(key)
                try:
                    count = sum(1 for f in d.iterdir() if f.suffix.lower() == ".txt")
                except Exception:
                    count = 0
                dirs.append({"nick": nick, "path": str(d), "file_count": count})
        except Exception:
            pass

    return sorted(dirs, key=lambda x: -x["file_count"])


def find_path_for_nick(nick: str) -> str:
    nick_lower = nick.strip().lower()
    for d in find_hh_dirs():
        if d["nick"].strip().lower() == nick_lower:
            return d["path"]
    return ""
