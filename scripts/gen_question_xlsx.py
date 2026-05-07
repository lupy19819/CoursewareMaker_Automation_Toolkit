#!/usr/bin/env python3
"""Generate question XLSX from hardcoded doc content."""
import openpyxl
from pathlib import Path

WORKDIR = Path(__file__).resolve().parents[1]

HEADERS = ["题目序号", "音频命名", "题干图片", "选项序号", "选项图片名称", "选项文本内容", "是否正确"]

# Each sheet: (sheet_name, questions)
# question: (qno, audio, stem_img, [(opt_no, opt_img, opt_text, is_correct)])

SHEETS = {
    "26春国际小班2赛跑": [
        (1,"26春国际小班2赛跑音频eyes",None,[(1,"26春国际小班2赛跑eyes",None,True),(2,"26春国际小班2赛跑nose",None,False),(3,"26春国际小班2赛跑ears",None,False)]),
        (2,"26春国际小班2赛跑音频nose",None,[(1,"26春国际小班2赛跑nose",None,True),(2,"26春国际小班2赛跑ears",None,False),(3,"26春国际小班2赛跑eyes",None,False)]),
        (3,"26春国际小班2赛跑音频ears",None,[(1,"26春国际小班2赛跑ears",None,True),(2,"26春国际小班2赛跑eyes",None,False),(3,"26春国际小班2赛跑nose",None,False)]),
        (4,"26春国际小班2赛跑音频nose",None,[(1,"26春国际小班2赛跑nose",None,True),(2,"26春国际小班2赛跑eyes",None,False),(3,"26春国际小班2赛跑ears",None,False)]),
        (5,"26春国际小班2赛跑音频ears",None,[(1,"26春国际小班2赛跑ears",None,True),(2,"26春国际小班2赛跑eyes",None,False),(3,"26春国际小班2赛跑nose",None,False)]),
        (6,"26春国际小班2赛跑音频nose",None,[(1,"26春国际小班2赛跑nose",None,True),(2,"26春国际小班2赛跑eyes",None,False),(3,"26春国际小班2赛跑ears",None,False)]),
        (7,"26春国际小班2赛跑音频eyes",None,[(1,"26春国际小班2赛跑eyes",None,True),(2,"26春国际小班2赛跑ears",None,False),(3,"26春国际小班2赛跑nose",None,False)]),
        (8,"26春国际小班2赛跑音频ears",None,[(1,"26春国际小班2赛跑ears",None,True),(2,"26春国际小班2赛跑eyes",None,False),(3,"26春国际小班2赛跑nose",None,False)]),
        (9,"26春国际小班2赛跑音频eyes",None,[(1,"26春国际小班2赛跑eyes",None,True),(2,"26春国际小班2赛跑nose",None,False),(3,"26春国际小班2赛跑ears",None,False)]),
        (10,"26春国际小班2赛跑音频nose",None,[(1,"26春国际小班2赛跑nose",None,True),(2,"26春国际小班2赛跑ears",None,False),(3,"26春国际小班2赛跑eyes",None,False)]),
    ],
    "26暑国际小班3赛车": [
        (1,"26暑国际小班3赛车音频teeth",None,[(1,"26暑国际小班3赛车teeth",None,True),(2,"26暑国际小班3赛车mouth",None,False),(3,"26暑国际小班3赛车face",None,False)]),
        (2,"26暑国际小班3赛车音频face",None,[(1,"26暑国际小班3赛车teeth",None,False),(2,"26暑国际小班3赛车face",None,True),(3,"26暑国际小班3赛车mouth",None,False)]),
        (3,"26暑国际小班3赛车音频mouth",None,[(1,"26暑国际小班3赛车face",None,False),(2,"26暑国际小班3赛车teeth",None,False),(3,"26暑国际小班3赛车mouth",None,True)]),
        (4,"26暑国际小班3赛车音频teeth",None,[(1,"26暑国际小班3赛车teeth",None,True),(2,"26暑国际小班3赛车mouth",None,False),(3,"26暑国际小班3赛车face",None,False)]),
        (5,"26暑国际小班3赛车音频face",None,[(1,"26暑国际小班3赛车teeth",None,False),(2,"26暑国际小班3赛车face",None,True),(3,"26暑国际小班3赛车mouth",None,False)]),
        (6,"26暑国际小班3赛车音频mouth",None,[(1,"26暑国际小班3赛车face",None,False),(2,"26暑国际小班3赛车teeth",None,False),(3,"26暑国际小班3赛车mouth",None,True)]),
        (7,"26暑国际小班3赛车音频face",None,[(1,"26暑国际小班3赛车teeth",None,False),(2,"26暑国际小班3赛车face",None,True),(3,"26暑国际小班3赛车mouth",None,False)]),
        (8,"26暑国际小班3赛车音频teeth",None,[(1,"26暑国际小班3赛车teeth",None,True),(2,"26暑国际小班3赛车mouth",None,False),(3,"26暑国际小班3赛车face",None,False)]),
        (9,"26暑国际小班3赛车音频face",None,[(1,"26暑国际小班3赛车teeth",None,False),(2,"26暑国际小班3赛车face",None,True),(3,"26暑国际小班3赛车mouth",None,False)]),
        (10,"26暑国际小班3赛车音频mouth",None,[(1,"26暑国际小班3赛车face",None,False),(2,"26暑国际小班3赛车teeth",None,False),(3,"26暑国际小班3赛车mouth",None,True)]),
    ],
    "26暑国际小班4游泳": [
        (1,"26暑国际小班4游泳音频hands",None,[(1,"26暑国际小班4游泳head",None,False),(2,"26暑国际小班4游泳hands",None,True),(3,"26暑国际小班4游泳feet",None,False)]),
        (2,"26暑国际小班4游泳音频head",None,[(1,"26暑国际小班4游泳feet",None,False),(2,"26暑国际小班4游泳hands",None,False),(3,"26暑国际小班4游泳head",None,True)]),
        (3,"26暑国际小班4游泳音频feet",None,[(1,"26暑国际小班4游泳head",None,False),(2,"26暑国际小班4游泳hands",None,False),(3,"26暑国际小班4游泳feet",None,True)]),
        (4,"26暑国际小班4游泳音频feet",None,[(1,"26暑国际小班4游泳feet",None,True),(2,"26暑国际小班4游泳hands",None,False),(3,"26暑国际小班4游泳head",None,False)]),
        (5,"26暑国际小班4游泳音频head",None,[(1,"26暑国际小班4游泳head",None,True),(2,"26暑国际小班4游泳hands",None,False),(3,"26暑国际小班4游泳feet",None,False)]),
        (6,"26暑国际小班4游泳音频hands",None,[(1,"26暑国际小班4游泳feet",None,False),(2,"26暑国际小班4游泳hands",None,True),(3,"26暑国际小班4游泳head",None,False)]),
        (7,"26暑国际小班4游泳音频feet",None,[(1,"26暑国际小班4游泳head",None,False),(2,"26暑国际小班4游泳feet",None,True),(3,"26暑国际小班4游泳hands",None,False)]),
        (8,"26暑国际小班4游泳音频head",None,[(1,"26暑国际小班4游泳feet",None,False),(2,"26暑国际小班4游泳hands",None,False),(3,"26暑国际小班4游泳head",None,True)]),
        (9,"26暑国际小班4游泳音频hands",None,[(1,"26暑国际小班4游泳head",None,False),(2,"26暑国际小班4游泳hands",None,True),(3,"26暑国际小班4游泳feet",None,False)]),
        (10,"26暑国际小班4游泳音频feet",None,[(1,"26暑国际小班4游泳hands",None,False),(2,"26暑国际小班4游泳feet",None,True),(3,"26暑国际小班4游泳head",None,False)]),
    ],
    "26暑国际小班5赛车": [
        (1,"26暑国际小班5赛车音频desk",None,[(1,"26暑国际小班5赛车chair",None,False),(2,"26暑国际小班5赛车desk",None,True),(3,"26暑国际小班5赛车door",None,False)]),
        (2,"26暑国际小班5赛车音频chair",None,[(1,"26暑国际小班5赛车chair",None,True),(2,"26暑国际小班5赛车door",None,False),(3,"26暑国际小班5赛车desk",None,False)]),
        (3,"26暑国际小班5赛车音频door",None,[(1,"26暑国际小班5赛车door",None,True),(2,"26暑国际小班5赛车desk",None,False),(3,"26暑国际小班5赛车chair",None,False)]),
        (4,"26暑国际小班5赛车音频chair",None,[(1,"26暑国际小班5赛车door",None,False),(2,"26暑国际小班5赛车desk",None,False),(3,"26暑国际小班5赛车chair",None,True)]),
        (5,"26暑国际小班5赛车音频door",None,[(1,"26暑国际小班5赛车chair",None,False),(2,"26暑国际小班5赛车door",None,True),(3,"26暑国际小班5赛车desk",None,False)]),
        (6,"26暑国际小班5赛车音频desk",None,[(1,"26暑国际小班5赛车door",None,False),(2,"26暑国际小班5赛车desk",None,True),(3,"26暑国际小班5赛车chair",None,False)]),
        (7,"26暑国际小班5赛车音频chair",None,[(1,"26暑国际小班5赛车chair",None,True),(2,"26暑国际小班5赛车door",None,False),(3,"26暑国际小班5赛车desk",None,False)]),
        (8,"26暑国际小班5赛车音频door",None,[(1,"26暑国际小班5赛车desk",None,False),(2,"26暑国际小班5赛车door",None,True),(3,"26暑国际小班5赛车chair",None,False)]),
        (9,"26暑国际小班5赛车音频desk",None,[(1,"26暑国际小班5赛车door",None,False),(2,"26暑国际小班5赛车desk",None,True),(3,"26暑国际小班5赛车chair",None,False)]),
        (10,"26暑国际小班5赛车音频chair",None,[(1,"26暑国际小班5赛车chair",None,True),(2,"26暑国际小班5赛车door",None,False),(3,"26暑国际小班5赛车desk",None,False)]),
    ],
    "测试小班赛车J4": [
        (1,"测试小班赛车J4赛车音频单词grandma",None,[(1,"测试小班赛车J4赛车grandma",None,True),(2,"测试小班赛车J4赛车grandpa",None,False),(3,"测试小班赛车J4赛车family",None,False)]),
        (2,"测试小班赛车J4赛车音频单词grandpa",None,[(1,"测试小班赛车J4赛车family",None,False),(2,"测试小班赛车J4赛车grandpa",None,True),(3,"测试小班赛车J4赛车grandma",None,False)]),
        (3,"测试小班赛车J4赛车音频单词family",None,[(1,"测试小班赛车J4赛车grandma",None,False),(2,"测试小班赛车J4赛车grandpa",None,False),(3,"测试小班赛车J4赛车family",None,True)]),
        (4,"测试小班赛车J4赛车音频单词family",None,[(1,"测试小班赛车J4赛车grandma",None,False),(2,"测试小班赛车J4赛车family",None,True),(3,"测试小班赛车J4赛车grandpa",None,False)]),
        (5,"测试小班赛车J4赛车音频单词grandma",None,[(1,"测试小班赛车J4赛车grandpa",None,False),(2,"测试小班赛车J4赛车family",None,False),(3,"测试小班赛车J4赛车grandma",None,True)]),
        (6,"测试小班赛车J4赛车音频单词grandpa",None,[(1,"测试小班赛车J4赛车family",None,False),(2,"测试小班赛车J4赛车grandma",None,False),(3,"测试小班赛车J4赛车grandpa",None,True)]),
        (7,"测试小班赛车J4赛车音频单词grandma",None,[(1,"测试小班赛车J4赛车grandma",None,True),(2,"测试小班赛车J4赛车grandpa",None,False),(3,"测试小班赛车J4赛车family",None,False)]),
        (8,"测试小班赛车J4赛车音频单词family",None,[(1,"测试小班赛车J4赛车grandpa",None,False),(2,"测试小班赛车J4赛车family",None,True),(3,"测试小班赛车J4赛车grandma",None,False)]),
        (9,"测试小班赛车J4赛车音频单词grandpa",None,[(1,"测试小班赛车J4赛车grandma",None,False),(2,"测试小班赛车J4赛车family",None,False),(3,"测试小班赛车J4赛车grandpa",None,True)]),
        (10,"测试小班赛车J4赛车音频单词grandma",None,[(1,"测试小班赛车J4赛车grandma",None,True),(2,"测试小班赛车J4赛车grandpa",None,False),(3,"测试小班赛车J4赛车family",None,False)]),
    ],
    "测试小班赛跑J2": [
        (1,"测试小班赛跑J2赛跑音频daddy",None,[(1,"测试小班赛跑J2赛跑mummy",None,False),(2,"测试小班赛跑J2赛跑daddy",None,True),(3,"测试小班赛跑J2赛跑baby",None,False)]),
        (2,"测试小班赛跑J2赛跑音频mummy",None,[(1,"测试小班赛跑J2赛跑mummy",None,True),(2,"测试小班赛跑J2赛跑daddy",None,False),(3,"测试小班赛跑J2赛跑baby",None,False)]),
        (3,"测试小班赛跑J2赛跑音频baby",None,[(1,"测试小班赛跑J2赛跑baby",None,True),(2,"测试小班赛跑J2赛跑daddy",None,False),(3,"测试小班赛跑J2赛跑mummy",None,False)]),
        (4,"测试小班赛跑J2赛跑音频mummy",None,[(1,"测试小班赛跑J2赛跑daddy",None,False),(2,"测试小班赛跑J2赛跑mummy",None,True),(3,"测试小班赛跑J2赛跑baby",None,False)]),
        (5,"测试小班赛跑J2赛跑音频daddy",None,[(1,"测试小班赛跑J2赛跑baby",None,False),(2,"测试小班赛跑J2赛跑mummy",None,False),(3,"测试小班赛跑J2赛跑daddy",None,True)]),
        (6,"测试小班赛跑J2赛跑音频baby",None,[(1,"测试小班赛跑J2赛跑daddy",None,False),(2,"测试小班赛跑J2赛跑mummy",None,False),(3,"测试小班赛跑J2赛跑baby",None,True)]),
        (7,"测试小班赛跑J2赛跑音频mummy",None,[(1,"测试小班赛跑J2赛跑baby",None,False),(2,"测试小班赛跑J2赛跑mummy",None,True),(3,"测试小班赛跑J2赛跑daddy",None,False)]),
        (8,"测试小班赛跑J2赛跑音频baby",None,[(1,"测试小班赛跑J2赛跑mummy",None,False),(2,"测试小班赛跑J2赛跑daddy",None,False),(3,"测试小班赛跑J2赛跑baby",None,True)]),
        (9,"测试小班赛跑J2赛跑音频daddy",None,[(1,"测试小班赛跑J2赛跑mummy",None,False),(2,"测试小班赛跑J2赛跑baby",None,False),(3,"测试小班赛跑J2赛跑daddy",None,True)]),
        (10,"测试小班赛跑J2赛跑音频baby",None,[(1,"测试小班赛跑J2赛跑daddy",None,False),(2,"测试小班赛跑J2赛跑mummy",None,False),(3,"测试小班赛跑J2赛跑baby",None,True)]),
    ],
    "测试小班游泳J3": [
        (1,"测试小班游泳J3游泳音频sister",None,[(1,"测试小班游泳J3游泳brother",None,False),(2,"测试小班游泳J3游泳sister",None,True),(3,"测试小班游泳J3游泳pet",None,False)]),
        (2,"测试小班游泳J3游泳音频brother",None,[(1,"测试小班游泳J3游泳brother",None,True),(2,"测试小班游泳J3游泳sister",None,False),(3,"测试小班游泳J3游泳pet",None,False)]),
        (3,"测试小班游泳J3游泳音频pet",None,[(1,"测试小班游泳J3游泳pet",None,True),(2,"测试小班游泳J3游泳brother",None,False),(3,"测试小班游泳J3游泳sister",None,False)]),
        (4,"测试小班游泳J3游泳音频brother",None,[(1,"测试小班游泳J3游泳sister",None,False),(2,"测试小班游泳J3游泳pet",None,False),(3,"测试小班游泳J3游泳brother",None,True)]),
        (5,"测试小班游泳J3游泳音频sister",None,[(1,"测试小班游泳J3游泳brother",None,False),(2,"测试小班游泳J3游泳sister",None,True),(3,"测试小班游泳J3游泳pet",None,False)]),
        (6,"测试小班游泳J3游泳音频pet",None,[(1,"测试小班游泳J3游泳sister",None,False),(2,"测试小班游泳J3游泳pet",None,True),(3,"测试小班游泳J3游泳brother",None,False)]),
        (7,"测试小班游泳J3游泳音频sister",None,[(1,"测试小班游泳J3游泳sister",None,True),(2,"测试小班游泳J3游泳brother",None,False),(3,"测试小班游泳J3游泳pet",None,False)]),
        (8,"测试小班游泳J3游泳音频brother",None,[(1,"测试小班游泳J3游泳pet",None,False),(2,"测试小班游泳J3游泳brother",None,True),(3,"测试小班游泳J3游泳sister",None,False)]),
        (9,"测试小班游泳J3游泳音频pet",None,[(1,"测试小班游泳J3游泳sister",None,False),(2,"测试小班游泳J3游泳pet",None,True),(3,"测试小班游泳J3游泳brother",None,False)]),
        (10,"测试小班游泳J3游泳音频sister",None,[(1,"测试小班游泳J3游泳sister",None,True),(2,"测试小班游泳J3游泳brother",None,False),(3,"测试小班游泳J3游泳pet",None,False)]),
    ],
    "测试小班游泳J1": [
        (1,"测试小班游泳J1游泳音频baby",None,[(1,"测试小班游泳J1游泳mummy",None,False),(2,"测试小班游泳J1游泳baby",None,True),(3,"测试小班游泳J1游泳daddy",None,False)]),
        (2,"测试小班游泳J1游泳音频mummy",None,[(1,"测试小班游泳J1游泳mummy",None,True),(2,"测试小班游泳J1游泳daddy",None,False),(3,"测试小班游泳J1游泳baby",None,False)]),
        (3,"测试小班游泳J1游泳音频daddy",None,[(1,"测试小班游泳J1游泳daddy",None,True),(2,"测试小班游泳J1游泳baby",None,False),(3,"测试小班游泳J1游泳mummy",None,False)]),
        (4,"测试小班游泳J1游泳音频mummy",None,[(1,"测试小班游泳J1游泳daddy",None,False),(2,"测试小班游泳J1游泳baby",None,False),(3,"测试小班游泳J1游泳mummy",None,True)]),
        (5,"测试小班游泳J1游泳音频baby",None,[(1,"测试小班游泳J1游泳mummy",None,False),(2,"测试小班游泳J1游泳baby",None,True),(3,"测试小班游泳J1游泳daddy",None,False)]),
        (6,"测试小班游泳J1游泳音频daddy",None,[(1,"测试小班游泳J1游泳baby",None,False),(2,"测试小班游泳J1游泳daddy",None,True),(3,"测试小班游泳J1游泳mummy",None,False)]),
        (7,"测试小班游泳J1游泳音频mummy",None,[(1,"测试小班游泳J1游泳mummy",None,True),(2,"测试小班游泳J1游泳baby",None,False),(3,"测试小班游泳J1游泳daddy",None,False)]),
        (8,"测试小班游泳J1游泳音频daddy",None,[(1,"测试小班游泳J1游泳baby",None,False),(2,"测试小班游泳J1游泳daddy",None,True),(3,"测试小班游泳J1游泳mummy",None,False)]),
        (9,"测试小班游泳J1游泳音频baby",None,[(1,"测试小班游泳J1游泳mummy",None,False),(2,"测试小班游泳J1游泳baby",None,True),(3,"测试小班游泳J1游泳daddy",None,False)]),
        (10,"测试小班游泳J1游泳音频baby",None,[(1,"测试小班游泳J1游泳baby",None,True),(2,"测试小班游泳J1游泳mummy",None,False),(3,"测试小班游泳J1游泳daddy",None,False)]),
    ],
}

def main():
    wb = openpyxl.Workbook()
    wb.remove(wb.active)  # remove default sheet
    for sheet_name, questions in SHEETS.items():
        ws = wb.create_sheet(title=sheet_name)
        ws.append(HEADERS)
        for q in questions:
            qno, audio, stem_img, opts = q
            for i, opt in enumerate(opts):
                opt_no, opt_img, opt_text, is_correct = opt
                row_qno = qno if i == 0 else None
                row_audio = audio if i == 0 else None
                row_stem = stem_img if i == 0 else None
                ws.append([row_qno, row_audio, row_stem, opt_no, opt_img, opt_text, "是" if is_correct else None])
    out = WORKDIR / "zhiyinlou_race_test_latest.xlsx"
    wb.save(out)
    print(f"Saved: {out}")

if __name__ == "__main__":
    main()
