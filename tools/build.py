#!/usr/bin/env python3
"""Build the Tinta add-ons into build/<id>.zip.

- replaces {ic:name} with the Material Symbols glyph (fails on unknown names);
- checks that every XML file is well formed and that every {ic:...}, $VAR[...], $EXP[...] and include
  in use is defined;
- writes one zip per add-on with the <id>/ folder at the root, as Kodi expects.
"""
import json
import re
import shutil
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "build"
ADDONS = ["script.tinta.colors", "skin.tinta"]
IC = re.compile(r"\{ic:([a-z0-9_]+)\}")


def fail(msg):
    sys.exit(f"ERROR: {msg}")


def check_skin(src: Path):
    icons = json.loads((src / "fonts" / "icons.json").read_text())
    xml_dir = src / "xml"
    texts = {p.name: p.read_text() for p in xml_dir.glob("*.xml")}
    defined_vars, defined_inc, used_vars, used_inc = set(), set(), {}, {}
    for name, text in texts.items():
        for m in IC.finditer(text):
            if m.group(1) not in icons:
                fail(f"{name}: unknown icon {m.group(0)} (add it to ICONS in gen_assets.py)")
        try:
            tree = ET.fromstring(IC.sub("X", text).encode())
        except ET.ParseError as exc:
            fail(f"{name}: malformed XML: {exc}")
        for el in tree.iter():
            if el.tag == "variable" and "name" in el.attrib:
                defined_vars.add(el.attrib["name"])
            if el.tag == "include" and "name" in el.attrib:
                defined_inc.add(el.attrib["name"])
            if el.tag == "include" and "name" not in el.attrib and "file" not in el.attrib:
                ref = el.attrib.get("content") or (el.text or "").strip()
                if ref:
                    used_inc.setdefault(ref, name)
        for m in re.finditer(r"\$VAR\[([A-Za-z0-9_]+)\]", text):
            used_vars.setdefault(m.group(1), name)
    for v, where in used_vars.items():
        if v not in defined_vars:
            fail(f"{where}: undefined variable $VAR[{v}]")
    for i, where in used_inc.items():
        if i not in defined_inc:
            fail(f"{where}: undefined include {i}")
    exprs = set()
    for text in texts.values():
        exprs.update(re.findall(r'<expression name="([^"]+)"', text))
    for name, text in texts.items():
        for m in re.finditer(r"\$EXP\[([A-Za-z0-9_]+)\]", text):
            if m.group(1) not in exprs:
                fail(f"{name}: undefined expression $EXP[{m.group(1)}]")
    return icons


def build_addon(addon_id):
    src = ROOT / addon_id
    out = BUILD / addon_id
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(src, out, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "icons.json"))
    if addon_id == "skin.tinta":
        icons = check_skin(src)
        for p in (out / "xml").glob("*.xml"):
            p.write_text(IC.sub(lambda m: f"&#x{icons[m.group(1)]};", p.read_text()))
    version = ET.parse(out / "addon.xml").getroot().attrib["version"]
    zpath = BUILD / f"{addon_id}.zip"
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(out.rglob("*")):
            if f.is_file():
                z.write(f, Path(addon_id) / f.relative_to(out))
    print(f"{addon_id} {version} -> {zpath.relative_to(ROOT)} ({zpath.stat().st_size // 1024} KiB)")
    return zpath


if __name__ == "__main__":
    BUILD.mkdir(exist_ok=True)
    for a in sys.argv[1:] or ADDONS:
        build_addon(a)
