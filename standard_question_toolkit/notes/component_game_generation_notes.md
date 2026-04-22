# Component Game Generation Notes

## Choice Questions

- Use `AloneClickChoice` (`component_id`: `3b9b8ec3-f7d3-11ee-b9ef-8e2f78cd4bcd`) for choice options.
- Keep manual submission/judging: `levelData.judge.autoJudge = 0`.
- Choice-question levels should allow submission without requiring all choice components to be answered first: set `levelData.judge.judgeRule = 0`.
- Keep per-option answer flags in `component_data.components.tools.AloneClickChoice.anwserConfig.anwserRadio`: `1` for the correct option, `2` for incorrect options.
- Do not change the choice component's `webEditorCustomInfo` answer/judge flags unless the template changes; in the current template, each option remains both answer and judge component.
- Choice option selected state should play the same sound as the fill box active/input state. In the current template, copy `QuestionForBlank` state index `1` `source.MAudio` into `AloneClickChoice` state index `1` `source.MAudio`.

## Nine-Grid Sprite Assets

- Nine-grid metadata lives at `component_data.states[].source.MSprite.nineGrid`.
- Treat a sprite as nine-grid enabled only when `nineGrid.enable = true`.
- When replacing an enabled nine-grid sprite URL, preserve its `left`, `right`, `top`, and `bottom` values unless the replacement asset has different stretch borders.
- Current templates use nine-grid most often for blank input box states, simple numeric keyboard button states, selected choice button states, and some framed title/stem background sprites.

## Layout Rules

- Before setting coordinates, build a whole-level content model. Classify visible blocks as `stem`, `condition`, `answer_sentence`, `formula_row`, `vertical_grid`, `image_or_table`, `choice_option`, `blank`, `keyboard`, `submit`, or `utility`.
- Use `docs/layout_generation_method.md` as the source of truth for layout generation.
- Use the three-zone model: recognition zone for stem/conditions, relation zone for image/table/formula/answer sentence, operation zone for choices/keyboards/confirm.
- Do not solve layout by moving only the stem text. Consider the whole level: supporting image/table, formulas, blanks, options, keyboard, submit, and utilities.
- Do not include question numbers in user-facing stem text or option/fill text; the level-number component handles numbering.
- Do not prepend option labels such as `A.`/`B.`/`C.`/`D.` when the option already has its own visible text content; only keep option letters when they are the actual user-facing option content, such as diagram labels with no other text.
- Apply typography by text role: short stem 60 centered, long stem 50 left-aligned, condition 50, answer sentence 54, formula row 50, choice option 38.
- If text will wrap in its text box, left-align it and increase text-box height. If it fits on one line, keep it centered.
- For formula rows, size the text component width to the formula length instead of using one fixed wide text box for every row.
- When resizing formula or short fill-label text components, recalculate both the text component `x` and its matching blank component `x` so the whole row pair is centered as one group: `group_width = text_width + gap + blank_width`, text first, then gap, then blank.
- For inline fill questions, split long problems into condition line(s) plus one answer sentence.
- For inline fill questions, replace the answer phrase with 6 full-width spaces and compute the blank position from the actual wrapped line containing the placeholder.
- For image/table questions, allocate the image/table in the relation zone before finalizing stem size and answer blank position.
- For choice questions, place options in the operation zone. If a standard choice button has user-edited `MSprite.nineGrid`, propagate only the nine-grid metadata to same-resource choice buttons.
- Prefer integer score allocation for generated multi-level configs; distribute points as evenly as possible while keeping the total exactly 100.

## Fill Question Consistency

- Use the ninth question's numeric keyboard style as the standard keyboard format for all fill-question levels.
- Within one fill question, set every `QuestionForBlank.fillInteractive.numberUnit` to the maximum answer length in that question.
- Within one fill question, keep every blank input label font size consistent; use the max answer length to choose the shared size for ordinary fill boxes, and preserve the larger vertical-calculation font size for vertical boxes.
- Do not distort input boxes. Keep blank transforms at resource-native dimensions with `scaleX = 1` and `scaleY = 1`; current ordinary fill boxes use `218 x 131`, while vertical-calculation boxes use `128 x 180`.
- When ordinary fill box size changes, increase vertical row spacing as well. With the current `218 x 131` ordinary box, keep multi-row fill gaps at least about `155` px, and use larger gaps such as `220` px for two-row layouts when space allows.

## Vertical Calculation Fill Questions

- Treat vertical calculation problems as fill questions when they contain blanks.
- Do not use a static image for the vertical expression when the expression can be assembled from text and blanks.
- Put known digits, operators, and horizontal divider lines into editable text components.
- Use `QuestionForBlank` input-box components only for unknown digits/answers.
- Auto-place the text components and input boxes on an arithmetic grid so known digits and blanks align by place value.
- Place known digits and blank boxes by shared column centers; do not position text and blank boxes with separate visual offsets.
- Preserve the template input-box default dimensions for the selected fill style unless the user explicitly asks for resizing.
- Vertical calculations must be right-aligned by place value; use the ones column as the right anchor, then place tens/hundreds/thousands to the left.
- Match known digit text size to the input-box answer text size, using the fill box's current answer font size as the standard.
- Keep enough vertical spacing between the top number row, operator row, divider line, and result row; avoid letting large digit text visually touch adjacent rows.
- Operator symbols should be visually close to digit size but may be slightly smaller than digit text so they read as operators without overpowering the layout.
