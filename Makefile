# Makefile for Open-Mon asset pipeline

assets: assets/sprites/ assets/sfx/ assets/music/
	python scripts/svg2gb.py mascots/tux.svg assets/sprites/tux.png
	python scripts/svg2gb.py mascots/octocat.svg assets/sprites/octocat.png
	python scripts/svg2gb.py mascots/bsd.svg assets/sprites/bsd.png
	python scripts/svg2gb.py mascots/elephpant.svg assets/sprites/elephpant.png
	python scripts/svg2gb.py mascots/konqi.svg assets/sprites/konqi.png
	python scripts/svg2gb.py mascots/gopher.svg assets/sprites/gopher.png
	python scripts/beepbox2wav.py music/overworld.json assets/music/overworld.wav
	python scripts/beepbox2wav.py music/battle.json assets/music/battle.wav
