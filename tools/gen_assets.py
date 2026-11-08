#!/usr/bin/env python3
"""Generate the textures and fonts of the Tinta skin.

Textures: white shapes (tinted in the skin with colordiffuse), 9-slice with border = radius.
Fonts: Roboto 400/500 instanced from the variable font; Material Symbols Rounded outline/filled
instanced and subset to the glyphs listed in ICONS.

Usage: gen_assets.py <source_font_dir> <skin_dir>
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw
from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

SS = 4  # supersampling for smooth edges

ICONS = [
    "home", "movie", "tv", "extension", "search", "settings", "arrow_back", "more_vert",
    "play_arrow", "pause", "replay_10", "forward_10", "subtitles", "graphic_eq", "tune",
    "speed", "closed_caption", "aspect_ratio", "lock", "favorite", "share", "bookmark_add",
    "close", "check", "star", "add", "bolt", "explore", "cloud_download", "info",
    "power_settings_new", "folder", "grid_view", "view_list", "sort", "filter_list", "refresh",
    "backspace", "arrow_upward", "space_bar", "keyboard_return", "keyboard_capslock",
    "chevron_left", "chevron_right", "expand_more", "expand_less", "volume_up", "volume_off",
    "skip_next", "skip_previous", "stop", "schedule", "download", "error", "warning",
    "notifications", "history", "trending_up", "person", "video_library", "apps", "delete",
    "edit", "language", "image", "music_note", "update", "fullscreen", "more_horiz",
    "keyboard_arrow_up", "keyboard_arrow_down", "radio_button_checked", "radio_button_unchecked",
    "check_box", "check_box_outline_blank", "visibility", "visibility_off", "link",
    "playlist_play", "folder_open", "arrow_forward", "restart_alt", "palette", "hourglass_empty",
    "dns", "keyboard", "123", "abc", "screen_rotation", "logout", "favorite_border",
    "live_tv", "radio_button_checked",
]


def rounded(w, h, r, path, stroke=0):
    img = Image.new("RGBA", (w * SS, h * SS), (255, 255, 255, 0))
    d = ImageDraw.Draw(img)
    box = [0, 0, w * SS - 1, h * SS - 1]
    if stroke:
        d.rounded_rectangle(box, radius=r * SS, outline=(255, 255, 255, 255), width=stroke * SS)
    else:
        d.rounded_rectangle(box, radius=r * SS, fill=(255, 255, 255, 255))
    img.resize((w, h), Image.LANCZOS).save(path)


def switch(out: Path):
    """M3 switch, 52x32dp = 143x88 px. On: filled track with the handle cut out (the surface shows
    through, close to a dark onPrimary handle). Off: outline + 16dp handle."""
    w, h = 143, 88
    for name in ("switch_on", "switch_off"):
        img = Image.new("RGBA", (w * SS, h * SS), (255, 255, 255, 0))
        d = ImageDraw.Draw(img)
        box = [0, 0, w * SS - 1, h * SS - 1]
        if name == "switch_on":
            d.rounded_rectangle(box, radius=h * SS // 2, fill=(255, 255, 255, 255))
            r = 33 * SS  # pallino 24dp
            cx, cy = (w - h // 2) * SS, h * SS // 2
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 255, 255, 0))
        else:
            d.rounded_rectangle(box, radius=h * SS // 2, outline=(255, 255, 255, 255), width=6 * SS)
            r = 22 * SS  # pallino 16dp
            cx, cy = (h // 2) * SS, h * SS // 2
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 255, 255, 255))
        img.resize((w, h), Image.LANCZOS).save(out / f"{name}.png")


def gradient(w, h, path, horizontal=False):
    img = Image.new("RGBA", (w, h), (255, 255, 255, 0))
    px = img.load()
    n = w if horizontal else h
    for i in range(n):
        t = i / (n - 1)
        a = int(255 * (t * t * (3 - 2 * t)))  # smoothstep
        for j in range(h if horizontal else w):
            if horizontal:
                px[i, j] = (255, 255, 255, a)
            else:
                px[j, i] = (255, 255, 255, a)
    img.save(path)


def textures(media: Path):
    (media / "shapes").mkdir(parents=True, exist_ok=True)
    (media / "masks").mkdir(parents=True, exist_ok=True)
    Image.new("RGBA", (8, 8), (255, 255, 255, 255)).save(media / "white.png")
    # raggi in px skin (dp * 2.75): 8dp=22, 12dp=33, 16dp=44, 20dp=55, 24dp=66, 28dp=77, 36dp=99
    for r in (22, 33, 44, 55, 66, 77, 99):
        rounded(2 * r + 2, 2 * r + 2, r, media / "shapes" / f"r{r}.png")
        rounded(2 * r + 2, 2 * r + 2, r, media / "shapes" / f"r{r}_o.png", stroke=3)
    rounded(400, 400, 200, media / "shapes" / "circle.png")
    rounded(400, 400, 200, media / "shapes" / "circle_o.png", stroke=6)
    # image masks (diffuse is not 9-slice: one per aspect ratio)
    rounded(400, 600, 36, media / "masks" / "poster.png")
    rounded(640, 360, 36, media / "masks" / "landscape.png")
    rounded(400, 400, 36, media / "masks" / "square.png")
    rounded(400, 400, 200, media / "masks" / "circle.png")
    switch(media / "shapes")
    rounded(17, 132, 8, media / "shapes" / "nib.png")
    # settings sliders: Kodi scales the handle by the height of the track texture (44 = 1:1)
    rounded(200, 44, 22, media / "shapes" / "slider_bar.png")
    rounded(44, 44, 22, media / "shapes" / "slider_nib.png")
    # M3 radio (20dp): ring + dot / ring only
    for name, dot in (("choice_on", True), ("choice_off", False)):
        img = Image.new("RGBA", (66 * SS, 66 * SS), (255, 255, 255, 0))
        d = ImageDraw.Draw(img)
        d.ellipse([3 * SS, 3 * SS, 63 * SS, 63 * SS], outline=(255, 255, 255, 255), width=6 * SS)
        if dot:
            d.ellipse([18 * SS, 18 * SS, 48 * SS, 48 * SS], fill=(255, 255, 255, 255))
        img.resize((66, 66), Image.LANCZOS).save(media / "shapes" / f"{name}.png")
    # invisible track as tall as the slider: Kodi scales the handle by the track height
    Image.new("RGBA", (8, 132), (255, 255, 255, 1)).save(media / "shapes" / "track_hit.png")  # M3 handle 4dp x 48dp (tall touch area)
    gradient(8, 256, media / "shapes" / "fade_v.png")
    gradient(256, 8, media / "shapes" / "fade_h.png", horizontal=True)


def codepoints(path: Path):
    cp = {}
    for line in path.read_text().splitlines():
        name, code = line.split()
        cp[name] = int(code, 16)
    return cp


def fonts(src: Path, out: Path, skin: Path):
    out.mkdir(parents=True, exist_ok=True)
    for wght, name in ((400, "Roboto-Regular.ttf"), (500, "Roboto-Medium.ttf")):
        f = TTFont(src / "roboto.ttf")
        inst = instancer.instantiateVariableFont(f, {"wght": wght, "wdth": 100})
        inst.save(out / name)
    cp = codepoints(src / "msr.codepoints")
    missing = [i for i in ICONS if i not in cp]
    if missing:
        sys.exit(f"missing icons: {missing}")
    unicodes = sorted({cp[i] for i in ICONS})
    for fill, name in ((0, "Symbols-Outline.ttf"), (1, "Symbols-Filled.ttf")):
        f = TTFont(src / "msr.ttf")
        inst = instancer.instantiateVariableFont(f, {"FILL": fill, "wght": 400, "GRAD": 0, "opsz": 24})
        tmp = out / ("_" + name)
        inst.save(tmp)
        opts = subset.Options()
        opts.layout_features = []
        opts.notdef_outline = True
        opts.name_IDs = ["*"]
        ft = TTFont(tmp)
        sub = subset.Subsetter(opts)
        sub.populate(unicodes=unicodes)
        sub.subset(ft)
        ft.save(out / name)
        tmp.unlink()
    # icon name -> XML entity table (Includes_Icons.xml)
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             "<!-- Generated by tools/gen_assets.py: icon name -> Material Symbols character -->",
             "<includes>"]
    for i in sorted(set(ICONS)):
        lines.append(f'\t<variable name="ic_{i}"><value>&#x{cp[i]:x};</value></variable>')
    lines.append("</includes>")
    (skin / "xml" / "Includes_Icons.xml").write_text("\n".join(lines) + "\n")
    (skin / "fonts" / "icons.json").write_text(json.dumps({i: f"{cp[i]:x}" for i in ICONS}, indent=0))


if __name__ == "__main__":
    src, skin = Path(sys.argv[1]), Path(sys.argv[2])
    textures(skin / "media")
    fonts(src, skin / "fonts", skin)
    print("ok")
