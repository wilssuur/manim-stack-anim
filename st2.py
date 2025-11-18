from manim import *
import numpy as np

BG = "#0b0e10"
FG = WHITE
MUTED = GREY_B
ACCENT = YELLOW
MONO = "Consolas"     

def create_stack_group(rows=9, col_w=3.6, cell_h=0.5):
    height = rows * cell_h
    outer = Rectangle(width=col_w, height=height, stroke_color=FG, stroke_width=2.5)

    cells = VGroup()
    for i in range(rows):
        r = Rectangle(width=col_w, height=cell_h, stroke_color=GREY_B, stroke_width=1.4)
        r.move_to(outer.get_top() + DOWN*(i+0.5)*cell_h)
        cells.add(r)

    group = VGroup(outer, cells)

    top_label = Text("High memory", font=MONO, color=MUTED).scale(0.35).next_to(outer, UP, buff=0.15)
    bot_label = Text("Low memory", font=MONO, color=MUTED).scale(0.35).next_to(outer, DOWN, buff=0.15)

    grow = Arrow(start=outer.get_top()+UP*0.45, end=outer.get_bottom()+DOWN*0.05, tip_length=0.2).set_stroke(ACCENT, 2.2)
    grow_text = Text("адреса растут ↓", font=MONO, color=ACCENT).scale(0.33).next_to(grow, LEFT, buff=0.2)

    param_lbl = Text("Параметры", font=MONO, color=MUTED).scale(0.33)
    ret_lbl   = Text("Адрес возврата", font=MONO, color=MUTED).scale(0.33)
    param_lbl.next_to(cells[2], LEFT, buff=0.35)
    ret_lbl.next_to(cells[3], LEFT, buff=0.35)

    group.add(param_lbl, ret_lbl)
    return group, top_label, bot_label, grow, grow_text

def code_panel(text: str, title: str, width=5.2):
    lines = text.splitlines()
    para = Paragraph(*lines, alignment="left", line_spacing=0.22, font=MONO, color=FG).scale(0.36)
    para.set_width(width)

    pad_x, pad_y = 0.25, 0.25
    bg = RoundedRectangle(
        width=para.width + 2*pad_x, height=para.height + 2*pad_y, corner_radius=0.08
    ).set_fill("#151a1f", opacity=1.0).set_stroke(GREY_D, 1.5)

    title_text = Text(title, font=MONO, color=MUTED).scale(0.42)
    title_text.next_to(bg, UP, buff=0.18).align_to(bg, LEFT)

    group = VGroup(bg, para, title_text)
    para.move_to(bg.get_center())
    return group

class StackMemoryDemo(Scene):
    def construct(self):
        self.camera.background_color = BG

        stack_grp, t_lbl, b_lbl, grow, grow_txt = create_stack_group(rows=9, col_w=3.6, cell_h=0.5)
        stack_grp.move_to(RIGHT*1.8)

        cpp_code = """int add(int a, int b) {
            int c;
            c = a + b;
            return c;
        }
        """
        cpp = code_panel(cpp_code, "C++", width=5.4).scale(0.98)
        cpp.to_edge(LEFT).shift(UP*0.2)

        asm_code = """push    ebp
            mov     ebp, esp
            sub     esp, 0x10

            mov     eax, DWORD PTR [ebp+0xC]    ; b
            mov     edx, DWORD PTR [ebp+0x8]    ; a
            lea     eax, [edx+eax*1]            ; a+b
            mov     DWORD PTR [ebp-0x4], eax    ; c
            mov     eax, DWORD PTR [ebp-0x4]
            leave
            ret
        """
        asm = code_panel(asm_code, "Assembly", width=5.4).scale(0.98)
        asm.next_to(stack_grp, RIGHT, buff=0.6)

        title = Text("STACK DEMONSTRATION (x86, 32-bit)", font=MONO, weight=BOLD).scale(0.6)
        title.to_edge(UP, buff=0.4)

        self.play(FadeIn(title, shift=DOWN*0.2))
        self.play(
            FadeIn(stack_grp, shift=UP*0.2, lag_ratio=0.03),
            FadeIn(t_lbl, shift=UP*0.2),
            FadeIn(b_lbl, shift=DOWN*0.2),
        )
        self.play(Create(grow), FadeIn(grow_txt, shift=LEFT*0.2))
        self.play(FadeIn(cpp, shift=RIGHT*0.2))
        self.play(FadeIn(asm, shift=LEFT*0.2))
        self.wait(1.0)
