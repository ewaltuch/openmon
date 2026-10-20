"""Outcome of a battle, handed from BattleScene to OverworldScene."""

from dataclasses import dataclass, field


@dataclass
class BattleResult:
    """What a finished battle tells the overworld.

    BattleScene sets one on ``manager.battle_result`` right before popping;
    ``OverworldScene.update()`` reads it and sets the attribute back to None.
    Add new outcomes as fields with defaults so existing callers keep working.
    """

    party_states: list = field(default_factory=list)  # party after battle (incl. xp)
    won: bool = False  # whole opponent party fainted
    lost: bool = False  # whole player party fainted: move back to spawn
    reward: int = 0  # money for a trainer win
    captured_name: str | None = None  # species captured (already in party_states)
