#!/bin/sh
# Download the source (variable) fonts used by tools/gen_assets.py into third_party/fonts.
set -e
D="$(dirname "$0")/../third_party/fonts"
mkdir -p "$D"
G=https://github.com/google
curl -fsSL -o "$D/roboto.ttf" "$G/fonts/raw/main/ofl/roboto/Roboto%5Bwdth,wght%5D.ttf"
curl -fsSL -o "$D/OFL.txt" "$G/fonts/raw/main/ofl/roboto/OFL.txt"
curl -fsSL -o "$D/msr.ttf" "$G/material-design-icons/raw/master/variablefont/MaterialSymbolsRounded%5BFILL,GRAD,opsz,wght%5D.ttf"
curl -fsSL -o "$D/msr.codepoints" "$G/material-design-icons/raw/master/variablefont/MaterialSymbolsRounded%5BFILL,GRAD,opsz,wght%5D.codepoints"
curl -fsSL -o "$D/MDI_LICENSE" "$G/material-design-icons/raw/master/LICENSE"
echo "fonts in $D"
