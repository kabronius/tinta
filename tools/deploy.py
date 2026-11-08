#!/usr/bin/env python3
"""Build and install on a phone over adb + JSON-RPC.

Usage:
  deploy.py            build, copy the zips to /sdcard/Download/tinta, ask Kodi to extract them and reload the skin
  deploy.py --push     build and copy only (first install: "Install from zip file" in Kodi)
  deploy.py --shot F   also save a screenshot to F
  deploy.py --service  also restart the colour service (after changes to script.tinta.colors)

Environment: ADB = path of adb (default: adb from PATH).
"""
import argparse
import os
import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import build  # noqa: E402
import kodirpc  # noqa: E402

ADB = os.environ.get("ADB", "adb")
REMOTE = "/sdcard/Download/tinta/"


def adb(*args, **kw):
    return subprocess.run([ADB, *args], check=True, capture_output=True, text=kw.pop("text", True), **kw)


def screenshot(path):
    png = subprocess.run([ADB, "exec-out", "screencap", "-p"], check=True, capture_output=True).stdout
    Path(path).write_bytes(png)
    print(f"screenshot -> {path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--push", action="store_true")
    ap.add_argument("--service", action="store_true")
    ap.add_argument("--shot")
    ap.add_argument("addons", nargs="*", default=build.ADDONS)
    a = ap.parse_args()

    zips = [build.build_addon(x) for x in a.addons]
    adb("shell", "mkdir", "-p", REMOTE)
    adb("shell", "touch", REMOTE + ".dev")  # enables the development deploy in the service
    for z in zips:
        adb("push", str(z), REMOTE + z.name)
    print("copied to", REMOTE)
    if a.push:
        return
    adb("forward", "tcp:9090", "tcp:9090")
    stamp = str(time.time())
    kodirpc.call("JSONRPC.NotifyAll", {"sender": "tinta", "message": "deploy",
                                       "data": {"zips": [z.name for z in zips], "reload": True, "stamp": stamp}})
    for _ in range(40):
        r = kodirpc.call("XBMC.GetInfoLabels", {"labels": ["Window(Home).Property(Tinta.Deployed)"]})
        val = r["result"]["Window(Home).Property(Tinta.Deployed)"]
        if val == stamp:
            print("installed, skin reloaded")
            break
        if val.startswith(f"error {stamp}"):
            sys.exit(val)
        time.sleep(0.25)
    else:
        sys.exit("no answer from the service (is it installed and enabled?)")
    if a.service:
        for en in (False, True):
            kodirpc.call("Addons.SetAddonEnabled", {"addonid": "script.tinta.colors", "enabled": en})
        print("colour service restarted")
    if a.shot:
        time.sleep(1.5)
        screenshot(a.shot)


if __name__ == "__main__":
    main()
