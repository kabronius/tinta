"""Tinta service: publishes the M3 colour scheme of the focused artwork.

Window(Home) properties: Tinta.<Role> = AARRGGBB (see palette.DARK_ROLES),
Tinta.Seed = AARRGGBB of the seed, Tinta.Ready = 1.

Artwork source, in order:
  1. Window(Home).Property(Tinta.Source), when a window sets it;
  2. the playing item while the video OSD or info is open;
  3. the focused container (System.CurrentControlId): poster, thumb, fanart, icon;
  4. the ListItem of the active window or dialog.
When no artwork is found the last scheme stays. Skin.HasSetting(tinta_static) forces the base scheme.
"""
import io
import os
import sys
import time
from collections import OrderedDict

import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

sys.path.insert(0, os.path.join(xbmcvfs.translatePath(xbmcaddon.Addon().getAddonInfo("path")), "resources", "lib"))
import palette  # noqa: E402

HOME = xbmcgui.Window(10000)
POLL_S = 0.12
FADE_STEPS = 6
FADE_S = 0.03
ART_KEYS = ("Art(poster)", "Art(tvshow.poster)", "Art(thumb)", "Art(fanart)", "Icon")
CACHE_MAX = 400


def log(msg, level=xbmc.LOGDEBUG):
    xbmc.log(f"[script.tinta.colors] {msg}", level)


def first_art(prefix):
    for key in ART_KEYS:
        val = xbmc.getInfoLabel(f"{prefix}{key}")
        if val and not val.startswith("Default"):  # the skin's Default*.png icons do not count
            return val
    return ""


def current_source():
    forced = HOME.getProperty("Tinta.Source")
    if forced:
        return forced
    if xbmc.getCondVisibility("Player.HasVideo + [Window.IsVisible(videoosd) | Window.IsVisible(fullscreeninfo) | Window.IsActive(fullscreenvideo)]"):
        for key in ("Player.Art(poster)", "Player.Art(tvshow.poster)", "Player.Art(thumb)", "Player.Art(fanart)"):
            val = xbmc.getInfoLabel(key)
            if val:
                return val
    cid = xbmc.getInfoLabel("System.CurrentControlId")
    if cid and cid.isdigit() and xbmc.getCondVisibility(f"Integer.IsGreater(Container({cid}).NumItems,0)"):
        art = first_art(f"Container({cid}).ListItem.")
        if art:
            return art
    return first_art("ListItem.")


def load_image(url):
    """PIL image from the Kodi texture cache, otherwise read from its URL."""
    from PIL import Image

    crc = xbmc.getCacheThumbName(url)
    for ext in (".jpg", ".png"):
        path = f"special://thumbnails/{crc[0]}/{crc[:-4]}{ext}"
        if xbmcvfs.exists(path):
            return Image.open(xbmcvfs.translatePath(path))
    src = url
    if src.startswith("image://"):
        from urllib.parse import unquote
        src = unquote(src[len("image://"):].rstrip("/"))
    f = xbmcvfs.File(src)
    try:
        data = f.readBytes()
    finally:
        f.close()
    if not data:
        raise IOError("empty image")
    return Image.open(io.BytesIO(bytes(data)))


def seed_from_image(img):
    img = img.convert("RGB")
    img.thumbnail((96, 96))
    q = img.quantize(colors=16, method=1)  # MAXCOVERAGE: keeps small clusters better
    pal = q.getpalette()
    counts = q.getcolors(256) or []
    pixels = [(cnt, tuple(pal[idx * 3: idx * 3 + 3])) for cnt, idx in counts]
    return palette.pick_seed(pixels)


DEV_DIR = "/storage/emulated/0/Download/tinta/"


class DevMonitor(xbmc.Monitor):
    """Development install: JSONRPC.NotifyAll("tinta", "deploy", {"zips": [...], "reload": true}).

    Active only when DEV_DIR/.dev exists (created by tools/deploy.py over adb). Extracts the zips found
    in DEV_DIR into the Kodi add-on folder and reloads the skin.
    """

    def onNotification(self, sender, method, data):
        if sender != "tinta" or not method.endswith("deploy"):
            return
        if not os.path.exists(os.path.join(DEV_DIR, ".dev")):
            log("deploy ignored: development mode is off", xbmc.LOGINFO)
            return
        import json
        import zipfile

        req = {}
        try:
            req = json.loads(data) if data else {}
            dest = xbmcvfs.translatePath("special://home/addons/")
            for name in req.get("zips", []):
                path = os.path.realpath(os.path.join(DEV_DIR, os.path.basename(name)))
                if not path.startswith(DEV_DIR):
                    continue
                with zipfile.ZipFile(path) as z:
                    z.extractall(dest)
                log(f"extracted {path}", xbmc.LOGINFO)
            for builtin in req.get("builtins", []):  # development only, e.g. Skin.SetString
                xbmc.executebuiltin(builtin, True)
            xbmc.executebuiltin("UpdateLocalAddons", True)
            if req.get("reload"):
                xbmc.executebuiltin("ReloadSkin()")
            HOME.setProperty("Tinta.Deployed", req.get("stamp", "1"))
        except Exception as exc:
            log(f"deploy failed: {exc}", xbmc.LOGERROR)
            HOME.setProperty("Tinta.Deployed", f"error {req.get('stamp', '') if isinstance(req, dict) else ''}: {exc}")


class Tinta:
    def __init__(self):
        self.monitor = DevMonitor()
        self.cache = OrderedDict()
        self.default = palette.default_scheme()
        self.shown = None
        self.last_source = None

    def scheme_for(self, url):
        if url in self.cache:
            self.cache.move_to_end(url)
            return self.cache[url]
        try:
            h, c = seed_from_image(load_image(url))
            scheme = palette.scheme_from_seed(h, c)
            scheme["Seed"] = palette.tone(h, c, 50)
        except Exception as exc:  # unreadable artwork: keep the current scheme
            log(f"artwork not usable {url!r}: {exc}", xbmc.LOGINFO)
            scheme = None
        self.cache[url] = scheme
        if len(self.cache) > CACHE_MAX:
            self.cache.popitem(last=False)
        return scheme

    def publish(self, scheme):
        for role, rgb in scheme.items():
            HOME.setProperty(f"Tinta.{role}", palette.to_argb(rgb))

    def show(self, scheme):
        if scheme == self.shown:
            return
        if self.shown is None:
            self.publish(scheme)
        else:
            start = self.shown
            for i in range(1, FADE_STEPS + 1):
                t = i / FADE_STEPS
                self.publish({k: palette.mix(start.get(k, v), v, t) for k, v in scheme.items()})
                if self.monitor.waitForAbort(FADE_S):
                    return
        self.shown = scheme
        HOME.setProperty("Tinta.Ready", "1")

    def run(self):
        log("started", xbmc.LOGINFO)
        base = dict(self.default)
        base["Seed"] = palette.DEFAULT_SEED
        self.default = base
        self.show(self.default)
        while not self.monitor.waitForAbort(POLL_S):
            if xbmc.getCondVisibility("Skin.HasSetting(tinta_static)"):
                self.show(self.default)
                self.last_source = None
                continue
            src = current_source()
            if not src or src == self.last_source:
                continue
            self.last_source = src
            started = time.monotonic()
            scheme = self.scheme_for(src)
            if scheme:
                self.show(scheme)
                log(f"scheme from {src} in {1000 * (time.monotonic() - started):.0f} ms")
        log("stopped", xbmc.LOGINFO)


if __name__ == "__main__":
    Tinta().run()
