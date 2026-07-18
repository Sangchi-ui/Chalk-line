---
name: manim-explainer
description: Use this skill to create 3Blue1Brown-style math explainer videos with ManimGL, rendered headlessly in the sandbox, including synced narration/voiceover. Trigger whenever the user asks for a math animation, visual proof, "manim video", concept explainer video, or wants a topic (calculus, linear algebra, probability, geometry, etc.) turned into an animated video with narration. Also use this for any task involving .py Manim scene files, ManimGL scenes, or rendering math animations to .mp4. Make sure to consult this skill even if the user just describes a math idea and asks to "animate it," "visualize it," or "make a video explaining it" — don't wait for them to say "manim" explicitly.
---

# ManimGL Explainer Videos

Build polished, 3Blue1Brown-style math explainer videos: clear visual narrative, deliberate camera work, a consistent color language, and narration synced to the animation. This skill covers environment setup (already verified working in this sandbox), the production workflow, and the gotchas that break naive Manim usage.

## Environment (verified working in this sandbox)

ManimGL is not preinstalled. Set it up once per session:

```bash
pip install manimgl --break-system-packages
apt-get install -y libpango1.0-dev xvfb libgl1-mesa-dri libglx-mesa0 \
  texlive-fonts-extra dvisvgm
```

Notes learned the hard way:
- `manimpango` (a ManimGL dependency) fails to build unless `pkg-config --exists pangocairo` succeeds, which needs `libpango1.0-dev` (not just the runtime `libpango1.0-0`).
- ManimGL opens an OpenGL context even in file-writing mode (no true "headless" flag), so it needs a virtual display. Always run through Xvfb with software rendering:
  ```bash
  LIBGL_ALWAYS_SOFTWARE=1 xvfb-run -a -s "-screen 0 1280x720x24" manimgl scene.py SceneName -w --hd
  ```
- LaTeX (`Tex`, `MathTex`, `TexText`) needs `dsfont.sty` (from `texlive-fonts-extra`) and the `dvisvgm` binary. Base `texlive-latex-base` is not enough — confirm both are present before relying on Tex-heavy scenes.
- If `apt-get` reports a dpkg lock/interrupt error, run `dpkg --configure -a` and retry.
- Run one quick smoke test (a bare `Circle()` scene) before building the real one, to catch environment issues early rather than after 10 minutes of animation-writing.

## Workflow

1. **Understand the concept.** Before writing any code, work out the actual explanation: what's the core insight, what's the best visual metaphor, what's the sequence of "aha" steps. This is the same design work a human animator does on paper first. Don't skip to code.
2. **Storyboard in prose** (in your response to the user, briefly, or as code comments): list scenes/beats in order, what's on screen, what the narration says at each beat. Confirm with the user for anything longer than ~60 seconds of final video, since re-rendering full videos is slow.
3. **Write the narration script first**, beat by beat, if voiceover is wanted. Timing the animation to words (not the other way around) is what makes 3b1b-style pacing work — see `references/voiceover.md`.
4. **Write the Scene code.** See `references/style_guide.md` for camera, color, pacing, and layout conventions, and `references/manimgl_api.md` for the ManimGL-specific API (it differs from ManimCE in several important ways — don't assume ManimCE syntax works).
5. **Render at low quality first** (`-l`, 480p) to check timing and layout fast, then re-render the final at `--hd` or `--uhd` once it's right. Don't iterate at 4K — it's slow and burns time on mistakes you haven't caught yet.
6. **Add narration**: generate/obtain the voiceover audio, then mux with ffmpeg (see `references/voiceover.md`). Never bake audio into the Manim scene itself — render video and audio separately, then combine, so each can be redone independently without re-rendering the other.
7. **Deliver**: copy the final mp4 to `/mnt/user-data/outputs/` and use `present_files`.

## Quick reference: render commands

```bash
# fast draft, single scene
LIBGL_ALWAYS_SOFTWARE=1 xvfb-run -a -s "-screen 0 1280x720x24" manimgl scene.py SceneName -w -l

# final, 1080p
LIBGL_ALWAYS_SOFTWARE=1 xvfb-run -a -s "-screen 0 1280x720x24" manimgl scene.py SceneName -w --hd

# final, 4K (only once the low-quality draft is approved)
LIBGL_ALWAYS_SOFTWARE=1 xvfb-run -a -s "-screen 0 1280x720x24" manimgl scene.py SceneName -w --uhd
```

Output lands in `<working_dir>/videos/SceneName.mp4`.

## Reference files

- `references/manimgl_api.md` — ManimGL-specific API notes (ShowCreation vs Create, camera/frame animation, common mobjects), read before writing scene code.
- `references/style_guide.md` — 3b1b-style visual conventions: color palette, typography, pacing, camera moves, what makes it look "polished" vs "default."
- `references/voiceover.md` — narration workflow: scripting, TTS/audio options, syncing animation timing to speech, ffmpeg muxing commands (tested in this sandbox).
- `references/troubleshooting.md` — errors you'll hit and their fixes (LaTeX, display, common runtime errors).

## Test scenes

`scripts/smoke_test.py` contains a `Circle` scene and a `Tex` scene — run both after any fresh environment setup to confirm rendering + LaTeX work before starting real production work.
