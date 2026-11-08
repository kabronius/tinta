"""Content slots of the Tinta skin.

Each slot holds a folder of any add-on, stored in skin strings:
Skin.String(tinta.<slot>.path) and Skin.String(tinta.<slot>.label).
"""
import re

import xbmc
import xbmcaddon
import xbmcgui

ADDON = xbmcaddon.Addon("script.tinta.colors")

# (slot id, string id of its group, row number or None)
SLOTS = [("movies.%d" % i, 32010, i) for i in range(1, 5)] + \
        [("shows.%d" % i, 32011, i) for i in range(1, 5)] + \
        [("live", 32012, None), ("search", 32013, None)]


def tr(sid):
    return ADDON.getLocalizedString(sid)


def slot_name(slot):
    for sid, group, row in SLOTS:
        if sid == slot:
            return tr(group) if row is None else "%s · %s" % (tr(group), tr(32014) % row)
    return slot


def get(slot):
    return (xbmc.getInfoLabel("Skin.String(tinta.%s.path)" % slot),
            xbmc.getInfoLabel("Skin.String(tinta.%s.label)" % slot))


def _quote(value):
    return '"%s"' % value.replace('"', "'")


def set_slot(slot, path, label):
    xbmc.executebuiltin("Skin.SetString(tinta.%s.path,%s)" % (slot, _quote(path)))
    xbmc.executebuiltin("Skin.SetString(tinta.%s.label,%s)" % (slot, _quote(label)))


def clear(slot):
    xbmc.executebuiltin("Skin.Reset(tinta.%s.path)" % slot)
    xbmc.executebuiltin("Skin.Reset(tinta.%s.label)" % slot)


def clean_label(label):
    """Removes Kodi formatting tags ([COLOR], [B], ...) and decorative symbols."""
    label = re.sub(r"\[/?[A-Z]+[^\]]*\]", "", label)
    return re.sub(r"\s+", " ", label).strip(" >-|·")


def choose_slot_for(path, label):
    """Asks which slot the folder goes to and stores it."""
    names = []
    for sid, _, _ in SLOTS:
        current = get(sid)[1]
        names.append("%s  —  %s" % (slot_name(sid), current) if current else slot_name(sid))
    idx = xbmcgui.Dialog().select(tr(32001) % label, names)
    if idx < 0:
        return
    slot = SLOTS[idx][0]
    set_slot(slot, path, label)
    xbmcgui.Dialog().notification("Tinta", tr(32002) % (label, slot_name(slot)), time=3000)


def manage(slot):
    """From the settings button: open or clear the slot, or explain how to fill it."""
    path, label = get(slot)
    if not path:
        xbmcgui.Dialog().ok(slot_name(slot), tr(32003))
        return
    idx = xbmcgui.Dialog().select("%s — %s" % (slot_name(slot), label), [tr(32004), tr(32005)])
    if idx == 0:
        xbmc.executebuiltin("ActivateWindow(Videos,%s,return)" % _quote(path))
    elif idx == 1:
        clear(slot)
