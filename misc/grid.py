'''
                      .,,
                    l;:;c::
                   ,:o. d.O
                    c:c;c:'
       .c:::c.        0.k
      'o,c'l.k        0.x
      .x'c,c.d,       0.x
        ;;;:cc:l;     0.d         ;;;;:
              :l:cc.  O.x        k'c,:'x.
                'lc:lcx 0.  .;::c,.o'c;o'
                   d:.:,:,cllc:::;c;;;c'
                   ,o::.d.x;.
                   lc'loc.O.
              .,'cl;o, ..lc:o,'.
            :cc:c.ll      'x :,::;
            0.l .d,c      ,;o. o.k
            :cc;c:o        c;c:c:'
              ','            ...



Copyright © 2026 Emergent Properly
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

'''

from kivy.uix.widget import Widget
from kivy.graphics import Color, Line, Rectangle
from kivy.properties import StringProperty, NumericProperty
from kivy.core.image import Image as CoreImage
import os

class Grid(Widget):

    grid_image_source = StringProperty(os.path.join(os.path.dirname(__file__), "grid.png"))
    grid_size = NumericProperty(48)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self._update_canvas, size=self._update_canvas)
        self._update_canvas()

    def _update_canvas(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(1, 1, 1, 0.1)

            if os.path.exists(self.grid_image_source):
                texture = self._get_texture()
                if texture:
                    texture.wrap = 'repeat'
                    uv_width = self.width / texture.width
                    uv_height = self.height / texture.height

                    Rectangle(
                        texture=texture,
                        pos=self.pos,
                        size=self.size,
                        uvsize=(uv_width, uv_height)
                    )

            Color(0.2, 0.2, 1, 0.2)

            for x in range(int(self.x), int(self.right), self.grid_size):
                Line(points=[x, self.y, x, self.top], width=1.5)
            for y in range(int(self.y), int(self.top), self.grid_size):
                Line(points=[self.x, y, self.right, y], width=1.5)

            Color(0.05, 0.05, 0.4, 1)
            Line(rectangle=(self.x, self.y, self.width, self.height), width=1.5)


    def _get_texture(self):
        if not hasattr(Grid, '_grid_texture_cache'):
            Grid._grid_texture_cache = CoreImage(self.grid_image_source).texture
        return Grid._grid_texture_cache
