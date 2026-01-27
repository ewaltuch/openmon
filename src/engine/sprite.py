"""
Abstract sprite and animation helper for Open-Mon.
"""

import pygame


class AnimatedSprite(pygame.sprite.Sprite):
    def __init__(self, images, pos, frame_duration=0.1):
        super().__init__()
        self.images = images
        self.index = 0
        self.image = self.images[self.index]
        self.rect = self.image.get_rect(topleft=pos)
        self.frame_duration = frame_duration
        self.timer = 0

    def update(self, dt):
        self.timer += dt
        if self.timer >= self.frame_duration:
            self.timer = 0
            self.index = (self.index + 1) % len(self.images)
            self.image = self.images[self.index]
