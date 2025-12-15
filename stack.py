from manim import *

BG = "#0b0e10"
FG = WHITE
MUTED = GREY_B
ACCENT = YELLOW
ACCENT2 = ORANGE
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
    top_lbl = Text("High memory", font=MONO, color=MUTED).scale(0.35).next_to(outer, UP, buff=0.15)
    bot_lbl = Text("Low memory", font=MONO, color=MUTED).scale(0.35).next_to(outer, DOWN, buff=0.15)

    grow = Arrow(
        start=outer.get_top() + UP * 0.45,
        end=outer.get_bottom() + DOWN * 0.05,
        tip_length=0.2,
    ).set_stroke(ACCENT, 2.2)
    grow_txt = Text("адреса растут ↓", font=MONO, color=ACCENT).scale(0.33).next_to(grow, LEFT, buff=0.2)

    return stack, cells, top_lbl, bot_lbl, grow, grow_txt


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
    return group, para


class StackDemo(Scene):
    def construct(self):
        self.camera.background_color = BG

        title = Text("STACK DEMO (x86, 32-bit)", font=MONO, weight=BOLD).scale(0.6).to_edge(UP, buff=0.4)

        stack, cells, top_lbl, bot_lbl, grow, grow_txt = make_stack(rows=ROWS, cell_w=CELL_W, cell_h=CELL_H)
        stack.move_to(RIGHT * 1.8)

        cpp_src = """int add(int a, int b) {
    int c;
    c = a + b;
    return c;
}"""
        cpp, _ = code_panel(cpp_src, "C++")
        cpp.to_edge(LEFT).shift(UP * 0.2)

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
        asm, asm_para = code_panel(asm_src, "Assembly")
        asm.next_to(stack, RIGHT, buff=0.6)

        self.play(FadeIn(title, shift=DOWN * 0.2))
        self.play(FadeIn(stack, shift=UP * 0.2), FadeIn(top_lbl), FadeIn(bot_lbl))
        self.play(Create(grow), FadeIn(grow_txt, shift=LEFT * 0.2))
        self.play(FadeIn(cpp, shift=RIGHT * 0.2), FadeIn(asm, shift=LEFT * 0.2))
        self.wait(0.2)

        hl = SurroundingRectangle(asm_para[0], color=ACCENT2, buff=0.08)
        hl.set_stroke(width=2.2).set_fill(ACCENT2, opacity=0.12)
        self.play(FadeIn(hl), run_time=0.3)

        esp_idx = len(cells) - 1
        esp_cell = cells[esp_idx]
        esp_arrow = Arrow(
            start=esp_cell.get_left() + LEFT * 0.9,
            end=esp_cell.get_left(),
            tip_length=0.16,
            stroke_width=2.3,
            color=FG,
        )
        esp_label = Text("ESP", font=MONO, color=FG).scale(0.33).next_to(esp_arrow, LEFT, buff=0.12)
        self.play(FadeIn(esp_arrow), FadeIn(esp_label), run_time=0.4)

        target_idx = esp_idx - 1
        value = Text("a = 4", font=MONO).scale(0.33).move_to(cells[target_idx].get_center())
        self.play(Write(value), Flash(cells[target_idx], color=ACCENT, flash_radius=0.25), run_time=0.6)

        new_end = cells[target_idx].get_left()
        new_start = new_end + LEFT * 0.9
        self.play(
            esp_arrow.animate.put_start_and_end_on(new_start, new_end),
            esp_label.animate.next_to(esp_arrow, LEFT, buff=0.12),
            run_time=0.5,
        )

        self.play(FadeOut(hl), run_time=0.3)
        self.wait(1.0)
