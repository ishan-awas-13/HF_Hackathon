# 🎨 White Theme — Next Session Agenda

## Strategy
Create a **parallel light-theme version** on a new branch so the dark theme stays untouched.

---

## Phase 1: Setup (5 min)
- [ ] Create branch: `git checkout -b feature/white-theme`
- [ ] Decide: duplicate `config.py` → `config_light.py`, or add a toggle?

## Phase 2: Background & Blobs (10 min)
- [ ] Change `:root` `--bg` from `#080818` → white/off-white (`#f8fafc` or `#ffffff`)
- [ ] Update `--surface` from dark glass → light glass (`rgba(255,255,255,0.7)`)
- [ ] Update `--border` to a soft gray (`rgba(0,0,0,0.08)`)
- [ ] Remap blob colors in `_BLOBS_HTML` to softer pastels (lower opacity, lighter hues)
- [ ] Adjust blob `filter: blur()` and `opacity` for a subtle light-mode glow

## Phase 3: Text & Foreground Colors (10 min)
- [ ] Flip `--text-main` → dark (`#1e293b`)
- [ ] Flip `--text-muted` → medium gray (`#64748b`)
- [ ] Flip `--text-dim` → light gray (`#94a3b8`)
- [ ] Update all inline `color:#94a3b8` / `color:#e2e8f0` in step labels & HTML blocks
- [ ] Verify header gradient still pops on white (may need darker gradient stops)

## Phase 4: Component Styling (15 min)
- [ ] Step group panels: light glass background, subtle shadow instead of dark glow
- [ ] Textareas: white/near-white bg, soft gray border (keep the 2px blue border accent)
- [ ] Buttons: ensure primary purple buttons contrast well on white
- [ ] Radio buttons (Step 2): verify readability on light surface
- [ ] Tabs: update selected/unselected colors for light mode
- [ ] Accordion headers: flip to dark-on-light text
- [ ] Tips box: adjust indigo overlay for light background

## Phase 5: Special Elements (10 min)
- [ ] Footer text: ensure visibility on white
- [ ] Loading state overrides: update `--block-background-fill` for light mode
- [ ] About tab: check blob z-index and text contrast
- [ ] PDF report styling (if any inline colors need updating)

## Phase 6: Test & Polish (10 min)
- [ ] Full visual walkthrough of all 4 tabs
- [ ] Check responsiveness at different widths
- [ ] Verify no white-on-white or invisible elements
- [ ] Commit & push

---

## Key Files to Touch
| File | What Changes |
|---|---|
| `config.py` | `:root` CSS variables, step group styles, glass panel colors |
| `interview_coach.py` | `_BLOBS_HTML` colors, inline HTML `style=` attributes, theme hues |

## Reference: Current Dark Palette → Light Palette
| Token | Dark Value | Light Target |
|---|---|---|
| `--bg` | `#080818` | `#f8fafc` |
| `--surface` | `rgba(15,15,35,0.65)` | `rgba(255,255,255,0.7)` |
| `--border` | `rgba(99,102,241,0.15)` | `rgba(0,0,0,0.08)` |
| `--text-main` | `#e2e8f0` | `#1e293b` |
| `--text-muted` | `#94a3b8` | `#64748b` |
| `--indigo` | `#6366f1` | `#6366f1` (keep) |
