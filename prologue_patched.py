from manim import *
import re
import numpy as np
import random

# 0) КОНСТАНТЫ И СТИЛИ

MONO = "Consolas"
INK, MUT, GRID = BLACK, GREY_B, GREY_B

CODE_COLOR_CPP_KW = "#0057B7"
CODE_COLOR_CPP_TYPE = "#0057B7"
CODE_COLOR_ASM_MNEM = "#7A3E9D"
CODE_COLOR_ASM_REG = "#0057B7"
CODE_COLOR_NUM = "#A31515"
CODE_COLOR_COMMENT = "#888888"

HIGHLIGHT_COLOR = ORANGE          
ACTIVE_BLOCK_COLOR = YELLOW      
ACTIVE_BRACE_COLOR = YELLOW       

# 0.1) СКОРОСТЬ АНИМАЦИИ
# 1.0 = текущая скорость; 2.0 = в 2 раза быстрее 

SPEED_MISC = 0.25  
SPEED_MAIN = 0.25
SPEED_ADD  = 0.25
SPEED_F2   = 0.25
SPEED_F3   = 0.25

ARG_COLOR = BLUE
RET_ADDR_COLOR = RED
EBP_COLOR = GREEN
LOCAL_VAR_COLOR = PURPLE

STACK_W = 2.45
CELL_H = 0.27
ROWS = 24

CODE_SCALE = 0.34
LINE_VSPACE = 0.17
GAP_L = 0.55
GAP_R = 0.55

FRAME_W = config.frame_width
AVAILABLE_CODE_W = (FRAME_W - STACK_W - GAP_L - GAP_R) / 2
LEFT_WIDTH = AVAILABLE_CODE_W
RIGHT_WIDTH = AVAILABLE_CODE_W


# 1) ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ СТЕКА

def make_stack(rows=ROWS, cell_w=STACK_W, cell_h=CELL_H):
    stack_h = rows * cell_h
    outer = Rectangle(width=cell_w, height=stack_h, stroke_color=INK, stroke_width=3.0)
    cells = VGroup()
    for i in range(rows):
        r = Rectangle(width=cell_w, height=cell_h, stroke_color=GRID, stroke_width=2.0)
        r.move_to(outer.get_top() + DOWN * (i + 0.5) * cell_h)
        cells.add(r)
    return VGroup(outer, cells), cells


def text_in_cell(cell, txt, color=INK, scale=0.33):
    t = Text(txt, font=MONO, color=color).scale(scale)
    t.move_to(cell.get_center())
    return t


# 2) ПОДСВЕТКА КОДА

CPP_KW = r"\b(int|return|void|float|double|long|short|unsigned|signed|auto|const)\b"
CPP_TYPES = r"\b(bool|char|size_t)\b"

ASM_MNEM = r"\b(push|pop|mov|lea|sub|add|leave|ret|retn|call|imul|xor)\b"
ASM_REGS = r"\b(eax|ebx|ecx|edx|esi|edi|esp|ebp)\b"
HEX_DEC = r"(?<![\w])0x[0-9A-Fa-f]+|(?<![\w])\d+"


def color_tokens(line: str, is_cpp: bool) -> dict:
    t2c = {}
    if is_cpp:
        for m in re.finditer(CPP_KW, line):
            t2c[m.group(0)] = CODE_COLOR_CPP_KW
        for m in re.finditer(CPP_TYPES, line):
            t2c[m.group(0)] = CODE_COLOR_CPP_TYPE
        for m in re.finditer(HEX_DEC, line):
            t2c[m.group(0)] = CODE_COLOR_NUM
    else:
        for m in re.finditer(ASM_MNEM, line):
            t2c[m.group(0)] = CODE_COLOR_ASM_MNEM
        for m in re.finditer(ASM_REGS, line):
            t2c[m.group(0)] = CODE_COLOR_ASM_REG
        for m in re.finditer(HEX_DEC, line):
            t2c[m.group(0)] = CODE_COLOR_NUM
    return t2c


def code_block_syntax(src: str, width, max_height=None, is_cpp=True):
    raw_lines = src.splitlines()
    ref_h = Text("Ag", font=MONO, color=INK).scale(CODE_SCALE).height

    line_groups = []
    for raw in raw_lines:
        if raw.strip() == "":
            spacer = Rectangle(width=0.2, height=ref_h, stroke_opacity=0, fill_opacity=0)
            row = VGroup(spacer)
            row._is_blank = True
            line_groups.append(row)
            continue

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
            cm = Text(comment_part, font=MONO, color=CODE_COLOR_COMMENT).scale(CODE_SCALE)
            row = VGroup(code_txt, cm).arrange(RIGHT, buff=0.12, aligned_edge=UP)
        else:
            row = VGroup(code_txt)

        row._is_blank = False
        line_groups.append(row)

    block = VGroup(*line_groups).arrange(DOWN, buff=LINE_VSPACE, aligned_edge=LEFT)

    if block.width > width:
        block.scale(width / block.width)
    if max_height is not None and block.height > max_height:
        block.scale(max_height / block.height)

    bg = RoundedRectangle(width=block.width + 0.35, height=block.height + 0.35, corner_radius=0.12)
    bg.set_stroke(GREY_D, 1.2).set_fill(WHITE, 0.0)

    group = VGroup(bg, block)
    block.move_to(bg.get_center())
    return group, line_groups, raw_lines


def highlight_line(line_group, color=HIGHLIGHT_COLOR):
    if getattr(line_group, "_is_blank", False):
        return None
    rect = SurroundingRectangle(line_group, color=color, buff=0.03)
    rect.set_fill(color, 0.10).set_stroke(color, 2.0)
    rect.set_z_index(10)
    return rect


def highlight_block(lines_vgroup: VGroup, color=ACTIVE_BLOCK_COLOR, buff=0.06):
    rect = SurroundingRectangle(lines_vgroup, color=color, buff=buff)
    rect.set_fill(color, 0.08).set_stroke(color, 2.0)
    rect.set_z_index(5)  # ниже активной строки
    return rect


