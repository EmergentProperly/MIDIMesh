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

from kivy.core.image import Image as CoreImage
from kivy.graphics import Color, Rectangle
from kivy.uix.floatlayout import FloatLayout
from kivy.properties import BooleanProperty


class ControlNode(FloatLayout):
    active = BooleanProperty(False)
    _texture_base = None
    _texture_control = None

    def __init__(self, control_panel, index, is_base=False, **kwargs):
        super().__init__(**kwargs)
        self.control_panel = control_panel
        self.index = index
        self.is_base = is_base
        self.dragging = False
        self.size_hint = (None, None)
        self.size = (76, 76)


        with self.canvas:
            if ControlNode._texture_base is None:
                ControlNode._texture_base = CoreImage("assets/node.png").texture
            if ControlNode._texture_control is None:
                ControlNode._texture_control = CoreImage("assets/node-flipped.png").texture

            node_texture = ControlNode._texture_control if not self.is_base else ControlNode._texture_base

            if self.is_base:
                Color(1, 1, 1, 1)
            else:
                Color(1, 1, 1, 1)
            self.circle = Rectangle(
                texture=node_texture,
                pos=self.pos,
                size=self.size
            )

        self.bind(pos=lambda instance, value: setattr(instance.circle, 'pos', value))
        self.bind(size=lambda instance, value: setattr(instance.circle, 'size', value))

    def on_touch_down(self, touch):
        if not self.is_base and self.collide_point(*touch.pos):
            self.dragging = True
            self.active = True
            touch.grab(self)
            return True
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if self.dragging and touch.grab_current is self:
            base_node = self.control_panel.nodes[self.index]
            min_x = base_node.x + base_node.width
            max_x = self.control_panel.width - self.width

            new_x = max(min_x, min(touch.x - self.width/2, max_x))
            self.x = new_x

            self.control_panel.update_control_value(self.index)
            return True
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if self.dragging and touch.grab_current is self:
            self.dragging = False
            self.active = False
            touch.ungrab(self)
            return True
        return super().on_touch_up(touch)
