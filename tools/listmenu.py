#!/usr/bin/env python3
"""List labels and paths of the list on screen (view 50/51) from info labels, without calling the plug-in."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kodirpc

cid = sys.argv[1] if len(sys.argv) > 1 else ""
n = int(kodirpc.call("XBMC.GetInfoLabels", {"labels": ["Container.NumItems"]})["result"]["Container.NumItems"] or 0)
print("path:", kodirpc.call("XBMC.GetInfoLabels", {"labels": ["Container.FolderPath"]})["result"]["Container.FolderPath"])
labels = []
for i in range(n):
    labels += [f"Container{cid}.ListItemAbsolute({i}).Label", f"Container{cid}.ListItemAbsolute({i}).FolderPath"]
res = kodirpc.call("XBMC.GetInfoLabels", {"labels": labels})["result"] if labels else {}
for i in range(n):
    print(f"{res[labels[2*i]]} | {res[labels[2*i+1]]}")
