# Troubleshooting

Every error below was actually hit and fixed while verifying this skill in the sandbox — fix in the given order if setting up fresh.

## `RequiredDependencyException: pangocairo >= 1.30.0 is required` (during `pip install manimgl`)

`pkg-config` can't find `pangocairo` because only the runtime lib is present, not headers.
```bash
apt-get install -y libpango1.0-dev
pkg-config --exists pangocairo && echo ok
```
Then retry `pip install manimgl --break-system-packages`.

## `pyglet.display.xlib.NoSuchDisplayException: Cannot connect to "None"`

ManimGL always opens an OpenGL context, even in `-w` (write-file, no window) mode. There is no true headless flag — you need a virtual X display:
```bash
apt-get install -y xvfb libgl1-mesa-dri libglx-mesa0
LIBGL_ALWAYS_SOFTWARE=1 xvfb-run -a -s "-screen 0 1280x720x24" manimgl scene.py SceneName -w
```
This applies even to just `import manimlib` in a plain Python shell for testing — wrap any manimlib import/inspection in `xvfb-run` too.

## `LatexError: LaTeX Error: File 'dsfont.sty' not found.`

Base `texlive-latex-base` doesn't include this. Install:
```bash
apt-get install -y texlive-fonts-extra
```

## `FileNotFoundError: [Errno 2] No such file or directory: 'dvisvgm'`

ManimGL converts LaTeX output to SVG via `dvisvgm`, which isn't pulled in by the texlive packages above.
```bash
apt-get install -y dvisvgm
```

## `E: Could not get lock /var/lib/dpkg/lock` / `dpkg was interrupted`

A previous `apt-get` call didn't finish cleanly (or ran concurrently). Fix and retry:
```bash
dpkg --configure -a
```

## Video renders but is silent / no audio

Expected — ManimGL never adds audio on its own. Audio is muxed in afterward with ffmpeg; see `references/voiceover.md`. Don't debug this as a Manim bug.

## `ffmpeg ... Error opening input: No such file or directory` when muxing

Almost always a path issue: ManimGL writes output to `<cwd>/videos/<SceneName>.mp4`, not the current directory. Check with `ls videos/` before assuming ffmpeg is broken.

## Scene takes a very long time / times out

- Don't render at `--uhd` while still iterating on content — use `-l` (480p) for drafts, switch to `--hd`/`--uhd` only for the final approved cut.
- LaTeX-heavy scenes (many distinct `Tex`/`TexText` calls) are slower on first render because each unique string gets compiled; ManimGL caches compiled tex, so re-renders of the same content are much faster the second time.

## Quick full environment setup (copy-paste, run once per fresh sandbox)

```bash
pip install manimgl --break-system-packages
apt-get install -y libpango1.0-dev xvfb libgl1-mesa-dri libglx-mesa0 \
  texlive-fonts-extra dvisvgm espeak-ng
dpkg --configure -a 2>/dev/null || true
pkg-config --exists pangocairo && echo "pangocairo ok"
which dvisvgm xvfb-run
```
