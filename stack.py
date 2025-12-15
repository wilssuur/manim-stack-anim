from manim import *

BG = "#0b0e10"
FG = WHITE
MUTED = GREY_B
ACCENT = YELLOW
MONO = "Consolas"

CELL_W = 3.6
CELL_H = 0.5
ROWS = 9


def make_stack(rows=ROWS, cell_w=CELL_W, cell_h=CELL_H):
    height = rows * cell_h
    outer = Rectangle(width=cell_w, height=height, stroke_color=FG, stroke_width=2.5)

    cells = VGroup()
    for i in range(rows):
        r = Rectangle(width=cell_w, height=cell_h, stroke_color=GREY_B, stroke_width=1.4)
        r.move_to(outer.get_top() + DOWN * (i + 0.5) * cell_h)
        cells.add(r)

    stack = VGroup(outer, cells)
    return stack


def code_panel(src: str, title: str, width=5.4):
    lines = src.splitlines()
    para = Paragraph(*lines, alignment="left", line_spacing=0.22, font=MONO, color=FG).scale(0.36)
    para.set_width(width)

    bg = RoundedRectangle(
        width=para.width + 0.5,
        height=para.height + 0.5,
        corner_radius=0.08,
    ).set_fill("#151a1f", opacity=1.0).set_stroke(GREY_D, 1.5)

    title_text = Text(title, font=MONO, color=MUTED).scale(0.42)
    title_text.next_to(bg, UP, buff=0.18).align_to(bg, LEFT)

    group = VGroup(bg, para, title_text)
    para.move_to(bg.get_center())
    return group


class StackDemo(Scene):
    def construct(self):
        self.camera.background_color = BG

        title = Text("STACK DEMO (x86, 32-bit)", font=MONO, weight=BOLD).scale(0.6)
        title.to_edge(UP, buff=0.4)

        stack = make_stack(rows=ROWS, cell_w=CELL_W, cell_h=CELL_H)
        stack.move_to(RIGHT * 1.8)

        top_lbl = Text("High memory", font=MONO, color=MUTED).scale(0.35).next_to(stack, UP, buff=0.15)
        bot_lbl = Text("Low memory", font=MONO, color=MUTED).scale(0.35).next_to(stack, DOWN, buff=0.15)

        grow = Arrow(
            start=stack.get_top() + UP * 0.45,
            end=stack.get_bottom() + DOWN * 0.05,
            tip_length=0.2,
        ).set_stroke(ACCENT, 2.2)
        grow_txt = Text("адреса растут ↓", font=MONO, color=ACCENT).scale(0.33).next_to(grow, LEFT, buff=0.2)

        cpp_src = """int add(int a, int b) {
    int c;
    c = a + b;
    return c;
}"""
        cpp = code_panel(cpp_src, "C++").to_edge(LEFT).shift(UP * 0.2)

        asm_src = """push    ebp
mov     ebp, esp
sub     esp, 0x10

mov     eax, [ebp+0xC]    ; b
mov     edx, [ebp+0x8]    ; a
lea     eax, [edx+eax*1]  ; a+b
mov     [ebp-0x4], eax    ; c
mov     eax, [ebp-0x4]
leave
ret"""
        asm = code_panel(asm_src, "Assembly")
        asm.next_to(stack, RIGHT, buff=0.6)

        self.play(FadeIn(title, shift=DOWN * 0.2))
        self.play(FadeIn(stack, shift=UP * 0.2), FadeIn(top_lbl), FadeIn(bot_lbl))
        self.play(Create(grow), FadeIn(grow_txt, shift=LEFT * 0.2))
        self.play(FadeIn(cpp, shift=RIGHT * 0.2))
        self.play(FadeIn(asm, shift=LEFT * 0.2))
        self.wait(1.0)
