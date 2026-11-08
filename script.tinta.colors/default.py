"""Entry point for RunScript(script.tinta.colors,slot,<slot>) from the skin."""
import os
import sys

import xbmcaddon
import xbmcvfs

sys.path.insert(0, os.path.join(xbmcvfs.translatePath(xbmcaddon.Addon("script.tinta.colors").getAddonInfo("path")),
                                "resources", "lib"))
import slots  # noqa: E402

if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) >= 2 and args[0] == "slot":
        slots.manage(args[1])
