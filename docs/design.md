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
