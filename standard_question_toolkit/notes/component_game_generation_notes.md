# Component Game Generation Notes

## Purpose Modes

- Decide the game purpose before generating levels. Use `diagnostic` for assessment/diagnosis and `practice` for non-diagnostic learning practice.
- Current reference configs are diagnostic by default: keep countdown, keep draft/scratchpad tools, allow unified correct/wrong feedback sounds, allow the level to switch after one wrong answer, and allow choice options, drag items, drop zones, and fill blanks to have no distinct correct/wrong visual states or to reuse the same resources.
- For non-diagnostic practice configs, remove countdown and draft/scratchpad tools, use distinct correct and wrong feedback sounds, disable wrong-answer level switching so the learner must answer correctly before progressing, and provide visibly distinct correct/wrong states for choice options, drag items/drop zones, and fill blanks.
- If a matched template only contains diagnostic-style resources, do not treat it as final for practice mode. Add or replace the missing correct/wrong state assets and interaction rules before exporting.

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

- Treat matched configs/templates as runnable component skeletons only. Reuse component types, state arrays, answer/judge metadata, and required root fields; recalculate coordinates, text sizes, alignments, image scale, blanks, choices, drag items, drop zones, and operation controls from the current level content.
- Before setting coordinates, build a whole-level content model. Classify visible blocks as `stem`, `condition`, `answer_sentence`, `formula_row`, `vertical_grid`, `image_or_table`, `choice_option`, `blank`, `keyboard`, `submit`, or `utility`.
- Use `docs/layout_generation_method.md` as the source of truth for layout generation.
- Use the three-zone model: recognition zone for stem/conditions, relation zone for image/table/formula/answer sentence, operation zone for choices/keyboards/confirm.
- For 小中诊断 resources, choose one of the three diagnostic archetypes before falling back to generic layouts: `diagnostic_visual_choice` for visual choice/rule questions, `diagnostic_compute_fill` for short computation fill questions, and `diagnostic_image_reasoning` for long text plus primary image/table reasoning.
- Do not solve layout by moving only the stem text. Consider the whole level: supporting image/table, formulas, blanks, options, keyboard, submit, and utilities.
- Do not include question numbers in user-facing stem text or option/fill text; the level-number component handles numbering.
- Do not prepend option labels such as `A.`/`B.`/`C.`/`D.` when the option already has its own visible text content; only keep option letters when they are the actual user-facing option content, such as diagram labels with no other text.
- Apply typography by text role: short stem 60 centered, long stem 50 left-aligned, condition 50, answer sentence 54, formula row 50, choice option 38.
- If text will wrap in its text box, left-align it and increase text-box height. If it fits on one line, keep it centered.
- For formula rows, size the text component width to the formula length instead of using one fixed wide text box for every row.
- When resizing formula or short fill-label text components, recalculate both the text component `x` and its matching blank component `x` so the whole row pair is centered as one group: `group_width = text_width + gap + blank_width`, text first, then gap, then blank.
- For inline fill questions, split long problems into condition line(s) plus `answer_prefix + QuestionForBlank + answer_suffix`.
- Do not use full-width-space placeholders for inline blanks. Device-dependent wrapping can shift the text while the blank stays fixed.
- Place `answer_suffix` from the right edge of the blank: `suffix_x = blank_x + blank_width / 2 + gap + suffix_width / 2`.
- For inline drag/drop sentences, use the same structure with `LDragPlace` as the target box.
- For image/table questions, allocate the image/table in the relation zone before finalizing stem size and answer blank position.
- For choice questions, place options in the operation zone. If a standard choice button has user-edited `MSprite.nineGrid`, propagate only the nine-grid metadata to same-resource choice buttons.
- Prefer integer score allocation for generated multi-level configs; distribute points as evenly as possible while keeping the total exactly 100.

## Drag Question Generation

- Drag questions must use `MDraggbale` plus `LDragPlace`; do not replace them with choice or fill components.
- Preserve `webEditorCustomInfo` answer/judge flags and component tool answer fields when cloning drag items and drop zones.
- Generate or implement equivalent helpers: `make_drag`, `clone_drag_item`, `clone_drop_zone`, and `apply_drag_skin`.
- Place drop zones first in the relation zone, then place draggable items in the operation zone or lower relation zone.
- For inline drag sentences, split into `answer_prefix + LDragPlace + answer_suffix`; never use whitespace placeholders.
- Validate that every draggable item has a unique `answerKey` and every drop zone has a matching `accept`.
- Apply skin states consistently: draggable default/dragging/placed and drop-zone default/adsorb/adsorbed/placed.
- Keep drag items and drop zones at resource-native proportions unless the user explicitly gives new dimensions.

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
