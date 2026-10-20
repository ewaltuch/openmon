# Design

## Types and the type chart

Four element types form a cycle. Each type is strong against the next one and
weak against the previous one:

    Kernel > Shell > Browser > Editor > Kernel

Multipliers apply to the attacking move's type against the defender's type.
Unlisted pairs (including same-type) are 1.0.

| Attacker \ Defender | Kernel | Shell | Browser | Editor |
|---------------------|--------|-------|---------|--------|
| Kernel              | 1.0    | 2.0   | 1.0     | 0.5    |
| Shell               | 0.5    | 1.0   | 2.0     | 1.0    |
| Browser             | 1.0    | 0.5   | 1.0     | 2.0    |
| Editor              | 2.0    | 1.0   | 0.5     | 1.0    |

The source of truth is `type_effectiveness` in `assets/mascots.yaml`.

## Damage

    damage = max(1, int(power * atk / defense * 0.7 * type multiplier * r))

`r` is a random factor, uniform in 0.85-1.0 (`battle_scene.damage_rng`, seed it
in tests). Move power matters in proportion, and atk against defense scales
the whole hit. With current stats a typical neutral hit takes a quarter of a
mascot's HP, so a KO takes roughly 3-8 hits (more against resisted types).

## Roster

| Species    | Type    |
|------------|---------|
| Tux        | Kernel  |
| Gopher     | Kernel  |
| BSD Daemon | Shell   |
| Octocat    | Browser |
| Konqi      | Browser |
| Elephpant  | Editor  |

Each species has 3-4 moves; move types may differ from the species type.

## Wild encounters

`wild_encounters` is one global weighted list, so every grass tile rolls from
the same table (Octocat most common, Elephpant rarest). Per-area tables need
map support (zones in the tile map) and are not done yet.
