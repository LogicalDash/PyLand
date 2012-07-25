from pyglet import window, graphics
import gameframe
import gamestate

class GameWindow(window.Window):
    def on_draw():
        gamestate.update()
        gameframe.draw()
