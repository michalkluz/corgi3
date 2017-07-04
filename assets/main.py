# TO DO LIST
# collision with borders refactored

from collections import defaultdict

import cocos
import cocos.collision_model as cm
import cocos.euclid as eu

import config as cfg

#from pyglet.image import load, ImageGrid, Animation
# 41 strona pdfa z ebooka
import pyglet
from pyglet.window import key

class MainLayer(cocos.layer.Layer):
    is_event_handler = True

    def __init__(self):
        super(MainLayer, self).__init__()
        """ Initializes the world, places background and all actors in the specified positions.
        Builds the collision manager and sets up the starting parameters of the game.

        """
        self.animation = pyglet.image.load_animation('assets/corgi1.gif')
        bin = pyglet.image.atlas.TextureBin()
        self.animation.add_to_texture_bin(bin)
        self.player = Actor(cfg.STARTING_POSITION, self.animation, cfg.PLAYER_SHAPE)
        self.add(self.player)

        for _, position in enumerate(cfg.GOLDEN_BONE_POSITIONS):
            self.add(Consumable(position, cfg.GOLDEN_BONE_SPRITE, cfg.GOLDEN_BONE_SHAPE))
        for _, position in enumerate(cfg.BONE_POSITIONS):
            self.add(Consumable(position, cfg.BONE_SPRITE, cfg.BONE_SHAPE))

        for _, position in enumerate(cfg.BORDER_VERTICAL_POSITIONS):
            self.add(Obstacle(position, cfg.BORDER_VERTICAL_IMAGE, cfg.BORDER_SHAPE))
        for _, position in enumerate(cfg.BORDER_HORIZONTAL_POSITIONS):
            self.add(Obstacle(position, cfg.BORDER_HORIZONTAL_IMAGE, cfg.BORDER_SHAPE))

        # Initializes the collision manager and all starting parameters, sets up the scheduler.
        cell = self.player.width * 1.25
        self.collman = cm.CollisionManagerGrid(0, cfg.WINDOW_WIDTH, 0,
                                               cfg.WINDOW_HEIGHT, cell, cell)

        #self.speed = cfg.STARTING_SPEED
        self.player_speed = PlayerSpeed()
        self.lives = cfg.STARTING_LIVES
        self.score = cfg.STARTING_SCORE
        self.may_jump = True
        self.pressed = defaultdict(int)

        # Starts the main loop of the game
        self.schedule(self.update)

    def on_key_press(self, k, m):
        """ Sets up the pressed key to be equal to 1

        """
        self.pressed[k] = 1

    def on_key_release(self, k, m):
        """ Sets up the released key to be equal to 0

        """
        self.pressed[k] = 0

    def update_score(self, points):
        """ Adds score and checks if the game is over

        """
        self.score += points
        print(self.score)
        if self.score >= cfg.WIN_SCORE:
            self.game_over()

    def game_over(self):
        """ Stops the game and displays a game over message

        """
        # Stops the update() loop of the game
        self.pause_scheduler()

        message = Actor(cfg.CENTER_POSITION, cfg.GAME_OVER_MESSAGE, cfg.MESSAGE_SHAPE)
        self.add(message)

    def lose_life(self):
        """ Decrements the number of lives and checks if the game is over. If not, it teleports
        player to the starting position.

        """
        self.lives -= 1
        if self.lives == 0:
            self.game_over()

        self.player.position = cfg.STARTING_POSITION
        self.player.cshape.center = self.player.position

    def move(self, dt):

        x = self.pressed[key.RIGHT] - self.pressed[key.LEFT]
        y = self.pressed[key.UP] - self.pressed[key.DOWN]
        space_pressed = self.pressed[key.SPACE]
        if space_pressed == 0:
            self.may_jump = True

        jump_action = cocos.actions.JumpBy((cfg.JUMP*x, cfg.JUMP*y), 30, 1, duration=0.4)
        is_player_jumping = self.player.are_actions_running()

        if self.player.are_actions_running() is False:
            self.player.image = cfg.PLAYER_STANDING
        
        if x != 0:
            self.player_speed.accelerate()
            pos = self.player.position
            new_x = pos[0] + self.player_speed.get_speed() * x * dt
            self.player.position = (new_x, pos[1])
            self.player.cshape.center = self.player.position

        if y != 0:
            self.player_speed.accelerate()
            pos = self.player.position
            new_y = pos[1] + self.player_speed.get_speed() * y * dt
            self.player.position = (pos[0], new_y)
            self.player.cshape.center = self.player.position

        if space_pressed == 1 and is_player_jumping is False and self.may_jump is True:
            self.may_jump = False
            super(Actor, self.player).do(jump_action)
            self.player.image_change(cfg.PLAYER_JUMP)
            self.player.cshape.center = self.player.position

            # checks if the player would be blocked by an obstacle in new position
            # if yes, the new position is not assigned (the player doesn't move)
            # for other in self.collman.objs_near(self.player, 3):
            #     if other.__class__.__name__ == "Obstacle":
            #         self.player.position = (pos[0], pos[1])

        # makes the player turn left or right
        if x == -1:
            self.player.scale_x = 1
        if x == 1:
            self.player.scale_x = -1

        # if the player is standing still it resets the player's speed factor
        if x == 0 and y == 0:
            self.player_speed.speed_factor = 0.1

    def update(self, dt):
        """ Main loop of the game. Checks the player collision with a consumable
        and allows the player to move.

        """
        self.collide()
        self.move(dt)

    def collide(self):
        """Checks for collisions with the player at the current player's position
        If there's a collision found with a consumable, the consumable is removed
        and the score is updated.

        """
        # clears the memory of the collision manager
        self.collman.clear()

        # adds every object in range of the collision manager
        for _, node in self.children:
            self.collman.add(node)
        for other in self.collman.iter_colliding(self.player):
            if other.__class__.__name__ == "Consumable":
                self.remove(other)
                self.update_score(other.score)


