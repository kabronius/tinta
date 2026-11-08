"""Context entry "Use in Tinta…": assigns the selected folder to a skin slot."""
import os
import sys

import xbmcaddon
import xbmcvfs

sys.path.insert(0, os.path.join(xbmcvfs.translatePath(xbmcaddon.Addon("script.tinta.colors").getAddonInfo("path")),
                                "resources", "lib"))
import slots  # noqa: E402

if __name__ == "__main__":
    item = sys.listitem
    slots.choose_slot_for(item.getPath(), slots.clean_label(item.getLabel()))
