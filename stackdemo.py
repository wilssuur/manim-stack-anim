from manim import *
import re

MONO = "Consolas"
INK, MUT, GRID = BLACK, GREY_B, GREY_B

CELL_W, CELL_H, ROWS = 2.6, 0.55, 8
LEFT_WIDTH, RIGHT_WIDTH = 5.3, 5.6
GAP_L, GAP_R = 1.6, 1.9
CODE_SCALE = 0.32
LINE_VSPACE = 0.10

CPP_KW = r"\b(int|return|void|float|double|long|short|unsigned|signed|auto|const)\b"
CPP_TYPES = r"\b(bool|char|size_t)\b"
ASM_MNEM = r"\b(push|pop|mov|lea|sub|add|leave|ret|retn|call)\b"
ASM_REGS = r"\b(eax|ebx|ecx|edx|esi|edi|esp|ebp|rax|rbx|rcx|rdx|rsp|rbp)\b"
HEX_DEC = r"(?<![\w])0x[0-9A-Fa-f]+|(?<![\w])\d+"


def make_stack(rows=ROWS, cell_w=CELL_W, cell_h=CELL_H):
    h = rows * cell_h
    outer = Rectangle(width=cell_w, height=h, stroke_color=INK, stroke_width=3.0)
    cells = VGroup()
    for i in range(rows):
        r = Rectangle(width=cell_w, height=cell_h, stroke_color=GRID, stroke_width=2.0)
        r.move_to(outer.get_top() + DOWN * (i + 0.5) * cell_h)
        cells.add(r)
    return VGroup(outer, cells), cells


def text_in_cell(cells, idx, txt, color=INK, scale=0.33):
    t = Text(txt, font=MONO, color=color).scale(scale)
    t.move_to(cells[idx].get_center())
    return t


def color_tokens(line: str, is_cpp: bool):
    t2c = {}
    if is_cpp:
        for m in re.finditer(CPP_KW, line):
            t2c[m.group(0)] = "#0057B7"
        for m in re.finditer(CPP_TYPES, line):
            t2c[m.group(0)] = "#0057B7"
        for m in re.finditer(HEX_DEC, line):
            t2c[m.group(0)] = "#A31515"
    else:
        for m in re.finditer(ASM_MNEM, line):
            t2c[m.group(0)] = "#7A3E9D"
        for m in re.finditer(ASM_REGS, line):
            t2c[m.group(0)] = "#0057B7"
        for m in re.finditer(HEX_DEC, line):
            t2c[m.group(0)] = "#A31515"
    return t2c


def code_block_syntax(src: str, width=5.8, is_cpp=True):
    lines = src.splitlines()
    line_groups = []
    for raw in lines:
        if is_cpp:
            split = raw.split("//", 1)
            code_part = split[0]
            comment_part = ("//" + split[1]) if len(split) == 2 else ""
        else:
            split = raw.split(";", 1)
            code_part = split[0]
            comment_part = (";" + split[1]) if len(split) == 2 else ""

        code_txt = Text(
            code_part if code_part else " ",
            font=MONO,
            color=INK,
            t2c=color_tokens(code_part, is_cpp),
        ).scale(CODE_SCALE)

        if comment_part:
            cm = Text(comment_part, font=MONO, color="#888888").scale(CODE_SCALE)
            row = VGroup(code_txt, cm).arrange(RIGHT, buff=0.10, aligned_edge=DOWN)
        else:
            row = VGroup(code_txt)

        line_groups.append(row)

    block = VGroup(*line_groups).arrange(DOWN, buff=LINE_VSPACE, aligned_edge=LEFT)
    if block.width > width:
        block.scale(width / block.width)

    bg = RoundedRectangle(width=block.width + 0.30, height=block.height + 0.30, corner_radius=0.10)
    bg.set_stroke(GREY_D, 1.2).set_fill(WHITE, 0.0)

    group = VGroup(bg, block)
    block.move_to(bg.get_center())
    return group, line_groups