# 3) УКАЗАТЕЛИ 

def make_ptr(name: str, cell, side="right", length=0.33, color=INK, font=MONO):
    if side == "right":
        end = cell.get_right()
        start = end + RIGHT * length
        label_dir = RIGHT
    else:
        end = cell.get_left()
        start = end + LEFT * length
        label_dir = LEFT

    arrow = Arrow(start, end, tip_length=0.14, stroke_width=3.0, color=color)
    label = Text(name, font=font, color=color).scale(0.34)
    label.next_to(arrow, label_dir, buff=0.10).align_to(arrow, DOWN)
    return VGroup(arrow, label)


def move_ptr(ptr: VGroup, cell, side="right", length=0.33):
    arrow, label = ptr[0], ptr[1]
    if side == "right":
        end = cell.get_right()
        start = end + RIGHT * length
        label_dir = RIGHT
    else:
        end = cell.get_left()
        start = end + LEFT * length
        label_dir = LEFT

    new_arrow = Arrow(start, end, tip_length=0.14, stroke_width=3.0, color=arrow.get_color())
    new_label = label.copy()
    new_label.next_to(new_arrow, label_dir, buff=0.10).align_to(new_arrow, DOWN)

    return AnimationGroup(Transform(arrow, new_arrow), Transform(label, new_label), lag_ratio=0.0)


# 4) ПАНЕЛЬ РЕГИСТРОВ

class RegistersPanel(VGroup):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.reg_names = ["ESP", "EBP"]
        self.reg_values = {
            "ESP": Text("0x????????", font=MONO, color=INK).scale(0.34),
            "EBP": Text("0x????????", font=MONO, color=INK).scale(0.34),
        }
        self.reg_groups = {}

        reg_cells = VGroup()
        for name in self.reg_names:
            name_text = Text(name, font=MONO, color=INK, weight=BOLD).scale(0.34)
            value_text = self.reg_values[name]
            reg_line = VGroup(name_text, value_text).arrange(RIGHT, buff=0.2, aligned_edge=UP)

            rect = SurroundingRectangle(reg_line, buff=0.15)
            rect.set_stroke(INK, 1.5).set_fill(WHITE, 1.0)

            reg_group = VGroup(rect, reg_line)
            self.reg_groups[name] = reg_group
            reg_cells.add(reg_group)

        self.add(*reg_cells.arrange(DOWN, buff=0.12, aligned_edge=LEFT))
        self.to_corner(UP + RIGHT, buff=0.35)

    def update_reg(self, reg_name, new_value_hex):
        value_text = self.reg_values[reg_name]
        target = Text(new_value_hex, font=MONO, color=INK).scale(0.34)
        target.move_to(value_text.get_center())
        flash = Flash(self.reg_groups[reg_name], color=HIGHLIGHT_COLOR, flash_radius=0.28)
        return AnimationGroup(Transform(value_text, target), flash, lag_ratio=0.0)


# 5) ОСНОВНАЯ СЦЕНА

