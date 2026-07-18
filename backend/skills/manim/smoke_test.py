"""
Smoke test scenes for the manim-explainer skill.
Run both after any fresh environment setup, before starting real production work:

    LIBGL_ALWAYS_SOFTWARE=1 xvfb-run -a -s "-screen 0 1280x720x24" manimgl smoke_test.py BasicRenderTest -w
    LIBGL_ALWAYS_SOFTWARE=1 xvfb-run -a -s "-screen 0 1280x720x24" manimgl smoke_test.py LatexRenderTest -w

If both produce an mp4 under videos/ without errors, rendering + LaTeX are confirmed working.
"""
from manimlib import *


class BasicRenderTest(Scene):
    """Confirms basic rendering, shapes, and color pipeline work."""
    def construct(self):
        circle = Circle(color=BLUE_C)
        square = Square(color=YELLOW)
        square.next_to(circle, RIGHT)
        self.play(ShowCreation(circle))
        self.play(ShowCreation(square))
        self.wait()


class LatexRenderTest(Scene):
    """Confirms LaTeX (dsfont.sty, dvisvgm) pipeline works."""
    def construct(self):
        eq = Tex(R"e^{i\pi} + 1 = 0")
        eq.scale(2)
        self.play(Write(eq))
        self.wait()


class CameraMoveTest(Scene):
    """Confirms camera.frame animation works (used heavily in style_guide.md)."""
    def construct(self):
        dots = VGroup(*[Dot(color=BLUE_C) for _ in range(5)])
        dots.arrange(RIGHT, buff=1)
        self.play(ShowCreation(dots))
        self.camera.frame.save_state()
        self.play(self.camera.frame.animate.scale(0.5).move_to(dots[0]))
        self.wait()
        self.play(Restore(self.camera.frame))
        self.wait()
