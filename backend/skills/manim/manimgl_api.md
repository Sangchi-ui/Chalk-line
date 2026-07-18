# ManimGL API Notes

ManimGL (3b1b's original, `pip install manimgl`) is **not** the same library as ManimCE (`pip install manim`). Code copied from ManimCE tutorials/docs will partially break. This project uses ManimGL — verified installed in this sandbox as v1.7.2.

## Key differences from ManimCE (don't use the ManimCE names)

| Do this (ManimGL) | Not this (ManimCE-only) |
|---|---|
| `ShowCreation(mob)` | `Create(mob)` |
| `self.camera.frame` for camera moves | `self.camera.frame` doesn't exist the same way in CE; CE uses `self.play(self.camera.animate...)` differently |
| `Tex(...)`, `TexText(...)` | CE's `MathTex`/`Tex` split works differently |
| scenes run via `manimgl file.py SceneName -w` | CE uses `manim render file.py SceneName` |

Confirmed available in `manimlib.animation.creation`: `ShowCreation`, `Write`, `Uncreate`, `DrawBorderThenFill`, `ShowIncreasingSubsets`, `ShowSubmobjectsOneByOne`, `AddTextWordByWord`.

Confirmed available in `manimlib.animation.fading`: `FadeIn`, `FadeOut`, `FadeTransform`, `FadeInFromPoint`, `FadeOutToPoint`, `VFadeIn`, `VFadeOut`.

Confirmed available in `manimlib.animation.transform`: `Transform`, `ReplacementTransform`, `TransformFromCopy`, `ApplyMethod`, `ApplyFunction`, `MoveToTarget`, `Restore`, `CyclicReplace`, `Swap`.

## Core mobjects for math explainers

- `Tex(r"...")` / `TexText("...")` — LaTeX math / text. Use raw strings (`r"..."`) to avoid backslash escaping headaches.
- `Text("...")` — non-LaTeX text (faster, no LaTeX compile needed; use for titles/captions where you don't need math typesetting).
- `NumberPlane()`, `Axes()`, `ThreeDAxes()` — coordinate systems.
- `Dot`, `Line`, `Arrow`, `Circle`, `Square`, `Polygon`, `VGroup` (grouping).
- `ParametricCurve`, `FunctionGraph` — for plotting `f(x)`.
- `always_redraw(lambda: ...)` — for mobjects that need to update every frame (e.g. a dot tracking a moving point).
- `ValueTracker()` + `.add_updater()` — the standard pattern for animating a changing numeric value (e.g. sliding a parameter while everything on screen reacts).

## Camera work (this is what makes it feel "3b1b-style" rather than static)

ManimGL scenes have `self.camera.frame`, a mobject you can animate directly:

```python
self.play(self.camera.frame.animate.scale(0.5).move_to(some_mobject))
```

Use this for zoom-ins on details and pans across a diagram — a static, never-moving camera is one of the biggest tells of a "default," unpolished Manim video.

To zoom in and later return to the original framing, call `self.camera.frame.save_state()` *before* animating it, then `self.play(Restore(self.camera.frame))` to snap back. `Restore` raises `Exception: Trying to restore without having saved` if `save_state()` was skipped — an easy mistake, confirmed by testing.

## Scene structure convention

```python
from manimlib import *

class MyExplainer(Scene):
    def construct(self):
        self.intro()
        self.main_argument()
        self.conclusion()

    def intro(self):
        ...

    def main_argument(self):
        ...

    def conclusion(self):
        ...
```

Breaking `construct` into named beat-methods keeps scenes readable and makes it easy to re-render just one beat while iterating (via `-n` start/end animation index, or by temporarily commenting out other beat calls).

## Rendering entry point

```bash
LIBGL_ALWAYS_SOFTWARE=1 xvfb-run -a -s "-screen 0 1280x720x24" manimgl <file>.py <SceneName> -w [-l|-m|--hd|--uhd]
```
Output: `<cwd>/videos/<SceneName>.mp4`.