class StackDemo(Scene):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        min_base = 0x10000000 + ROWS * 4 + 0x1000
        max_base = 0xFFF00000
        self.addr_base = random.randrange(min_base, max_base, 0x10)

        self.stack_ptr = 0
        self.ebp_ptr = 0

        self.labels = {}
        self.cell_values = {}
        self.cells = None
        self.esp_ptr_obj = None
        self.ebp_ptr_obj = None
        self.registers = None

        self.cpp_lines = None
        self.cpp_raw_lines = None

        self.asm_lines = None
        self.asm_raw_lines = None
        self.asm_grp = None

        self.ebp_history = []

        self.note = None
        self.garbage_note = None

        self.cpp_focus = None

        self.speed_by_key = {
            "misc": SPEED_MISC,
            "main": SPEED_MAIN,
            "add":  SPEED_ADD,
            "f2":   SPEED_F2,
            "f3":   SPEED_F3,
        }
        self.active_speed_key = "misc"
        self.speed_key_history = []
    def _get_hex_addr(self, cell_index: int):
        addr = (self.addr_base - cell_index * 4) & 0xFFFFFFFF
        return f"0x{addr:08X}"

    def _set_speed_for_func(self, func_name: str):
        self.speed_key_history.append(getattr(self, 'active_speed_key', 'misc') or 'misc')
        key = (func_name or '').lower()
        self.active_speed_key = key if key in self.speed_by_key else 'misc'

    def _scale_time(self, seconds: float, speed_key: str | None = None) -> float:
        """Масштабирует длительность анимации под выбранную скорость."""
        key = speed_key or self.active_speed_key or 'misc'
        factor = float(self.speed_by_key.get(key, 1.0) or 1.0)
        if factor <= 0:
            factor = 1.0
        return seconds / factor

    def play(self, *anims, **kwargs):  # type: ignore[override]
        speed_key = kwargs.pop('speed_key', None)
        if 'run_time' in kwargs and kwargs['run_time'] is not None:
            kwargs['run_time'] = self._scale_time(kwargs['run_time'], speed_key=speed_key)
        return super().play(*anims, **kwargs)

    def wait(self, duration: float = 0.0, **kwargs):  # type: ignore[override]
        speed_key = kwargs.pop('speed_key', None)
        return super().wait(self._scale_time(duration, speed_key=speed_key), **kwargs)

    def _grey_out_cell_anim(self, idx: int):
        """Оставляет значение в ячейке, но красит его в серый (MUT)"""
        if idx < 0 or idx >= ROWS:
            return None
        old = self.labels[idx]
        cur = self.cell_values.get(idx, getattr(old, 'text', '?'))
        new = text_in_cell(self.cells[idx], cur, color=MUT)
        return Transform(old, new)

    def _write_cell(self, idx: int, text: str, color=INK, run_time=0.35):
        if idx < 0 or idx >= ROWS:
            return
        old = self.labels[idx]
        new = text_in_cell(self.cells[idx], text, color=color)
        self.play(Transform(old, new), run_time=run_time)
        self.labels[idx] = old
        self.cell_values[idx] = text

    def _push_to_stack(self, label_text, color, run_time=0.5):
        if self.stack_ptr >= ROWS - 1:
            raise Exception("Stack Overflow: Not enough cells for animation.")
        self.stack_ptr += 1
        cell_idx = self.stack_ptr

        old_label = self.labels[cell_idx]
        new_label = text_in_cell(self.cells[cell_idx], label_text, color=color)

        self.play(
            Transform(old_label, new_label),
            move_ptr(self.esp_ptr_obj, self.cells[cell_idx], side="right", length=0.33),
            self.registers.update_reg("ESP", self._get_hex_addr(self.stack_ptr)),
            run_time=run_time,
        )
        self.labels[cell_idx] = old_label
        self.cell_values[cell_idx] = label_text

    def _write_at_esp(self, offset_bytes: int, label: str, color, run_time=0.35):
        off_cells = offset_bytes // 4
        idx = self.stack_ptr - off_cells
        self._write_cell(idx, label, color=color, run_time=run_time)

    def _slot_local(self, off_bytes: int) -> int:
        return self.ebp_ptr + (off_bytes // 4)

    @staticmethod
    def _find_line_index(raw_lines, needle: str, occurrence: int = 1) -> int:
        """Находит индекс строки, содержащей needle.
        Поиск устойчив к разному количеству пробелов/табов 
        """
        def _norm(x: str) -> str:
            return " ".join(str(x).split())
        n = _norm(needle)
        cnt = 0
        for i, s in enumerate(raw_lines):
            if n and n in _norm(s):
                cnt += 1
                if cnt == occurrence:
                    return i
        raise ValueError(f"Line containing '{needle}' (occ={occurrence}) not found.")

    def _hl_asm(self, needle: str, occurrence: int = 1):
        idx = self._find_line_index(self.asm_raw_lines, needle, occurrence)
        return highlight_line(self.asm_lines[idx], color=HIGHLIGHT_COLOR)

    def _hl_cpp_text(self, needle: str, occurrence: int = 1, color=ACTIVE_BLOCK_COLOR):
        idx = self._find_line_index(self.cpp_raw_lines, needle, occurrence)
        return highlight_line(self.cpp_lines[idx], color=color)

    def _hl_asm_block(self, start_needle: str, end_needle: str, occ_s: int = 1, occ_e: int = 1, color=ACTIVE_BLOCK_COLOR):
        i0 = self._find_line_index(self.asm_raw_lines, start_needle, occ_s)
        i1 = self._find_line_index(self.asm_raw_lines, end_needle, occ_e)
        lo, hi = (i0, i1) if i0 <= i1 else (i1, i0)
        lines = VGroup(*self.asm_lines[lo:hi + 1])
        return highlight_block(lines, color=color)


    def _is_on_scene(self, mob) -> bool:
        if mob is None:
            return False
        for m in list(self.mobjects) + list(getattr(self, "foreground_mobjects", [])):
            if mob is m:
                return True
            try:
                if mob in m.get_family():
                    return True
            except Exception:
                pass
        return False

    def _play_cpp_focus(self, cpp_hl, *other_anims, run_time=0.18):
        anims = []
        if getattr(self, "cpp_focus", None) is not None and self.cpp_focus is not cpp_hl and self._is_on_scene(self.cpp_focus):
            anims.append(FadeOut(self.cpp_focus))
        if cpp_hl is not None:
            anims.append(FadeIn(cpp_hl))
            self.cpp_focus = cpp_hl
        else:
            self.cpp_focus = None
        anims.extend(other_anims)
        if anims:
            self.play(*anims, run_time=run_time)

    def _clear_cpp_focus(self, run_time=0.10):
        if getattr(self, "cpp_focus", None) is None:
            return
        if self._is_on_scene(self.cpp_focus):
            self.play(FadeOut(self.cpp_focus), run_time=run_time)
        self.cpp_focus = None

    def _fade_in(self, mob, run_time=0.15):
        if mob is None:
            return
        self.play(FadeIn(mob), run_time=run_time)

    def _fade_out(self, mob, run_time=0.12):
        if mob is None:
            return
        if not self._is_on_scene(mob):
            if getattr(self, 'cpp_focus', None) is mob:
                self.cpp_focus = None
            return
        self.play(FadeOut(mob), run_time=run_time)
        if getattr(self, 'cpp_focus', None) is mob:
            self.cpp_focus = None

    def _place_notes(self):
        if self.note is None or self.garbage_note is None or self.registers is None:
            return
        target_w = self.registers.width
        for mob in [self.garbage_note, self.note]:
            if mob.width > target_w:
                mob.scale(target_w / mob.width)
        notes_group = VGroup(self.garbage_note, self.note).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        notes_group.to_corner(DOWN + RIGHT, buff=0.30)

    def _switch_asm(self, new_grp: VGroup, new_lines: list, new_raw_lines: list, run_time=0.30):
        if new_grp is self.asm_grp:
            return
        old_grp = self.asm_grp
        fade_anims = [FadeOut(old_grp)]
        if getattr(self, 'cpp_focus', None) is not None and self._is_on_scene(self.cpp_focus):
            fade_anims.append(FadeOut(self.cpp_focus))
            self.cpp_focus = None
        self.play(*fade_anims, run_time=run_time)
        self.play(FadeIn(new_grp), run_time=run_time)
        self.asm_grp = new_grp
        self.asm_lines = new_lines
        self.asm_raw_lines = new_raw_lines
        self._place_notes()

    # stack frame logic 

    def _call_function(self, func_name, ret_addr_label="Ret Addr", run_time=0.55):
        self._push_to_stack(f"{ret_addr_label} ({func_name})", RET_ADDR_COLOR, run_time=run_time)

    def _prologue(self, func_name, local_bytes=0, cpp_open_occ: int | None = None):
        self._set_speed_for_func(func_name)
        cpp_brace = self._hl_cpp_text("{ // пролог", occurrence=cpp_open_occ, color=ACTIVE_BRACE_COLOR) if cpp_open_occ else None
        if local_bytes > 0:
            asm_block = self._hl_asm_block("push    ebp", "sub     esp", color=ACTIVE_BLOCK_COLOR)
        else:
            asm_block = self._hl_asm_block("push    ebp", "mov     ebp, esp", color=ACTIVE_BLOCK_COLOR)

        if cpp_brace:
            self._play_cpp_focus(cpp_brace, FadeIn(asm_block), run_time=0.18)
        else:
            self.play(FadeIn(asm_block), run_time=0.18)

        h_push = self._hl_asm("push    ebp")
        self._fade_in(h_push, run_time=0.12)
        self.ebp_history.append(self.ebp_ptr)
        self._push_to_stack(f"Old EBP ({func_name})", EBP_COLOR, run_time=0.45)
        self._fade_out(h_push, run_time=0.10)

        h_mov = self._hl_asm("mov     ebp, esp")
        self._fade_in(h_mov, run_time=0.12)
        self.ebp_ptr = self.stack_ptr
        self.play(
            move_ptr(self.ebp_ptr_obj, self.cells[self.ebp_ptr], side="right", length=0.33),
            self.registers.update_reg("EBP", self._get_hex_addr(self.ebp_ptr)),
            run_time=0.45,
        )
        self._fade_out(h_mov, run_time=0.10)

        if local_bytes > 0:
            h_sub = self._hl_asm("sub     esp")
            self._fade_in(h_sub, run_time=0.12)
            for _ in range(local_bytes // 4):
                self._push_to_stack("?", MUT, run_time=0.20)
            self._fade_out(h_sub, run_time=0.10)

        self.play(*[FadeOut(m) for m in [asm_block, cpp_brace] if m], run_time=0.12)

    def _epilogue_leave_ret(self, func_name, cpp_close_occ: int | None = None, show_asm_block: bool = True):
        """Эпилог без leave: mov esp, ebp; pop ebp; ret.
        После уменьшения стека значения остаются, но становятся серыми (MUT).
        """
        cpp_brace = self._hl_cpp_text("} // эпилог", occurrence=cpp_close_occ, color=ACTIVE_BRACE_COLOR) if cpp_close_occ else None
        asm_block = self._hl_asm_block("mov     esp, ebp", "ret", color=ACTIVE_BLOCK_COLOR) if show_asm_block else None

        if cpp_brace and asm_block:
            self._play_cpp_focus(cpp_brace, FadeIn(asm_block), run_time=0.18)
        elif cpp_brace and not asm_block:
            self._play_cpp_focus(cpp_brace, run_time=0.18)
        elif asm_block:
            self.play(FadeIn(asm_block), run_time=0.18)

        h_mov_sp = self._hl_asm("mov     esp, ebp")
        self._fade_in(h_mov_sp, run_time=0.12)

        old_sp = self.stack_ptr
        self.stack_ptr = self.ebp_ptr

        grey_anims = []
        for i in range(self.ebp_ptr + 1, old_sp + 1):
            a = self._grey_out_cell_anim(i)
            if a is not None:
                grey_anims.append(a)

        self.play(
            move_ptr(self.esp_ptr_obj, self.cells[self.stack_ptr], side="right", length=0.33),
            self.registers.update_reg("ESP", self._get_hex_addr(self.stack_ptr)),
            *grey_anims,
            run_time=0.55,
        )
        self._fade_out(h_mov_sp, run_time=0.10)

        h_pop = self._hl_asm("pop     ebp")
        self._fade_in(h_pop, run_time=0.12)

        saved_ebp_cell = self.stack_ptr
        grey_saved = self._grey_out_cell_anim(saved_ebp_cell)

        prev_ebp = self.ebp_history.pop() if self.ebp_history else 0

        self.ebp_ptr = prev_ebp
        anims_ebp = [
            move_ptr(self.ebp_ptr_obj, self.cells[self.ebp_ptr], side="right", length=0.33),
            self.registers.update_reg("EBP", self._get_hex_addr(self.ebp_ptr)),
        ]
        if grey_saved is not None:
            anims_ebp.insert(0, grey_saved)

        self.play(*anims_ebp, run_time=0.28)

        self.stack_ptr = max(0, self.stack_ptr - 1)
        self.play(
            move_ptr(self.esp_ptr_obj, self.cells[self.stack_ptr], side="right", length=0.33),
            self.registers.update_reg("ESP", self._get_hex_addr(self.stack_ptr)),
            run_time=0.27,
        )

        self._fade_out(h_pop, run_time=0.10)

        h_ret = self._hl_asm("ret")
        self._fade_in(h_ret, run_time=0.12)

        ra_cell = self.stack_ptr
        grey_ra = self._grey_out_cell_anim(ra_cell)
        self.stack_ptr = max(0, self.stack_ptr - 1)

        anims = [
            move_ptr(self.esp_ptr_obj, self.cells[self.stack_ptr], side="right", length=0.33),
            self.registers.update_reg("ESP", self._get_hex_addr(self.stack_ptr)),
        ]
        if grey_ra is not None:
            anims.insert(0, grey_ra)

        self.play(*anims, run_time=0.50)
        self._fade_out(h_ret, run_time=0.10)

        fades = [FadeOut(m) for m in [asm_block, cpp_brace] if m]
        if fades:
            self.play(*fades, run_time=0.12)

        self.active_speed_key = self.speed_key_history.pop() if getattr(self, 'speed_key_history', None) else 'misc'
    def construct(self):
        self.camera.background_color = WHITE
        LAYOUT_DOWN = 0.25

        cpp_src = """
int f3(int p)
{ // пролог
    int u = p + 1;
    return u;
} // эпилог

int f2(int x, int y)
{ // пролог
    int t = x * y;
    int r = f3(t);
    return r + 2;
} // эпилог

int add(int a, int b)
{ // пролог
    int c = a + b;
    int k = f2(c, b);
    return k;
} // эпилог

int main()
{
    int result = add(4, 8);
    return 0;
}"""

        asm_full_src = """f3:
        push    ebp
        mov     ebp, esp
        sub     esp, 8
        mov     eax, dword ptr [ebp + 8]
        add     eax, 1
        mov     dword ptr [ebp - 4], eax
        mov     eax, dword ptr [ebp - 4]
        mov     esp, ebp
        pop     ebp
        ret

f2:
        push    ebp
        mov     ebp, esp
        sub     esp, 16
        mov     eax, dword ptr [ebp + 8]
        imul    eax, dword ptr [ebp + 12]
        mov     dword ptr [ebp - 4], eax
        mov     eax, dword ptr [ebp - 4]
        mov     dword ptr [esp], eax
        call    f3
        mov     dword ptr [ebp - 8], eax
        mov     eax, dword ptr [ebp - 8]
        add     eax, 2
        mov     esp, ebp
        pop     ebp
        ret

add:
        push    ebp
        mov     ebp, esp
        sub     esp, 16
        mov     edx, dword ptr [ebp + 8]
        mov     eax, dword ptr [ebp + 12]
        add     eax, edx
        mov     dword ptr [ebp - 4], eax
        mov     eax, dword ptr [ebp - 4]
        mov     edx, dword ptr [ebp + 12]
        mov     dword ptr [esp], eax
        mov     dword ptr [esp + 4], edx
        call    f2
        mov     dword ptr [ebp - 8], eax
        mov     eax, dword ptr [ebp - 8]
        mov     esp, ebp
        pop     ebp
        ret

main:
        push    ebp
        mov     ebp, esp
        sub     esp, 16
        mov     dword ptr [esp], 4
        mov     dword ptr [esp + 4], 8
        call    add
        mov     dword ptr [ebp - 4], eax
        xor     eax, eax
        mov     esp, ebp
        pop     ebp
        ret"""

        asm_main_src = """main:
        push    ebp
        mov     ebp, esp
        sub     esp, 16
        mov     dword ptr [esp], 4
        mov     dword ptr [esp + 4], 8
        call    add
        mov     dword ptr [ebp - 4], eax
        xor     eax, eax
        mov     esp, ebp
        pop     ebp
        ret"""

        asm_add_src = """add:
        push    ebp
        mov     ebp, esp
        sub     esp, 16
        mov     edx, dword ptr [ebp + 8]
        mov     eax, dword ptr [ebp + 12]
        add     eax, edx
        mov     dword ptr [ebp - 4], eax
        mov     eax, dword ptr [ebp - 4]
        mov     edx, dword ptr [ebp + 12]
        mov     dword ptr [esp], eax
        mov     dword ptr [esp + 4], edx
        call    f2
        mov     dword ptr [ebp - 8], eax
        mov     eax, dword ptr [ebp - 8]
        mov     esp, ebp
        pop     ebp
        ret"""

        asm_f2_src = """f2:
        push    ebp
        mov     ebp, esp
        sub     esp, 16
        mov     eax, dword ptr [ebp + 8]
        imul    eax, dword ptr [ebp + 12]
        mov     dword ptr [ebp - 4], eax
        mov     eax, dword ptr [ebp - 4]
        mov     dword ptr [esp], eax
        call    f3
        mov     dword ptr [ebp - 8], eax
        mov     eax, dword ptr [ebp - 8]
        add     eax, 2
        mov     esp, ebp
        pop     ebp
        ret"""

        asm_f3_src = """f3:
        push    ebp
        mov     ebp, esp
        sub     esp, 8
        mov     eax, dword ptr [ebp + 8]
        add     eax, 1
        mov     dword ptr [ebp - 4], eax
        mov     eax, dword ptr [ebp - 4]
        mov     esp, ebp
        pop     ebp
        ret"""

        # --- геометрия / раскладка ---
        stack_grp, self.cells = make_stack()
        stack_outer = stack_grp[0]

        title = Text("STACK DEMONSTRATION (x86, 32-бит)", font=MONO, weight=BOLD, color=INK).scale(0.41)
        title.to_edge(UP, buff=0.25)

        stack_grp.move_to(ORIGIN).shift(UP * 0.05 + LEFT * 0.95)

        cpp_grp, self.cpp_lines, self.cpp_raw_lines = code_block_syntax(
            cpp_src, width=LEFT_WIDTH, max_height=stack_outer.height, is_cpp=True
        )

        asm_max_h = stack_outer.height - 1.25
        asm_full_grp, asm_full_lines, asm_full_raw = code_block_syntax(
            asm_full_src, width=RIGHT_WIDTH, max_height=asm_max_h, is_cpp=False
        )
        asm_main_grp, asm_main_lines, asm_main_raw = code_block_syntax(
            asm_main_src, width=RIGHT_WIDTH, max_height=asm_max_h, is_cpp=False
        )
        asm_add_grp, asm_add_lines, asm_add_raw = code_block_syntax(
            asm_add_src, width=RIGHT_WIDTH, max_height=asm_max_h, is_cpp=False
        )
        asm_f2_grp, asm_f2_lines, asm_f2_raw = code_block_syntax(
            asm_f2_src, width=RIGHT_WIDTH, max_height=asm_max_h, is_cpp=False
        )
        asm_f3_grp, asm_f3_lines, asm_f3_raw = code_block_syntax(
            asm_f3_src, width=RIGHT_WIDTH, max_height=asm_max_h, is_cpp=False
        )

        cpp_grp.next_to(stack_outer, LEFT, buff=GAP_L).shift(LEFT * 0.25)
        for g in [asm_full_grp, asm_main_grp, asm_add_grp, asm_f2_grp, asm_f3_grp]:
            g.next_to(stack_outer, RIGHT, buff=GAP_R)
            g.shift(RIGHT * 0.28 + UP * 0.06)

        layout_group = VGroup(
            cpp_grp,
            stack_grp,
            asm_full_grp,
            asm_main_grp,
            asm_add_grp,
            asm_f2_grp,
            asm_f3_grp,
        )
        layout_group.shift(DOWN * LAYOUT_DOWN)

        self.asm_grp = asm_full_grp
        self.asm_lines = asm_full_lines
        self.asm_raw_lines = asm_full_raw

        self.registers = RegistersPanel()
        self.registers.to_corner(UP + RIGHT, buff=0.20)
        self.registers.shift(LEFT * 0.45)

        high_addr = Text(self._get_hex_addr(0) + " (High)", font=MONO, color=INK).scale(0.30)
        high_addr.next_to(stack_outer, UP, buff=0.10)

        bit_label = Text("32 бита (ячейка)", font=MONO, color=INK).scale(0.28)
        bit_label.next_to(stack_outer, DOWN, buff=0.05)

        low_addr = Text(self._get_hex_addr(ROWS - 1) + " (Low)", font=MONO, color=INK).scale(0.30)
        low_addr.next_to(bit_label, DOWN, buff=0.05)
        low_addr.shift(UP * 0.02)

        x_arrow = (cpp_grp.get_right()[0] + stack_outer.get_left()[0]) / 2
        addr_arrow = Arrow(
            start=np.array([x_arrow, stack_outer.get_top()[1] - 0.05, 0]),
            end=np.array([x_arrow, stack_outer.get_bottom()[1] + 0.05, 0]),
            tip_length=0.13,
            stroke_width=2.2,
            color=INK,
        )
        addr_label = Text("Адреса", font=MONO, color=INK).scale(0.30)
        addr_label.next_to(addr_arrow.get_start(), UP, buff=0.03)
        addr_label.shift(DOWN * 0.05)
        addr_label.set_x(addr_arrow.get_x())

        NOTE_SCALE = 0.30
        NOTE_LINE_BUFF = 0.06

        self.note = VGroup(
            Text("* ? — неинициализ. данные", font=MONO, color=MUT).scale(NOTE_SCALE)
        ).arrange(DOWN, aligned_edge=LEFT, buff=NOTE_LINE_BUFF)

        garbage_lines = [
            # "Примечание: старые значения",
            # "физически остаются в памяти,",
            # "но после сдвига ESP/EBP",
            # "считаются неактуальными.",
        ]
        self.garbage_note = VGroup(
            *[Text(line, font=MONO, color=MUT).scale(NOTE_SCALE) for line in garbage_lines]
        ).arrange(DOWN, aligned_edge=LEFT, buff=NOTE_LINE_BUFF)

        # --- инициализация ячеек ---
        for i in range(ROWS):
            self.labels[i] = text_in_cell(self.cells[i], "?", MUT)
            self.cell_values[i] = "?"

        preset = {
            1: ("Old EBP (OS)", EBP_COLOR),
            2: ("Ret Addr (OS)", RET_ADDR_COLOR),
            3: ("Old EBP (main)", EBP_COLOR),
            4: ("result (uninit)", LOCAL_VAR_COLOR),
            5: ("?", MUT),
            6: ("?", MUT),
            7: ("?", MUT),
        }
        for idx, (txt, col) in preset.items():
            self.labels[idx] = text_in_cell(self.cells[idx], txt, col)
            self.cell_values[idx] = txt

        self.stack_ptr = 7
        self.ebp_ptr = 3
        self.ebp_history = [1]

        self.esp_ptr_obj = make_ptr("ESP", self.cells[self.stack_ptr], side="right", length=0.33, color=RED)
        self.ebp_ptr_obj = make_ptr("EBP", self.cells[self.ebp_ptr], side="right", length=0.33, color=GREEN)

        self.registers.reg_values["ESP"].become(
            Text(self._get_hex_addr(self.stack_ptr), font=MONO, color=INK).scale(0.34).move_to(self.registers.reg_values["ESP"])
        )
        self.registers.reg_values["EBP"].become(
            Text(self._get_hex_addr(self.ebp_ptr), font=MONO, color=INK).scale(0.34).move_to(self.registers.reg_values["EBP"])
        )

        # --- появление ---
        self.play(FadeIn(title, shift=DOWN * 0.15), run_time=0.5)
        self.play(FadeIn(cpp_grp), FadeIn(stack_grp), FadeIn(self.asm_grp), FadeIn(self.registers), run_time=0.7)

        self._place_notes()
        self.play(
            FadeIn(high_addr),
            FadeIn(bit_label),
            FadeIn(low_addr),
            Create(addr_arrow),
            FadeIn(addr_label),
            FadeIn(self.note),
            FadeIn(self.garbage_note),
            run_time=0.6,
        )

        self.play(*[FadeIn(v) for v in self.labels.values()], run_time=0.6)
        self.play(FadeIn(self.esp_ptr_obj), FadeIn(self.ebp_ptr_obj), run_time=0.4)
        self.wait(0.4)

        # --- main листинг ---
        self._switch_asm(asm_main_grp, asm_main_lines, asm_main_raw, run_time=0.25)

        # ======================================================================
        # main: mov [esp],4 ; mov [esp+4],8 ; call add
        # ======================================================================

        self.next_section("Main_Setup_Args")

        cpp_main_call = self._hl_cpp_text("int result = add(4, 8);")
        asm_block_main_call = self._hl_asm_block("mov     dword ptr [esp], 4", "call    add")

        self._play_cpp_focus(cpp_main_call, FadeIn(asm_block_main_call), run_time=0.20)

        h_mov_a = self._hl_asm("mov     dword ptr [esp], 4")
        self._fade_in(h_mov_a, run_time=0.12)
        self._write_at_esp(0, "4 (a)", ARG_COLOR, run_time=0.35)
        self._fade_out(h_mov_a, run_time=0.10)

        h_mov_b = self._hl_asm("mov     dword ptr [esp + 4], 8")
        self._fade_in(h_mov_b, run_time=0.12)
        self._write_at_esp(4, "8 (b)", ARG_COLOR, run_time=0.35)
        self._fade_out(h_mov_b, run_time=0.10)

        h_call_add = self._hl_asm("call    add")
        self._fade_in(h_call_add, run_time=0.15)
        self._call_function("add", run_time=0.45)
        self._fade_out(h_call_add, run_time=0.12)

        self.play(FadeOut(asm_block_main_call), run_time=0.12)

        # ======================================================================
        # add prologue + body + call f2
        # ======================================================================

        self._switch_asm(asm_add_grp, asm_add_lines, asm_add_raw, run_time=0.25)
        self._prologue("add", local_bytes=16, cpp_open_occ=3)

        # add: c = a + b
        self.next_section("Add_c")
        cpp_c = self._hl_cpp_text("int c = a + b;")
        asm_block_c = self._hl_asm_block("mov     edx, dword ptr [ebp + 8]", "mov     dword ptr [ebp - 4], eax")
        self._play_cpp_focus(cpp_c, FadeIn(asm_block_c), run_time=0.18)

        for needle in ["mov     edx, dword ptr [ebp + 8]", "mov     eax, dword ptr [ebp + 12]", "add     eax, edx"]:
            h = self._hl_asm(needle)
            self._fade_in(h, run_time=0.10)
            self._fade_out(h, run_time=0.08)

        h_store_c = self._hl_asm("mov     dword ptr [ebp - 4], eax")
        self._fade_in(h_store_c, run_time=0.12)
        self._write_cell(self._slot_local(4), "c = 12", LOCAL_VAR_COLOR, run_time=0.45)
        self.play(Flash(self.cells[self._slot_local(4)], color=HIGHLIGHT_COLOR, flash_radius=0.20), run_time=0.25)
        self._fade_out(h_store_c, run_time=0.10)

        self.play(FadeOut(asm_block_c), run_time=0.12)
        self._fade_out(cpp_c, run_time=0.12)

        # add: k = f2(c, b)
        self.next_section("Add_call_f2")
        cpp_k = self._hl_cpp_text("int k = f2(c, b);")
        asm_block_k = self._hl_asm_block("mov     eax, dword ptr [ebp - 4]", "call    f2")
        self._play_cpp_focus(cpp_k, FadeIn(asm_block_k), run_time=0.18)

        for needle in ["mov     eax, dword ptr [ebp - 4]", "mov     edx, dword ptr [ebp + 12]"]:
            h = self._hl_asm(needle)
            self._fade_in(h, run_time=0.10)
            self._fade_out(h, run_time=0.08)

        h_arg1 = self._hl_asm("mov     dword ptr [esp], eax")
        self._fade_in(h_arg1, run_time=0.12)
        self._write_at_esp(0, "12 (x)", ARG_COLOR, run_time=0.35)
        self._fade_out(h_arg1, run_time=0.10)

        h_arg2 = self._hl_asm("mov     dword ptr [esp + 4], edx")
        self._fade_in(h_arg2, run_time=0.12)
        self._write_at_esp(4, "8 (y)", ARG_COLOR, run_time=0.35)
        self._fade_out(h_arg2, run_time=0.10)

        h_call_f2 = self._hl_asm("call    f2")
        self._fade_in(h_call_f2, run_time=0.12)
        self._call_function("f2", run_time=0.45)
        self._fade_out(h_call_f2, run_time=0.10)

        self.play(FadeOut(asm_block_k), run_time=0.12)

        # ======================================================================
        # f2 prologue + body + call f3
        # ======================================================================

        self._switch_asm(asm_f2_grp, asm_f2_lines, asm_f2_raw, run_time=0.25)
        self._prologue("f2", local_bytes=16, cpp_open_occ=2)

        # self.wait(5)
        # return()

        # f2: t = x * y
        self.next_section("F2_t")
        cpp_t = self._hl_cpp_text("int t = x * y;")
        asm_block_t = self._hl_asm_block("mov     eax, dword ptr [ebp + 8]", "mov     dword ptr [ebp - 4], eax")
        self._play_cpp_focus(cpp_t, FadeIn(asm_block_t), run_time=0.18)

        for needle in ["mov     eax, dword ptr [ebp + 8]", "imul    eax, dword ptr [ebp + 12]"]:
            h = self._hl_asm(needle)
            self._fade_in(h, run_time=0.10)
            self._fade_out(h, run_time=0.08)

        h_store_t = self._hl_asm("mov     dword ptr [ebp - 4], eax")
        self._fade_in(h_store_t, run_time=0.12)
        self._write_cell(self._slot_local(4), "t = 96", LOCAL_VAR_COLOR, run_time=0.45)
        self.play(Flash(self.cells[self._slot_local(4)], color=HIGHLIGHT_COLOR, flash_radius=0.20), run_time=0.25)
        self._fade_out(h_store_t, run_time=0.10)

        self.play(FadeOut(asm_block_t), run_time=0.12)
        self._fade_out(cpp_t, run_time=0.12)

        # f2: r = f3(t)
        self.next_section("F2_call_f3")
        cpp_r = self._hl_cpp_text("int r = f3(t);")
        asm_block_r = self._hl_asm_block("mov     eax, dword ptr [ebp - 4]", "call    f3")
        self._play_cpp_focus(cpp_r, FadeIn(asm_block_r), run_time=0.18)

        h_load_t = self._hl_asm("mov     eax, dword ptr [ebp - 4]")
        self._fade_in(h_load_t, run_time=0.10)
        self._fade_out(h_load_t, run_time=0.08)

        h_pass_p = self._hl_asm("mov     dword ptr [esp], eax")
        self._fade_in(h_pass_p, run_time=0.12)
        self._write_at_esp(0, "96 (p)", ARG_COLOR, run_time=0.35)
        self._fade_out(h_pass_p, run_time=0.10)

        h_call_f3 = self._hl_asm("call    f3")
        self._fade_in(h_call_f3, run_time=0.12)
        self._call_function("f3", run_time=0.45)
        self._fade_out(h_call_f3, run_time=0.10)

        self.play(FadeOut(asm_block_r), run_time=0.12)

        # ======================================================================
        # f3 prologue + body + return
        # ======================================================================

        self._switch_asm(asm_f3_grp, asm_f3_lines, asm_f3_raw, run_time=0.25)
        self._prologue("f3", local_bytes=8, cpp_open_occ=1)

        # f3: u = p + 1
        self.next_section("F3_u")
        cpp_u = self._hl_cpp_text("int u = p + 1;")
        asm_block_u = self._hl_asm_block("mov     eax, dword ptr [ebp + 8]", "mov     dword ptr [ebp - 4], eax")
        self._play_cpp_focus(cpp_u, FadeIn(asm_block_u), run_time=0.18)

        for needle in ["mov     eax, dword ptr [ebp + 8]", "add     eax, 1"]:
            h = self._hl_asm(needle)
            self._fade_in(h, run_time=0.10)
            self._fade_out(h, run_time=0.08)

        h_store_u = self._hl_asm("mov     dword ptr [ebp - 4], eax")
        self._fade_in(h_store_u, run_time=0.12)
        self._write_cell(self._slot_local(4), "u = 97", LOCAL_VAR_COLOR, run_time=0.45)
        self.play(Flash(self.cells[self._slot_local(4)], color=HIGHLIGHT_COLOR, flash_radius=0.20), run_time=0.25)
        self._fade_out(h_store_u, run_time=0.10)

        self.play(FadeOut(asm_block_u), run_time=0.12)
        self._fade_out(cpp_u, run_time=0.12)

        # return u;
        cpp_ret_u = self._hl_cpp_text("return u;")
        asm_block_ret_u = self._hl_asm_block("mov     eax, dword ptr [ebp - 4]", "mov     eax, dword ptr [ebp - 4]")
        self._play_cpp_focus(cpp_ret_u, FadeIn(asm_block_ret_u), run_time=0.18)

        h_load_ret = self._hl_asm("mov     eax, dword ptr [ebp - 4]")
        self._fade_in(h_load_ret, run_time=0.12)
        self._fade_out(h_load_ret, run_time=0.10)

        self.play(FadeOut(asm_block_ret_u), run_time=0.12)

        self.next_section("Return_f3")
        self._epilogue_leave_ret("f3", cpp_close_occ=1)

        self._fade_out(cpp_ret_u, run_time=0.10)
        self._fade_out(cpp_r, run_time=0.10)

        # ======================================================================
        # back to f2: store r, add 2, return
        # ======================================================================

        self.next_section("F2_after_f3")
        self._switch_asm(asm_f2_grp, asm_f2_lines, asm_f2_raw, run_time=0.20)

        h_store_r = self._hl_asm("mov     dword ptr [ebp - 8], eax")
        self._fade_in(h_store_r, run_time=0.12)
        self._write_cell(self._slot_local(8), "r = 97", LOCAL_VAR_COLOR, run_time=0.40)
        self._fade_out(h_store_r, run_time=0.10)

        cpp_ret_r2 = self._hl_cpp_text("return r + 2;")
        asm_block_ret_r2 = self._hl_asm_block("mov     eax, dword ptr [ebp - 8]", "add     eax, 2")
        self._play_cpp_focus(cpp_ret_r2, FadeIn(asm_block_ret_r2), run_time=0.18)

        for needle in ["mov     eax, dword ptr [ebp - 8]", "add     eax, 2"]:
            h = self._hl_asm(needle)
            self._fade_in(h, run_time=0.10)
            self._fade_out(h, run_time=0.08)

        self.play(FadeOut(asm_block_ret_r2), run_time=0.12)

        self.next_section("Return_f2")
        self._epilogue_leave_ret("f2", cpp_close_occ=2)
        self._fade_out(cpp_ret_r2, run_time=0.10)

        # ======================================================================
        # back to add: store k, return
        # ======================================================================

        self.next_section("Add_after_f2")
        self._switch_asm(asm_add_grp, asm_add_lines, asm_add_raw, run_time=0.20)

        h_store_k = self._hl_asm("mov     dword ptr [ebp - 8], eax")
        self._fade_in(h_store_k, run_time=0.12)
        self._write_cell(self._slot_local(8), "k = 99", LOCAL_VAR_COLOR, run_time=0.40)
        self._fade_out(h_store_k, run_time=0.10)

        cpp_ret_k = self._hl_cpp_text("return k;")
        asm_block_ret_k = self._hl_asm_block("mov     eax, dword ptr [ebp - 8]", "mov     eax, dword ptr [ebp - 8]")
        self._play_cpp_focus(cpp_ret_k, FadeIn(asm_block_ret_k), run_time=0.18)

        h_load_k = self._hl_asm("mov     eax, dword ptr [ebp - 8]")
        self._fade_in(h_load_k, run_time=0.12)
        self._fade_out(h_load_k, run_time=0.10)

        self.play(FadeOut(asm_block_ret_k), run_time=0.12)

        self.next_section("Return_add")
        self._epilogue_leave_ret("add", cpp_close_occ=3)

        self._fade_out(cpp_ret_k, run_time=0.10)
        self._fade_out(cpp_k, run_time=0.10)

        # ======================================================================
        # back to main: store result, xor eax,eax, return
        # ======================================================================

        self.next_section("Main_after_add")
        self._switch_asm(asm_main_grp, asm_main_lines, asm_main_raw, run_time=0.20)

        h_store_result = self._hl_asm("mov     dword ptr [ebp - 4], eax")
        self._fade_in(h_store_result, run_time=0.12)
        self._write_cell(self._slot_local(4), "result = 99", LOCAL_VAR_COLOR, run_time=0.45)
        self._fade_out(h_store_result, run_time=0.10)

        cpp_ret0 = self._hl_cpp_text("return 0;")
        asm_block_ret0 = self._hl_asm_block("xor     eax, eax", "ret")
        self._play_cpp_focus(cpp_ret0, FadeIn(asm_block_ret0), run_time=0.18)

        self.next_section("Return_main")
        self._epilogue_leave_ret("main", cpp_close_occ=None, show_asm_block=False)

        self.play(FadeOut(asm_block_ret0), run_time=0.12)

        self._fade_out(cpp_ret0, run_time=0.10)
        self._fade_out(cpp_main_call, run_time=0.10)

        self._switch_asm(asm_full_grp, asm_full_lines, asm_full_raw, run_time=0.25)
        self.wait(1.2)