def make_ptr(name: str, cell, side="right", length=0.55, color=INK):
    if side == "right":
        end = cell.get_right()
        start = end + RIGHT * length
        label_dir = RIGHT
    else:
        end = cell.get_left()
        start = end + LEFT * length
        label_dir = LEFT

    arrow = Arrow(start, end, tip_length=0.16, stroke_width=3.0, color=color)
    label = Text(name, font=MONO, color=color).scale(0.34)
    label.next_to(arrow, label_dir, buff=0.10).align_to(arrow, DOWN)
    return VGroup(arrow, label)


def move_ptr(ptr: VGroup, cell, side="right", length=0.55):
    arrow, label = ptr[0], ptr[1]
    if side == "right":
        end = cell.get_right()
        start = end + RIGHT * length
        label_dir = RIGHT
    else:
        end = cell.get_left()
        start = end + LEFT * length
        label_dir = LEFT

    return AnimationGroup(
        arrow.animate.put_start_and_end_on(start, end),
        label.animate.next_to(arrow, label_dir, buff=0.10).align_to(arrow, DOWN),
        lag_ratio=0.0,
    )


class StackDemo(Scene):
    def construct(self):
        self.camera.background_color = WHITE

        title = Text("STACK DEMONSTRATION (x86, 32-бит)", font=MONO, weight=BOLD, color=INK).scale(0.75)
        title.to_edge(UP, buff=0.35)

        stack, cells = make_stack()

        cpp_src = """add(x1, x2);

int add(int a, int b)
{
    int c;
    c = a + b;
    return c;
}"""
        cpp_grp, cpp_lines = code_block_syntax(cpp_src, width=LEFT_WIDTH, is_cpp=True)

        asm_src = """push    ebp
mov     ebp, esp
sub     esp, 0x10

mov     eax, DWORD PTR [ebp+0xC]    ; b
mov     edx, DWORD PTR [ebp+0x8]    ; a
lea     eax, [edx + eax*1]          ; a+b
mov     DWORD PTR [ebp-0x4], eax    ; c
mov     eax, DWORD PTR [ebp-0x4]
leave
ret"""
        asm_grp, asm_lines = code_block_syntax(asm_src, width=RIGHT_WIDTH, is_cpp=False)

        VGroup(cpp_grp, stack, asm_grp).arrange(RIGHT, buff=GAP_L)
        asm_grp.next_to(stack, RIGHT, buff=GAP_R)
        cpp_grp.next_to(stack, LEFT, buff=GAP_L)

        high = Text("High memory (100)", font=MONO, color=INK).scale(0.34).next_to(stack, UP, buff=0.18)
        high.set_x(stack.get_x())

        hi_arrow = Arrow(
            start=stack.get_top() + RIGHT * 0.55 + UP * 0.16,
            end=stack.get_top() + RIGHT * 0.55,
            tip_length=0.13,
            stroke_width=2.4,
            color=INK,
        )

        low = Text("Low memory (0)", font=MONO, color=INK).scale(0.34)
        low.next_to(stack, DOWN, buff=0.12).align_to(stack, RIGHT).shift(RIGHT * 0.2)

        brace = BraceBetweenPoints(
            stack.get_bottom() + LEFT * 0.9,
            stack.get_bottom() + RIGHT * 0.9,
            direction=DOWN,
            color=INK,
        )
        bits = Text("32 бита", font=MONO, color=INK).scale(0.34).next_to(brace, DOWN, buff=0.06)
        note = Text("* ? — неинициализ. данные", font=MONO, color=MUT).scale(0.28)
        note.next_to(low, DOWN, buff=0.08).align_to(stack, RIGHT)

        left_band_x = (cpp_grp.get_right()[0] + stack.get_left()[0]) / 2
        p_lbl = Text("Параметры", font=MONO, color=INK).scale(0.34)
        r_lbl = Text("Адрес\nвозврата", font=MONO, color=INK).scale(0.34)
        p_lbl.move_to([left_band_x, cells[3].get_center()[1], 0])
        r_lbl.move_to([left_band_x, cells[4].get_center()[1], 0])

        esp = make_ptr("ESP", cells[6], side="right", length=0.55)
        ebp = make_ptr("EBP", cells[5], side="right", length=0.55)

        labels = {
            "q7": text_in_cell(cells, 0, "?", MUT),
            "q6": text_in_cell(cells, 1, "?", MUT),
            "b": text_in_cell(cells, 2, "8"),
            "a": text_in_cell(cells, 3, "4"),
            "ret": text_in_cell(cells, 4, "return address", scale=0.30),
            "old": text_in_cell(cells, 5, "EBP"),
            "c0c": text_in_cell(cells, 6, "0xC"),
            "c": text_in_cell(cells, 7, "?", MUT),
        }

        def highlight_line(line_group, color=ORANGE):
            rect = SurroundingRectangle(line_group, color=color, buff=0.07)
            rect.set_fill(color, 0.10).set_stroke(color, 2.0)
            return rect

        self.play(FadeIn(title, shift=DOWN * 0.2), run_time=0.5)
        self.play(FadeIn(cpp_grp), FadeIn(stack), FadeIn(asm_grp), run_time=0.7)
        self.play(
            FadeIn(high),
            Create(hi_arrow),
            FadeIn(low),
            Create(brace),
            FadeIn(bits),
            FadeIn(note),
            run_time=0.6,
        )
        self.play(*[FadeIn(v) for v in labels.values()], FadeIn(p_lbl), FadeIn(r_lbl), run_time=0.7)
        self.play(FadeIn(esp), FadeIn(ebp), run_time=0.4)
        self.wait(0.2)

        h_cpp = highlight_line(cpp_lines[0])
        h_asm = highlight_line(asm_lines[0])
        self.play(FadeIn(h_cpp), FadeIn(h_asm), run_time=0.25)
        self.play(Flash(cells[4], color=YELLOW, flash_radius=0.24), run_time=0.30)
        self.play(FadeOut(h_cpp), FadeOut(h_asm), run_time=0.2)

        h_asm2 = highlight_line(asm_lines[1])
        self.play(FadeIn(h_asm2), run_time=0.2)
        self.play(move_ptr(ebp, cells[6], side="right", length=0.55), run_time=0.6)
        self.play(FadeOut(h_asm2), run_time=0.2)

        h_asm3 = highlight_line(asm_lines[2])
        self.play(FadeIn(h_asm3), run_time=0.2)
        target_idx = 2
        self.play(move_ptr(esp, cells[target_idx], side="right", length=0.55), run_time=0.7)
        for i in range(target_idx, 6):
            self.play(Flash(cells[i], color=YELLOW, flash_radius=0.22), run_time=0.10)
        self.play(FadeOut(h_asm3), run_time=0.2)

        h_cpp2 = highlight_line(cpp_lines[5])
        h_asm4 = highlight_line(asm_lines[6])
        self.play(FadeIn(h_cpp2), FadeIn(h_asm4), run_time=0.2)
        self.play(Flash(cells[5], color=YELLOW, flash_radius=0.23), run_time=0.30)
        self.play(FadeOut(h_cpp2), FadeOut(h_asm4), run_time=0.2)

        h_cpp3 = highlight_line(cpp_lines[5])
        h_asm5 = highlight_line(asm_lines[7])
        self.play(FadeIn(h_cpp3), FadeIn(h_asm5), run_time=0.2)
        c_val = text_in_cell(cells, 7, "12", INK)
        self.play(
            Transform(labels["c"], c_val),
            Flash(cells[7], color=YELLOW, flash_radius=0.22),
            run_time=0.55,
        )
        self.play(FadeOut(h_cpp3), FadeOut(h_asm5), run_time=0.2)

        self.wait(0.8)
