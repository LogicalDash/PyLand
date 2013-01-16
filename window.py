from pyglet import window

class GameWindow(window.Window):
    def __init__(self, frame):
        self.frame = frame
        
    def on_draw(self):
        self.frame.state.update()
        self.frame.draw()
