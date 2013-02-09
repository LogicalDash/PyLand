import pyglet, math
from widgets import WidgetFactory
from database import Database
from parms import DefaultParameters
from state import GameState

d = DefaultParameters()
window = pyglet.window.Window()
batch = pyglet.graphics.Batch()

db = Database(":memory:")
db.mkschema()
db.insert_defaults(d)

gamestate = GameState(db)
wf = WidgetFactory(db, gamestate, 'Default', window, batch)

pyglet.clock.schedule_interval(gamestate.update, 1/60.0, 1/60.0)
pyglet.clock.schedule_interval(wf.movepawns, 1/60.0, 1/60.0)

@window.event
def on_draw():
    window.clear()
    wf.on_draw() # actually adds stuff to batch. maybe rename?
    batch.draw()    
@window.event
def on_key_press(sym, mods):
    wf.on_key_press(sym, mods)
@window.event
def on_mouse_motion(x, y, dx, dy):
    wf.on_mouse_motion(x, y, dx, dy)
@window.event
def on_mouse_press(x, y, button, modifiers):
    wf.on_mouse_press(x, y, button, modifiers)
@window.event
def on_mouse_release(x, y, button, modifiers):
    wf.on_mouse_release(x, y, button, modifiers)
@window.event
def on_mouse_drag(x, y, dx, dy, buttons, modifiers):
    wf.on_mouse_drag(x, y, dx, dy, buttons, modifiers)



pyglet.app.run()