class Actor(cocos.sprite.Sprite):

    def __init__(self, coords, image, shape):
        super().__init__(image)
        pos = self.sprite_position(coords)
        self.collision_shape(shape, pos)

    def sprite_position(self, coords):
        x, y = coords
        self.position = pos = eu.Vector2(x, y)
        return pos

    def collision_shape(self, shape, pos):

        if shape == "box":
            self.cshape = cm.AARectShape(pos, self.width/2, self.height/2)
        if shape == "circle":
            self.cshape = cm.CircleShape(pos, self.width/2)

    def image_change(self, image):
        self.image = pyglet.image.load(image)


class Consumable(Actor):

    def __init__(self, coords, image, shape):
        super().__init__(coords, image, shape)
        self.set_score(image)

    def set_score(self, image):
        if image == cfg.GOLDEN_BONE_SPRITE:
            self.score = cfg.GOLDEN_BONE_SCORE
            self.speed_boost = cfg.GOLDEN_BONE_SPEED_BOOST

        if image == cfg.BONE_SPRITE:
            self.score = cfg.BONE_SCORE
            self.speed_boost = cfg.BONE_SPEED_BOOST


class Obstacle(Actor):

    def __init__(self, coords, image, shape):
        super().__init__(coords, image, shape)


class PlayerSpeed:
    def __init__(self):
        self.acceleration = 0.15
        self.speed_factor = 0.1
        self.speed = cfg.STARTING_SPEED * self.speed_factor

    def get_speed(self):
        return cfg.STARTING_SPEED * self.speed_factor

    def accelerate(self):
        if self.speed_factor < 1:
            self.speed_factor += self.acceleration


if __name__ == '__main__':

    cocos.director.director.init(fullscreen=True,
                                 caption='The Amazing Adventures of the Courageous Corgi! Part 1')

    # game_Background = cocos.tiles.load(cfg.MAP_PATH)['Background']
    # game_TopLayer = cocos.tiles.load(cfg.MAP_PATH)['TopLayer']
    # game_CollisionLayer = cocos.tiles.load(cfg.MAP_PATH)['CollisionLayer']
    # game_Consumable = cocos.tiles.load(cfg.MAP_PATH)['Consumable']
    # main_layer = MainLayer()

    # scene = cocos.scene.Scene(game_Background)
    # game_Background.set_view(0, 0, game_Background.px_width, game_Background.px_height)

    layer = MainLayer()
    scene = cocos.scene.Scene(layer)

    # scene.add(main_layer)
    # scene.add(game_TopLayer)
    # game_TopLayer.set_view(0, 0, game_TopLayer.px_width, game_TopLayer.px_height)
    # scene.add(game_CollisionLayer)
    # scene.add(game_Consumable)
    cocos.director.director.run(scene)
