# Open-Mon Architecture

```mermaid
graph TD
    Game --> SceneManager
    SceneManager --> TitleScene
    SceneManager --> OverworldScene
    SceneManager --> BattleScene
    SceneManager --> CreditsScene
    OverworldScene --> TileMap
    OverworldScene --> Player
    BattleScene --> Mascot
    BattleScene --> Move
    SaveManager --> Game
```

- **Game**: Main loop, input, timing
- **SceneManager**: State stack, transitions
- **Scenes**: Title, Overworld, Battle, Credits
- **TileMap/Player**: Overworld logic
- **Mascot/Move**: Battle logic
- **SaveManager**: Save/load JSON
