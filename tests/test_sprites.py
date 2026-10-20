import os
import sys

import pygame
import pytest
from PIL import Image

from src.constants import GB_PALETTE, SPRITE_DIR
from src.engine import mascots
from src.engine.overworld_scene import OverworldScene
from src.overworld import load_overworld_sprite, load_player_images

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import svg2gb  # noqa: E402


class FakeManager:
    scenes = []

    def push(self, scene):
        pass


def test_quantize_maps_to_palette_and_transparent_is_lightest():
    img = Image.new("RGBA", (2, 1), (0, 0, 0, 0))
    img.putpixel((1, 0), (0, 0, 0, 255))
    out = svg2gb.quantize(img)
    assert out.getpixel((0, 0)) == GB_PALETTE[0]
    assert out.getpixel((1, 0)) == GB_PALETTE[3]


def test_svg_to_png_sizes(tmp_path):
    pytest.importorskip("cairosvg")
    out = tmp_path / "t.png"
    svg2gb.svg_to_gb_png("mascots/tux.svg", str(out))
    assert Image.open(out).size == (32, 32)
    svg2gb.svg_to_gb_png("mascots/overworld/tux.svg", str(out), 8)
    img = Image.open(out)
    assert img.size == (8, 8)
    assert {c for _, c in img.getcolors()} <= set(GB_PALETTE)


def test_species_sprite_loaded_from_png():
    mascots.get_sprite.cache_clear()
    img = mascots.get_sprite("Tux")
    assert img.get_size() == (32, 32)
    png = pygame.image.load(os.path.join(SPRITE_DIR, "tux.png"))
    assert pygame.image.tobytes(img, "RGB") == pygame.image.tobytes(png, "RGB")


def test_sprite_falls_back_to_placeholder(monkeypatch):
    spec = dict(mascots.species("Tux"), sprite="does_not_exist")
    monkeypatch.setitem(mascots.SPECIES, "Tux", spec)
    mascots.get_sprite.cache_clear()
    try:
        assert mascots.get_sprite("Tux").get_size() == (32, 32)
    finally:
        mascots.get_sprite.cache_clear()


def test_player_has_four_facing_frames():
    frames = load_player_images()
    assert set(frames) == {"up", "down", "left", "right"}
    scene = OverworldScene(FakeManager())
    seen = set()
    for d in frames:
        scene.player.facing = d
        assert scene.player.image is frames[d]
        seen.add(pygame.image.tobytes(scene.player.image, "RGB"))
    assert len(seen) == 4


def test_npc_sprites_exist_and_draw_without_circles():
    scene = OverworldScene(FakeManager())
    for npc in scene.npcs:
        assert load_overworld_sprite(npc.sprite) is not None, npc.sprite
    scene.draw(pygame.Surface((240, 160)))
