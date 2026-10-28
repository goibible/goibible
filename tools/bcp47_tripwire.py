"""Runtime tripwire for pre-BCP-47 edition paths (renamed 2026-10-28, see Meta_Bible_Data/docs/bcp47_naming.md).

Grep and tools/bcp47_composite_scan.py only see names written in source. This sees the final path of every
open / listdir / scandir / glob / stat (exists, is_file, ...) in a Python process, however the name was assembled, so a composite like
'GOI_Zh_' + ed or f"GOI_Bible_{lang.capitalize()}" is caught when it runs. That matters because a glob of a
missing directory does not fail: it returns zero files and the script "passes".

On a hit: one warning on stderr per call site, and a line in ~/.cache/goi_bcp47_tripwire.log naming the calling
file:line. GOI_BCP47_TRIPWIRE=raise turns hits into errors; =off disables it.

Per run: tools/py-tripwire script.py [args]. Always-on (optional, owner's choice): tools/install_bcp47_tripwire.sh.
"""
import os
import re
import sys
import time

OLD = re.compile(r"GOI_Bible_(English|Chinese_Han[st])(/|$)|[_/]GOI_Zh_Han[st]\.(txt|db|sql|epub)$")
EVENTS = {"open", "os.listdir", "os.scandir", "glob.glob", "os.mkdir", "os.rename",
          "pathlib.Path.glob", "pathlib.Path.rglob"}  # 3.12 pathlib skips scandir on a missing dir
LOG = os.path.expanduser("~/.cache/goi_bcp47_tripwire.log")
MODE = os.environ.get("GOI_BCP47_TRIPWIRE", "warn")
_seen = set()


def _caller() -> str:
    f = sys._getframe(2)
    while f and (f.f_code.co_filename == _SELF or "/lib/python" in f.f_code.co_filename or f.f_code.co_filename.startswith("<frozen")):
        f = f.f_back
    return f"{f.f_code.co_filename}:{f.f_lineno}" if f else "?"


def _hook(event, args):
    if event not in EVENTS or not args:
        return
    try:
        hit = _check(event, args[0])
    except Exception:  # a tripwire must never break the program it watches
        return
    if hit and MODE == "raise":
        raise FileNotFoundError(f"pre-BCP-47 edition path {hit!r} (see Meta_Bible_Data/docs/bcp47_naming.md)")


def _check(event, path):
    if isinstance(path, os.PathLike):
        path = os.fspath(path)
    if isinstance(path, bytes):
        path = path.decode(errors="replace")
    if not isinstance(path, str) or not OLD.search(path):
        return None
    where = _caller()
    if where not in _seen:  # one report per call site; the call site is what needs fixing
        _seen.add(where)
        msg = f"BCP47 TRIPWIRE: old edition path {path!r} via {event} at {where} (further hits from here not repeated)"
        try:
            with open(LOG, "a", encoding="utf-8") as fh:  # cannot re-trigger: LOG never matches OLD
                fh.write(f"{time.strftime('%Y-%m-%dT%H:%M:%S')} pid={os.getpid()} argv={' '.join(sys.argv)[:200]} | {msg}\n")
        except OSError:
            pass
        print(msg, file=sys.stderr)
    return path


_SELF = _check.__code__.co_filename


def _wrap_stat(orig):
    # exists()/is_file()/isdir() go through stat, which raises no audit event; probing a missing old path
    # and quietly skipping it is exactly the silent-zero failure this guards against
    def stat(path, *args, **kwargs):
        _hook("os.stat", (path,))
        return orig(path, *args, **kwargs)
    stat.__wrapped__ = orig
    return stat


if MODE != "off":
    sys.addaudithook(_hook)
    EVENTS.add("os.stat")
    os.stat, os.lstat = _wrap_stat(os.stat), _wrap_stat(os.lstat)
