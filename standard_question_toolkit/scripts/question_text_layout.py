import json
import math
from pathlib import Path
from unicodedata import east_asian_width


ROOT = Path(__file__).resolve().parents[1]
CONSTANTS_PATH = ROOT / "data/layout_constants.json"


def load_question_text_rules(path=CONSTANTS_PATH):
    constants = json.loads(Path(path).read_text(encoding="utf-8"))
    return constants["question_text_labels"]


QUESTION_TEXT_RULES = load_question_text_rules()


def visual_width(value, font_size):
    total = 0.0
    for char in value:
        if char == " ":
            total += font_size * 0.45
        elif char.isascii():
            total += font_size * 0.58
        elif east_asian_width(char) in "WF":
            total += font_size
        else:
            total += font_size * 0.78
    return total


def count_label_chars(value):
    return sum(1 for char in value.replace("\n", "") if char)


def split_question_text(value, max_chars):
    text = " ".join(str(value).split())
    if count_label_chars(text) <= max_chars:
        return [text]

    target = min(max_chars, max(1, math.ceil(count_label_chars(text) / 2)))
    break_chars = "，。；、：,.!?！？"
    candidates = []
    visible_count = 0
    for index, char in enumerate(text):
        visible_count += 1
        if char in break_chars and 4 <= visible_count <= max_chars:
            candidates.append((index + 1, visible_count))

    if candidates:
        split_index, _ = min(candidates, key=lambda item: abs(item[1] - target))
    else:
        visible_count = 0
        split_index = len(text)
        for index, char in enumerate(text):
            visible_count += 1
            if visible_count >= target:
                split_index = index + 1
                break

    first = text[:split_index].strip()
    second = text[split_index:].strip()
    return [line for line in (first, second) if line]


def get_question_label_specs(value, profile, font_size=None, center_x=0, center_y=0):
    rules = QUESTION_TEXT_RULES["profiles"][profile]
    font_size = font_size or rules["font_size"]
    max_chars = rules["max_chars"]
    line_height = rules["label_h"]
    line_gap = rules.get("line_gap", line_height)
    max_width = QUESTION_TEXT_RULES["max_text_w"]
    padding_x = QUESTION_TEXT_RULES["padding_x"]

    explicit_lines = [line.strip() for line in str(value).splitlines() if line.strip()]
    lines = explicit_lines if len(explicit_lines) > 1 else split_question_text(value, max_chars)
    align = "center" if len(lines) == 1 else "left"
    label_width = max(
        rules["min_label_w"],
        min(max_width, round(max(visual_width(line, font_size) for line in lines) + padding_x * 2)),
    )

    if len(lines) == 1:
        ys = [center_y]
    else:
        top_y = center_y + line_gap / 2
        ys = [top_y - i * line_gap for i in range(len(lines))]

    return [
        {
            "text": line,
            "x": center_x,
            "y": y,
            "w": label_width,
            "h": line_height,
            "font_size": font_size,
            "align": align,
            "line_index": index + 1,
            "line_count": len(lines),
            "max_chars": max_chars,
        }
        for index, (line, y) in enumerate(zip(lines, ys))
    ]
