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

from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import Color, Line


class ControlConnection(FloatLayout):
    def __init__(self, node1, node2, **kwargs):
        super().__init__(**kwargs)
        self.node1 = node1
        self.node2 = node2
        self.size_hint = (None, None)

        with self.canvas:
            Color(0.8, 0.2, 0.0, 0.7)
            self.line = Line(width=1)

        self.update_position()
        node1.bind(pos=self.update_position)
        node2.bind(pos=self.update_position)

    def update_position(self, *args):
        center1 = (self.node1.x + self.node1.width/2,
                  self.node1.y + self.node1.height/2)
        center2 = (self.node2.x + self.node2.width/2,
                  self.node2.y + self.node2.height/2)
        self.line.points = [center1[0], center1[1], center2[0], center2[1]]
