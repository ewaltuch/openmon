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

## Progression

Species stats in `assets/mascots.yaml` are the level-5 values; each level adds
the species' `growth` (rounded). `xp` counts within the current level and
`xp_to_next(level) = 3 * level^2`. Defeating a mascot yields
`xp_yield * level / 5` (x1.5 from trainers), split among the party members
that fought it and are still standing. A level-up raises HP by the max-HP gain.
A `learnset` maps levels to moves; a mascot knows the newest 4, so learning a
fifth forgets the oldest. Wild levels come from `wild_encounters` (`level` is a
number or `[min, max]`); trainer party entries are a name (level 5) or
`{name, level}`.

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

`wild_encounters` in `mascots.yaml` is the default weighted list (Octocat most
common, Elephpant rarest). A map YAML can define its own `encounters` list;
maps without one (the town) use the default. Route 1 favors Gopher and
Elephpant.
