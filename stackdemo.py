from manim import *
import re
import numpy as np

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
    """Создает стек (контур) и VGroup ячеек. Индекс 0 — верхняя ячейка."""
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
    """
    Панель кода: каждая строка — отдельный VGroup (для подсветки).
    Пустые строки делаем спейсерами нормальной высоты.
    Возвращаем: group, line_groups, raw_lines
    """
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
    """Подсветка одной строки. Blank-строки не подсвечиваем."""
    if getattr(line_group, "_is_blank", False):
        return None
    rect = SurroundingRectangle(line_group, color=color, buff=0.03)
    rect.set_fill(color, 0.10).set_stroke(color, 2.0)
    rect.set_z_index(10)
    return rect


# 3) УКАЗАТЕЛИ (СТРЕЛКА+ЛЕЙБЛ)

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
            "ESP": Text("0xDEADBEEF", font=MONO, color=INK).scale(0.34),
            "EBP": Text("0xCAFEBABE", font=MONO, color=INK).scale(0.34),
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
        self.stack_ptr = 0  
        self.ebp_ptr = 0   

        self.labels = {}
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

    def _get_hex_addr(self, cell_index: int):
        base = 0xDEADBEEF
        return f"0x{(base - cell_index * 4) & 0xFFFFFFFF:08X}"

    def _write_cell(self, idx: int, text: str, color=INK, run_time=0.35):
        if idx < 0 or idx >= ROWS:
            return
        old = self.labels[idx]
        new = text_in_cell(self.cells[idx], text, color=color)
        self.play(Transform(old, new), run_time=run_time)
        self.labels[idx] = old

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

    def _pop_from_stack(self, run_time=0.5):
        cell_idx = self.stack_ptr
        if cell_idx <= 0:
            return

        old_label = self.labels[cell_idx]
        new_label = text_in_cell(self.cells[cell_idx], "?", MUT)

        self.stack_ptr = max(0, self.stack_ptr - 1)

        self.play(
            Transform(old_label, new_label),
            move_ptr(self.esp_ptr_obj, self.cells[self.stack_ptr], side="right", length=0.33),
            self.registers.update_reg("ESP", self._get_hex_addr(self.stack_ptr)),
            run_time=run_time,
        )
        self.labels[cell_idx] = old_label

    def _write_at_esp(self, offset_bytes: int, label: str, color, run_time=0.35):
        """mov dword ptr [esp+offset], X : ESP НЕ меняется, меняется только память."""
        off_cells = offset_bytes // 4
        idx = self.stack_ptr - off_cells
        self._write_cell(idx, label, color=color, run_time=run_time)

    def _slot_local(self, off_bytes: int) -> int:
        """[ebp - off] (off>0) -> ниже ebp (индекс больше)"""
        return self.ebp_ptr + (off_bytes // 4)

    def _slot_arg(self, off_bytes: int) -> int:
        """[ebp + off] (off>=4) -> выше ebp (индекс меньше)"""
        return self.ebp_ptr - (off_bytes // 4)

    @staticmethod
    def _find_line_index(raw_lines, needle: str, occurrence: int = 1) -> int:
        cnt = 0
        for i, s in enumerate(raw_lines):
            if needle in s:
                cnt += 1
                if cnt == occurrence:
                    return i
        raise ValueError(f"Line containing '{needle}' (occ={occurrence}) not found.")

    def _hl_asm(self, needle: str, occurrence: int = 1):
        idx = self._find_line_index(self.asm_raw_lines, needle, occurrence)
        return highlight_line(self.asm_lines[idx])

    def _hl_cpp_text(self, needle: str, occurrence: int = 1):
        idx = self._find_line_index(self.cpp_raw_lines, needle, occurrence)
        return highlight_line(self.cpp_lines[idx])

    def _fade_in(self, mob, run_time=0.15):
        if mob is None:
            return
        self.play(FadeIn(mob), run_time=run_time)

    def _fade_out(self, mob, run_time=0.12):
        if mob is None:
            return
        self.play(FadeOut(mob), run_time=run_time)


    def _place_notes(self):
        """Примечания в правый нижний угол, с ограничением по ширине панели регистров."""
        if self.note is None or self.garbage_note is None or self.registers is None:
            return

        target_w = self.registers.width
        for mob in [self.garbage_note, self.note]:
            if mob.width > target_w:
                mob.scale(target_w / mob.width)

        notes_group = VGroup(self.garbage_note, self.note).arrange(
            DOWN, aligned_edge=LEFT, buff=0.12
        )


        notes_group.to_corner(DOWN + RIGHT, buff=0.30)

    def _switch_asm(self, new_grp: VGroup, new_lines: list, new_raw_lines: list, run_time=0.30):
        if new_grp is self.asm_grp:
            return
        old_grp = self.asm_grp
        self.play(FadeOut(old_grp), run_time=run_time)
        self.play(FadeIn(new_grp), run_time=run_time)
        self.asm_grp = new_grp
        self.asm_lines = new_lines
        self.asm_raw_lines = new_raw_lines
        self._place_notes()


    def _call_function(self, func_name, ret_addr_label="Ret Addr", run_time=0.55):
        """CALL: PUSH return address (упрощение)."""
        self._push_to_stack(f"{ret_addr_label} ({func_name})", RET_ADDR_COLOR, run_time=run_time)

    def _prologue(self, func_name, local_bytes=0):
        """push ebp; mov ebp, esp; sub esp, N"""
        h_push = self._hl_asm("push    ebp")
        self._fade_in(h_push, run_time=0.18)

        self.ebp_history.append(self.ebp_ptr)
        self._push_to_stack(f"Old EBP ({func_name})", EBP_COLOR, run_time=0.45)

        self._fade_out(h_push, run_time=0.12)

        h_mov = self._hl_asm("mov     ebp, esp")
        self._fade_in(h_mov, run_time=0.18)

        self.ebp_ptr = self.stack_ptr
        self.play(
            move_ptr(self.ebp_ptr_obj, self.cells[self.ebp_ptr], side="right", length=0.33),
            self.registers.update_reg("EBP", self._get_hex_addr(self.ebp_ptr)),
            run_time=0.45,
        )
        self._fade_out(h_mov, run_time=0.12)

        if local_bytes > 0:
            h_sub = self._hl_asm("sub     esp")
            self._fade_in(h_sub, run_time=0.18)
            for _ in range(local_bytes // 4):
                self._push_to_stack("?", MUT, run_time=0.20)
            self._fade_out(h_sub, run_time=0.12)

    def _epilogue_leave_ret(self, func_name):
        """leave; ret"""
        h_leave = self._hl_asm("leave")
        self._fade_in(h_leave, run_time=0.18)

        old_sp = self.stack_ptr
        self.stack_ptr = self.ebp_ptr

        clear_anims = []
        for i in range(self.ebp_ptr + 1, old_sp + 1):
            old = self.labels[i]
            new = text_in_cell(self.cells[i], "?", MUT)
            clear_anims.append(Transform(old, new))

        self.play(
            move_ptr(self.esp_ptr_obj, self.cells[self.stack_ptr], side="right", length=0.33),
            self.registers.update_reg("ESP", self._get_hex_addr(self.stack_ptr)),
            *clear_anims,
            run_time=0.55,
        )

        saved_ebp_cell = self.stack_ptr
        old = self.labels[saved_ebp_cell]
        new = text_in_cell(self.cells[saved_ebp_cell], "?", MUT)

        prev_ebp = self.ebp_history.pop() if self.ebp_history else 0
        self.ebp_ptr = prev_ebp
        self.stack_ptr = max(0, self.stack_ptr - 1)

        self.play(
            Transform(old, new),
            move_ptr(self.esp_ptr_obj, self.cells[self.stack_ptr], side="right", length=0.33),
            move_ptr(self.ebp_ptr_obj, self.cells[self.ebp_ptr], side="right", length=0.33),
            self.registers.update_reg("ESP", self._get_hex_addr(self.stack_ptr)),
            self.registers.update_reg("EBP", self._get_hex_addr(self.ebp_ptr)),
            run_time=0.55,
        )
        self._fade_out(h_leave, run_time=0.12)

        h_ret = self._hl_asm("ret")
        self._fade_in(h_ret, run_time=0.18)

        ra_cell = self.stack_ptr
        old = self.labels[ra_cell]
        new = text_in_cell(self.cells[ra_cell], "?", MUT)
        self.stack_ptr = max(0, self.stack_ptr - 1)

        self.play(
            Transform(old, new),
            move_ptr(self.esp_ptr_obj, self.cells[self.stack_ptr], side="right", length=0.33),
            self.registers.update_reg("ESP", self._get_hex_addr(self.stack_ptr)),
            run_time=0.50,
        )
        self._fade_out(h_ret, run_time=0.12)


    def construct(self):
        self.camera.background_color = WHITE
        LAYOUT_DOWN = 0.25

        cpp_src = """// main (вызывающий код)
int f3(int p)
{
    int u = p + 1;
    return u;
}

int f2(int x, int y)
{
    int t = x * y;
    int r = f3(t);
    return r + 2;
}

int add(int a, int b)
{
    int c = a + b;
    int k = f2(c, b);
    return k;
}

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
        leave
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
        leave
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
        leave
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
        leave
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
        leave
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
        leave
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
        leave
        ret"""

        asm_f3_src = """f3:
        push    ebp
        mov     ebp, esp
        sub     esp, 8
        mov     eax, dword ptr [ebp + 8]
        add     eax, 1
        mov     dword ptr [ebp - 4], eax
        mov     eax, dword ptr [ebp - 4]
        leave
        ret"""

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

        bit_brace = Brace(stack_outer, direction=DOWN, buff=0.05)
        bit_label = Text("32 бита (ячейка)", font=MONO, color=INK).scale(0.28)
        bit_label.next_to(bit_brace, DOWN, buff=0.02)
        bit_group = VGroup(bit_brace, bit_label)
        bit_group.shift(UP * 0.2)

        low_addr = Text(self._get_hex_addr(ROWS - 1) + " (Low)", font=MONO, color=INK).scale(0.30)
        low_addr.next_to(bit_group, DOWN, buff=0.05)
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
            "Примечание: старые значения",
            "физически остаются в памяти,",
            "но после сдвига ESP/EBP",
            "считаются неактуальными.",
        ]

        self.garbage_note = VGroup(
            *[Text(line, font=MONO, color=MUT).scale(NOTE_SCALE) for line in garbage_lines]
        ).arrange(DOWN, aligned_edge=LEFT, buff=NOTE_LINE_BUFF)

        # --- инициализация ячеек ---
        for i in range(ROWS):
            self.labels[i] = text_in_cell(self.cells[i], "?", MUT)

        # Старт: main уже вошёл и сделал sub esp,16:
        # 1: Old EBP (OS)
        # 2: Ret Addr (OS)
        # 3: Old EBP (main)   
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

        self.play(FadeIn(title, shift=DOWN * 0.15), run_time=0.5)
        self.play(FadeIn(cpp_grp), FadeIn(stack_grp), FadeIn(self.asm_grp), FadeIn(self.registers), run_time=0.7)

        self._place_notes()
        self.play(
            FadeIn(high_addr),
            FadeIn(bit_group),
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



        self._switch_asm(asm_main_grp, asm_main_lines, asm_main_raw, run_time=0.25)

        # main: mov [esp],4 ; mov [esp+4],8 ; call add

        self.next_section("Main_Setup_Args")

        cpp_main_call = self._hl_cpp_text("int result = add(4, 8);")
        self._fade_in(cpp_main_call, run_time=0.20)

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

        # add prologue + body + call f2

        self._switch_asm(asm_add_grp, asm_add_lines, asm_add_raw, run_time=0.25)
        self._prologue("add", local_bytes=16)

        self.next_section("Add_c")
        cpp_c = self._hl_cpp_text("int c = a + b;")
        self._fade_in(cpp_c, run_time=0.18)

        for needle in ["mov     edx, dword ptr [ebp + 8]", "mov     eax, dword ptr [ebp + 12]", "add     eax, edx"]:
            h = self._hl_asm(needle)
            self._fade_in(h, run_time=0.10)
            self._fade_out(h, run_time=0.08)

        h_store_c = self._hl_asm("mov     dword ptr [ebp - 4], eax")
        self._fade_in(h_store_c, run_time=0.12)
        self._write_cell(self._slot_local(4), "c = 12", LOCAL_VAR_COLOR, run_time=0.45)
        self.play(Flash(self.cells[self._slot_local(4)], color=HIGHLIGHT_COLOR, flash_radius=0.20), run_time=0.25)
        self._fade_out(h_store_c, run_time=0.10)
        self._fade_out(cpp_c, run_time=0.12)

        self.next_section("Add_call_f2")
        cpp_k = self._hl_cpp_text("int k = f2(c, b);")
        self._fade_in(cpp_k, run_time=0.18)

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

        # f2 prologue + body + call f3

        self._switch_asm(asm_f2_grp, asm_f2_lines, asm_f2_raw, run_time=0.25)
        self._prologue("f2", local_bytes=16)

        self.next_section("F2_t")
        cpp_t = self._hl_cpp_text("int t = x * y;")
        self._fade_in(cpp_t, run_time=0.18)

        for needle in ["mov     eax, dword ptr [ebp + 8]", "imul    eax, dword ptr [ebp + 12]"]:
            h = self._hl_asm(needle)
            self._fade_in(h, run_time=0.10)
            self._fade_out(h, run_time=0.08)

        h_store_t = self._hl_asm("mov     dword ptr [ebp - 4], eax")
        self._fade_in(h_store_t, run_time=0.12)
        self._write_cell(self._slot_local(4), "t = 96", LOCAL_VAR_COLOR, run_time=0.45)
        self.play(Flash(self.cells[self._slot_local(4)], color=HIGHLIGHT_COLOR, flash_radius=0.20), run_time=0.25)
        self._fade_out(h_store_t, run_time=0.10)

        self._fade_out(cpp_t, run_time=0.12)

        self.next_section("F2_call_f3")
        cpp_r = self._hl_cpp_text("int r = f3(t);")
        self._fade_in(cpp_r, run_time=0.18)

        for needle in ["mov     eax, dword ptr [ebp - 4]"]:
            h = self._hl_asm(needle)
            self._fade_in(h, run_time=0.10)
            self._fade_out(h, run_time=0.08)

        h_pass_p = self._hl_asm("mov     dword ptr [esp], eax")
        self._fade_in(h_pass_p, run_time=0.12)
        self._write_at_esp(0, "96 (p)", ARG_COLOR, run_time=0.35)
        self._fade_out(h_pass_p, run_time=0.10)

        h_call_f3 = self._hl_asm("call    f3")
        self._fade_in(h_call_f3, run_time=0.12)
        self._call_function("f3", run_time=0.45)
        self._fade_out(h_call_f3, run_time=0.10)

        # f3 prologue + body + return

        self._switch_asm(asm_f3_grp, asm_f3_lines, asm_f3_raw, run_time=0.25)
        self._prologue("f3", local_bytes=8)

        self.next_section("F3_u")
        cpp_u = self._hl_cpp_text("int u = p + 1;")
        self._fade_in(cpp_u, run_time=0.18)

        for needle in ["mov     eax, dword ptr [ebp + 8]", "add     eax, 1"]:
            h = self._hl_asm(needle)
            self._fade_in(h, run_time=0.10)
            self._fade_out(h, run_time=0.08)

        h_store_u = self._hl_asm("mov     dword ptr [ebp - 4], eax")
        self._fade_in(h_store_u, run_time=0.12)
        self._write_cell(self._slot_local(4), "u = 97", LOCAL_VAR_COLOR, run_time=0.45)
        self.play(Flash(self.cells[self._slot_local(4)], color=HIGHLIGHT_COLOR, flash_radius=0.20), run_time=0.25)
        self._fade_out(h_store_u, run_time=0.10)
        self._fade_out(cpp_u, run_time=0.12)

        cpp_ret_u = self._hl_cpp_text("return u;")
        self._fade_in(cpp_ret_u, run_time=0.18)

        h_load_ret = self._hl_asm("mov     eax, dword ptr [ebp - 4]")
        self._fade_in(h_load_ret, run_time=0.12)
        self._fade_out(h_load_ret, run_time=0.10)

        self.next_section("Return_f3")
        self._epilogue_leave_ret("f3")

        self._fade_out(cpp_ret_u, run_time=0.10)
        self._fade_out(cpp_r, run_time=0.10)

        # back to f2: store r, add 2, return

        self.next_section("F2_after_f3")
        self._switch_asm(asm_f2_grp, asm_f2_lines, asm_f2_raw, run_time=0.20)

        h_store_r = self._hl_asm("mov     dword ptr [ebp - 8], eax")
        self._fade_in(h_store_r, run_time=0.12)
        self._write_cell(self._slot_local(8), "r = 97", LOCAL_VAR_COLOR, run_time=0.40)
        self._fade_out(h_store_r, run_time=0.10)

        cpp_ret_r2 = self._hl_cpp_text("return r + 2;")
        self._fade_in(cpp_ret_r2, run_time=0.18)

        for needle in ["mov     eax, dword ptr [ebp - 8]", "add     eax, 2"]:
            h = self._hl_asm(needle)
            self._fade_in(h, run_time=0.10)
            self._fade_out(h, run_time=0.08)

        self.next_section("Return_f2")
        self._epilogue_leave_ret("f2")
        self._fade_out(cpp_ret_r2, run_time=0.10)

        # back to add: store k, return

        self.next_section("Add_after_f2")
        self._switch_asm(asm_add_grp, asm_add_lines, asm_add_raw, run_time=0.20)

        h_store_k = self._hl_asm("mov     dword ptr [ebp - 8], eax")
        self._fade_in(h_store_k, run_time=0.12)
        self._write_cell(self._slot_local(8), "k = 99", LOCAL_VAR_COLOR, run_time=0.40)
        self._fade_out(h_store_k, run_time=0.10)

        cpp_ret_k = self._hl_cpp_text("return k;")
        self._fade_in(cpp_ret_k, run_time=0.18)

        h_load_k = self._hl_asm("mov     eax, dword ptr [ebp - 8]")
        self._fade_in(h_load_k, run_time=0.12)
        self._fade_out(h_load_k, run_time=0.10)

        self.next_section("Return_add")
        self._epilogue_leave_ret("add")

        self._fade_out(cpp_ret_k, run_time=0.10)
        self._fade_out(cpp_k, run_time=0.10)

        # back to main: store result, xor eax,eax, return

        self.next_section("Main_after_add")
        self._switch_asm(asm_main_grp, asm_main_lines, asm_main_raw, run_time=0.20)

        h_store_result = self._hl_asm("mov     dword ptr [ebp - 4], eax")
        self._fade_in(h_store_result, run_time=0.12)
        self._write_cell(self._slot_local(4), "result = 99", LOCAL_VAR_COLOR, run_time=0.45)
        self._fade_out(h_store_result, run_time=0.10)

        cpp_ret0 = self._hl_cpp_text("return 0;")
        self._fade_in(cpp_ret0, run_time=0.18)

        h_xor = self._hl_asm("xor     eax, eax")
        self._fade_in(h_xor, run_time=0.12)
        self._fade_out(h_xor, run_time=0.10)

        self.next_section("Return_main")
        self._epilogue_leave_ret("main")

        self._fade_out(cpp_ret0, run_time=0.10)
        self._fade_out(cpp_main_call, run_time=0.10)

        self._switch_asm(asm_full_grp, asm_full_lines, asm_full_raw, run_time=0.25)
        self.wait(1.2)
