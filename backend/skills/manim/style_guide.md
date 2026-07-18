# Style Guide: What Makes It Look "3Blue1Brown," Not "Default Manim"

A technically-correct Manim scene can still look like a tutorial demo instead of a polished explainer. These are the differences that matter.

## Color palette

Don't use raw primary colors (`RED`, `GREEN`, `BLUE` at full saturation) side by side — it reads as a default/demo look. Use ManimGL's built-in muted variants and stick to a small, consistent palette per video:

- Background: pure black (`BLACK`) or very dark gray — never white unless intentionally doing a "whiteboard" style.
- Primary accent: `BLUE_D` / `BLUE_C` for the main object of focus.
- Secondary: `YELLOW` for emphasis/highlighting (sparingly — it should mean "look here").
- Tertiary: `GREEN_C`, `MAROON_B`, `TEAL` for supporting/contrasting elements.
- Text: `WHITE` for primary text, `GREY_B`/`GREY_A` for secondary/caption text.
- Pick 3-4 colors total for a given video and reuse them consistently — e.g. if a variable is blue in scene 1, keep it blue throughout, so color becomes a visual language the viewer learns.

## Typography

- Use `TexText`/`Tex` for anything mathematical, `Text` for plain titles/captions — mixing font styles between the two (LaTeX serif vs a sans Text font) is intentional in 3b1b's style, not a bug, but keep it consistent (e.g. all math in Tex, all narration captions in one Text font).
- Keep on-screen text sparse. The narration carries the explanation; on-screen text should be short labels, key equations, or emphasis words — not paragraphs.
- Scale equations to be legible at final resolution: as a rule of thumb, a `Tex` mobject central to the scene should span roughly 1/3 to 1/2 of frame width.

## Pacing

- Vary animation `run_time`. Simple appearances: 0.5–1s. Important reveals the viewer needs to absorb: 1.5–2.5s. Don't leave everything at the 1s default — it creates a monotone rhythm.
- Use `self.wait()` deliberately after each "aha" moment — give the viewer a beat to actually look, don't rush from one animation straight into the next.
- Build complexity incrementally: introduce one new element, let it settle, then introduce the next. Avoid `self.play(*[Create(m) for m in ten_mobjects])` all at once unless the point is literally "look at all of these together."

## Camera movement

- Treat `self.camera.frame` as a storytelling tool, not just a technical option. Zoom into a sub-expression when explaining it, then zoom back out for context. Pan across a diagram left-to-right if the narration follows that order.
- Keep camera moves slow and smooth (`run_time` 1.5s+) — fast whip-pans read as accidental/broken, not stylistic, in an explainer context.

## Layout

- Respect a safe margin — don't place important content flush against frame edges (things get cropped in different aspect ratio exports and just look cramped).
- Use `VGroup(...).arrange(...)` to lay out related elements rather than hand-placing coordinates — it keeps spacing consistent and makes later edits (adding one more element) trivial.
- When comparing two things, arrange them symmetrically (side by side or stacked) rather than scattering them.

## The "default Manim" tells to avoid

- Every animation at the same 1-second `run_time`.
- Full-saturation primary colors used indiscriminately.
- Camera that never moves.
- Walls of on-screen text duplicating the narration word-for-word.
- Objects popping in with `FadeIn`/`Write` with zero variation in the entrance style across an entire video — mix entrance types (`Write` for text, `ShowCreation` for diagrams/shapes, `FadeIn` for supporting annotations) so entrances also carry meaning.
