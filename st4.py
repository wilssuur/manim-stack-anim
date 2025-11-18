from manim import *
import numpy as np

MONO = "Consolas"   
INK  = BLACK
MUT  = GREY_B
GRID = GREY_B

CELL_W, CELL_H = 2.6, 0.55
ROWS = 8

def make_stack(rows=ROWS, cell_w=CELL_W, cell_h=CELL_H):
    h = rows * cell_h
    outer = Rectangle(width=cell_w, height=h, stroke_color=INK, stroke_width=2.5)
    cells = VGroup()
    for i in range(rows):
        r = Rectangle(width=cell_w, height=cell_h, stroke_color=GRID, stroke_width=1.6)
        r.move_to(outer.get_top() + DOWN*(i+0.5)*cell_h)
        cells.add(r)

    def put(idx, txt, scale=0.33):
        t = Text(txt, font=MONO, color=INK).scale(scale)
        t.move_to(cells[idx].get_center())
        return t

    tx8   = put(2, "8")
    tx4   = put(3, "4")
    txret = put(4, "return address", 0.30)
    txebp = put(5, "EBP", 0.33)
    tx0c  = put(6, "0xC", 0.33)

    grp = VGroup(outer, cells, tx8, tx4, txret, txebp, tx0c)
    return grp, cells

def code_block(lines: str, title: str, width=5.3):
    paras = Paragraph(*lines.splitlines(), alignment="left",
                      line_spacing=0.22, font=MONO, color=INK).scale(0.36)
    paras.set_width(width)
    ttl = Text(title, font=MONO, color=INK, weight=BOLD).scale(0.5)
    ttl.next_to(paras, UP, buff=0.18).align_to(paras, LEFT)
    grp = VGroup(paras, ttl)
    return grp, paras, ttl

class StackSixSeconds(Scene):
    def construct(self):
        self.camera.background_color = WHITE

        title = Text("STACK DEMOSTRATION (x86, 32-бит)", font=MONO,
                     weight=BOLD, color=INK).scale(0.8)
        title.to_edge(UP, buff=0.4)

        stack, cells = make_stack()
        stack.move_to(ORIGIN)

        high = Text("High memory (100)", font=MONO, color=INK).scale(0.36)
        high.next_to(stack, UP, buff=0.20)
        high.set_x(stack.get_x()) 

        hi_arrow = Arrow(
            start=stack.get_top()+RIGHT*0.6+UP*0.18,
            end=stack.get_top()+RIGHT*0.6,
            tip_length=0.15, stroke_width=2, color=INK
        )

        low = Text("Low memory (0)", font=MONO, color=INK).scale(0.36)
        low.next_to(stack, DOWN, buff=0.15).align_to(stack, RIGHT).shift(RIGHT*0.2)

        brace = BraceBetweenPoints(stack.get_bottom()+LEFT*0.9,
                                   stack.get_bottom()+RIGHT*0.9, direction=DOWN, color=INK)
        bits  = Text("32 бита", font=MONO, color=INK).scale(0.36).next_to(brace, DOWN, buff=0.08)

        p_lbl = Text("Параметры", font=MONO, color=INK).scale(0.36)
        r_lbl = Text("Адрес\nвозврата", font=MONO, color=INK).scale(0.36)
        p_lbl.next_to(cells[3], LEFT, buff=0.6)
        r_lbl.next_to(cells[4], LEFT, buff=0.6)

        esp_target = cells[-1].get_right()
        esp_arrow = Arrow(esp_target+RIGHT*0.9, esp_target, tip_length=0.16,
                          stroke_width=2.3, color=INK)
        esp_txt = Text("ESP", font=MONO, color=INK).scale(0.38).next_to(esp_arrow, RIGHT, buff=0.12)

        ebp_target = cells[5].get_right()
        ebp_arrow = Arrow(ebp_target+RIGHT*0.9, ebp_target, tip_length=0.16,
                          stroke_width=2.3, color=INK)
        ebp_txt = Text("EBP", font=MONO, color=INK).scale(0.38).next_to(ebp_arrow, RIGHT, buff=0.12)

        cpp_src = """int add(int a, int b)
            {
                int c;
                c = a + b;
                return c;
            }
        """
        cpp_grp, cpp_para, cpp_ttl = code_block(cpp_src, "C++", width=5.5)
        cpp_grp.to_edge(LEFT).align_to(stack, UP).shift(DOWN*0.2)

        asm_src = """push    ebp
            mov     ebp, esp
            sub     esp, 0x10

            mov     eax, DWORD PTR [ebp+0xC]    ; 12
            mov     edx, DWORD PTR [ebp+0x8]    ; 8
            lea     eax, [edx + eax*1]
            mov     DWORD PTR [ebp-0x4], eax
            mov     eax, DWORD PTR [ebp-0x4]
            leave
            ret
        """
        asm_grp, asm_para, asm_ttl = code_block(asm_src, "Assembly", width=5.9)
        asm_grp.align_to(stack, UP).next_to(stack, RIGHT, buff=1.2).shift(DOWN*0.2)

        self.play(FadeIn(title, shift=DOWN*0.2), run_time=0.6)                  
        self.play(FadeIn(stack, shift=UP*0.15), run_time=0.8)                   
        self.play(FadeIn(high), Create(hi_arrow), FadeIn(low), run_time=0.4)    
        self.play(FadeIn(p_lbl), FadeIn(r_lbl), Create(brace), FadeIn(bits),
                  run_time=0.6)                                                
        self.play(FadeIn(cpp_grp, shift=RIGHT*0.2),
                  FadeIn(asm_grp, shift=LEFT*0.2), run_time=1.0)                
        self.play(FadeIn(esp_arrow), FadeIn(esp_txt),
                  FadeIn(ebp_arrow), FadeIn(ebp_txt), run_time=0.8)             
        self.wait(1.8)  
