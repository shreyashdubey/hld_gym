#!/usr/bin/env bash
# Record a reel and encode it. Usage: ./make.sh [reel] [dark|manim]
#   ./make.sh 03 manim
set -euo pipefail
cd "$(dirname "$0")"

REEL="${1:-01}"
THEME="${2:-dark}"
FPS=30

node shoot.mjs --frames --reel "$REEL" --fps "$FPS" --theme "$THEME"

# Grain and vignette are the whole "shot on a camera" finish; the push-in is
# already baked in by the page, so nothing here rescales and the hairlines
# survive. yuv420p because everything that plays a reel demands it.
#
# The paper cut gets a gentler finish: both effects are darkening operations,
# which is invisible on black and obvious on white — at full strength the grain
# reads as sensor noise and the vignette as a dirty scan.
if [ "$THEME" = "paper" ]; then FINISH="noise=alls=2:allf=t+u,vignette=PI/11"
else                           FINISH="noise=alls=5:allf=t+u,vignette=PI/6"; fi

ffmpeg -y -loglevel error -framerate "$FPS" -i frames-$REEL/f%04d.png \
  -vf "$FINISH,format=yuv420p" \
  -c:v libx264 -crf 18 -preset slow -movflags +faststart \
  "reel$REEL-$THEME.mp4"

# A poster frame for the page, taken from the kernel card.
ffmpeg -y -loglevel error -i "reel$REEL-$THEME.mp4" -ss 41.5 -frames:v 1 "reel$REEL-$THEME-poster.png"

# Frame 0 is the thumbnail every feed shows before anyone presses play, and it
# is what a paused player displays, so a black one reads as a broken file. This
# shipped black once already.
#
# Measure the brightest pixel, not the file size: the grain filter pushes even a
# solid black frame past 60kB, so size proves nothing. Black + grain peaks near
# 30; a frame carrying white text peaks near 235. Nothing lands in between.
# -v info, not -v error: the metadata filter prints at info level, so quieting
# ffmpeg silently swallows the measurement and the check passes on nothing.
YMAX=$(ffmpeg -v info -i "reel$REEL-$THEME.mp4" -frames:v 1 \
       -vf signalstats,metadata=print:key=lavfi.signalstats.YMAX -f null - 2>&1 \
       | grep -o 'YMAX=[0-9]*' | head -1 | cut -d= -f2)
if [ -z "$YMAX" ] || [ "$YMAX" -lt 120 ]; then
  echo "FAIL: frame 0 is blank (peak luma ${YMAX:-none}). The opening card must be visible at t=0." >&2
  exit 1
fi

# The web encode is a different job from the master. The 1080x1920 file is for
# uploading to a feed, where the platform re-encodes anyway and quality upstream
# is worth the size. This one is downloaded over mobile data by someone deciding
# whether to buy, so it is 720x1280, and it drops the grain entirely — grain is
# noise by definition, it defeats every predictor in the encoder, and at this
# size nobody can see it. 17MB becomes about 2MB.
mkdir -p ../dist/reels
ffmpeg -y -loglevel error -i "reel$REEL-$THEME.mp4" \
  -vf "scale=720:1280:flags=lanczos,format=yuv420p" \
  -c:v libx264 -crf 26 -preset slow -movflags +faststart -an \
  "../dist/reels/reel$REEL-$THEME.mp4"

echo "built reel$REEL-$THEME.mp4 ($(du -h "reel$REEL-$THEME.mp4" | cut -f1)) → web $(du -h "../dist/reels/reel$REEL-$THEME.mp4" | cut -f1), frame 0 peak luma $YMAX"
