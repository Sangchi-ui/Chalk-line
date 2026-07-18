# Voiceover Workflow

Narration and animation are rendered separately, then combined — never generate audio inside the Manim scene itself. This keeps the two independently redoable (fixing a line of narration shouldn't force a full video re-render, and vice versa).

## Step 1: Write the script broken into beats

Write narration as a numbered list of short lines, each tied to one animation beat:

```
1. "Let's start with a circle." — [ShowCreation(circle), 1.5s]
2. "Now watch what happens as we inscribe a square." — [ShowCreation(square), 2s]
...
```

This is the single most important step for good sync — decide the beats before writing scene code, not after.

## Step 2: Get audio for each line (or the full script)

Narration quality/voice depends on what's available:

- **Offline TTS (`espeak-ng`, installed in this sandbox)** — works with no network, but sounds robotic. Good for a *timing scratch track* while you nail animation pacing, not for a final deliverable.
  ```bash
  espeak-ng "Let's start with a circle." -w line01.wav -s 150
  ```
  `-s` = speed (words/min); slower (130-150) reads as more deliberate/explainer-like than the 175 default.
- **User-supplied audio** — if the person can record their own narration or generate it with a TTS tool of their choice (this sandbox can't reach external TTS APIs — network is restricted to package registries), have them upload the audio files and reference them directly.
- **No narration** — perfectly fine; on-screen text and pacing alone can carry an explainer. Don't force voiceover if the person didn't ask for it.

Always check duration of each line before building the scene timing:
```bash
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1 line01.wav
```

## Step 3: Time the Manim scene to the audio durations

Use the measured durations to set `run_time` / `self.wait()` so animation beats land where the corresponding line finishes, e.g. if `line01.wav` is 2.3s, give the matching animation `run_time=2.3` (or slightly less, plus a short `self.wait(0.2)` buffer) rather than guessing.

## Step 4: Render video and audio separately, then mux

1. Render the Manim scene to `.mp4` as usual (no audio).
2. Concatenate the narration lines into one full-length track matching the video length (pad gaps with silence where needed):
   ```bash
   ffmpeg -f concat -safe 0 -i lines.txt -c copy narration_full.mp3
   ```
   (`lines.txt` = `file 'line01.wav'` / `file 'silence_0.5s.wav'` / `file 'line02.wav'` etc.)
3. Mux onto the rendered video (verified working in this sandbox):
   ```bash
   ffmpeg -i videos/SceneName.mp4 -i narration_full.mp3 \
     -c:v copy -c:a aac -map 0:v:0 -map 1:a:0 -shortest \
     final_with_audio.mp4 -y
   ```
   `-c:v copy` avoids re-encoding the video (fast, no quality loss); `-shortest` trims to the shorter of the two streams — make sure video and audio lengths were actually matched in step 3 so this isn't silently cutting content.

## Generating a silence clip (for gaps/padding)

```bash
ffmpeg -f lavfi -i anullsrc=r=44100:cl=stereo -t 0.5 -q:a 9 silence_0.5s.wav -y
```
