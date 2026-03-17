import enum
import sqlite3
from multiprocessing.spawn import set_executable

import arcade
import json
from pyglet.graphics import Batch

SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 600

world_width = 2000
world_height = 1200

DEAD_ZONE_W = int(SCREEN_WIDTH * 0.35)
DEAD_ZONE_H = int(SCREEN_HEIGHT * 0.35)

CAMERA_LERP = 0.15

db = sqlite3.connect("resurses/game.db")
cursor = db.cursor()
query = "SELECT * FROM player"
player = cursor.execute(query).fetchone()
RADIOS = player[1]
Granma, Military, Mechanic, Governor, Elin_call = player[3:]
NPC_uni = {'Granma': Granma, 'Elin': Military, 'Mechanic': Mechanic, 'Governor': Governor, 'Elin_call': Elin_call}


def load_dialogues():
    with open("resurses/dialogues.json", "r", encoding="utf-8") as file:
        return json.load(file)


ALL_DIALOGUES = load_dialogues()


class FaceDirection(enum.Enum):
    LEFT = 0
    RIGHT = 1


class Player(arcade.Sprite):
    def __init__(self):
        super().__init__(scale=0.1)
        self.texture_change_time = None
        self.idle_texture = arcade.load_texture('resurses/hero/hero1.png')
        self.texture = self.idle_texture

        self.walk_textures = []
        for i in range(1, 3):
            texture = arcade.load_texture(f'resurses/hero/hero{i}.png')
            self.walk_textures.append(texture)

        self.current_texture = 0
        self.texture_change_time = 0
        self.texture_change_delay = 0.1
        self.is_walking = False
        self.face_direction = FaceDirection.RIGHT

        self.speed = 300
        self.center_x = SCREEN_WIDTH // 2
        self.center_y = SCREEN_HEIGHT // 2

    def update_animation(self, delta_time: float = 1 / 60):
        if self.is_walking:
            self.texture_change_time += delta_time
            if self.texture_change_time >= self.texture_change_delay:
                self.texture_change_time = 0
                self.current_texture += 1
                if self.current_texture >= len(self.walk_textures):
                    self.current_texture = 0
                if self.face_direction == FaceDirection.RIGHT:
                    self.texture = self.walk_textures[self.current_texture]
                else:
                    self.texture = self.walk_textures[self.current_texture].flip_horizontally()
        else:
            if self.face_direction == FaceDirection.RIGHT:
                self.texture = self.idle_texture
            else:
                self.texture = self.idle_texture.flip_horizontally()

    def update(self, delta_time, keys_pressed):
        dx, dy = 0, 0
        if arcade.key.LEFT in keys_pressed or arcade.key.A in keys_pressed:
            dx -= self.speed * delta_time
        if arcade.key.RIGHT in keys_pressed or arcade.key.D in keys_pressed:
            dx += self.speed * delta_time
        if arcade.key.UP in keys_pressed or arcade.key.W in keys_pressed:
            dy += self.speed * delta_time
        if arcade.key.DOWN in keys_pressed or arcade.key.S in keys_pressed:
            dy -= self.speed * delta_time
        if arcade.key.F in keys_pressed:
            print(self.center_x, self.center_y)

        if dx != 0 and dy != 0:
            factor = 0.7071
            dx *= factor
            dy *= factor

        self.center_x += dx
        self.center_y += dy

        if dx < 0:
            self.face_direction = FaceDirection.LEFT
        elif dx > 0:
            self.face_direction = FaceDirection.RIGHT

        self.center_x = max(self.width / 2, min(world_width - self.width / 2, self.center_x))
        self.center_y = max(self.height / 2, min(world_height - self.height / 2, self.center_y))

        self.is_walking = dx or dy


class NPC(arcade.Sprite):
    def __init__(self, name, image, dialogue_script, scale=1):
        super().__init__(image, scale)
        self.name = name
        self.default_dialogue = dialogue_script
        self.dialogue_script = dialogue_script
        self.dialogue_index = 0
        self.in_interaction_zone = False
        self.unique = not NPC_uni[name]

    def start_dialogue(self):
        if self.unique and NPC_uni['Elin']:
            self.dialogue_index = 0
            self.dialogue_script = self.default_dialogue
        elif self.unique and not NPC_uni['Elin']:
            self.dialogue_index = 0
            if self.name == 'Elin':
                return
            if self.name != 'Elin_call':
                self.dialogue_script = ALL_DIALOGUES['default_quest1']
        else:
            self.dialogue_index = 0
            if self.name == 'Elin' and all(NPC_uni.values()):
                self.dialogue_script = ALL_DIALOGUES['Elin_quest']
                return
            self.dialogue_script = ALL_DIALOGUES['default_quest2']

    def get_current_line(self):
        return self.dialogue_script[self.dialogue_index]

    def advance_dialogue(self):
        self.dialogue_index += 1
        if self.dialogue_index >= len(self.dialogue_script):
            self.on_dialogue_end()
            return False
        return True

    def on_dialogue_end(self):
        pass

    def get_radio(self):
        global RADIOS
        name = self.name
        NPC_uni[name] = True
        self.unique = False
        query = f"UPDATE player SET {name} = ?, radios = radios + 1 "
        cursor.execute(query, (True,))
        RADIOS += 1
        db.commit()


class Granma(NPC):
    def __init__(self):
        super().__init__("Granma", "resurses/NPC/grandma/grandma1.png", ALL_DIALOGUES["granma_quest"], scale=0.1)
        self.center_x = SCREEN_WIDTH // 2 - 100
        self.center_y = SCREEN_HEIGHT // 2 + 150
        self.current_texture = 0
        self.texture_change_time = 0
        self.texture_change_delay = 0.3

        self.animate_textures = []
        for i in range(1, 3):
            texture = arcade.load_texture(f'resurses/NPC/grandma/grandma{i}.png')
            self.animate_textures.append(texture)

    def update_animation(self, delta_time):
        self.texture_change_time += delta_time
        if self.texture_change_time >= self.texture_change_delay:
            self.texture_change_time = 0
            self.current_texture += 1
            if self.current_texture >= len(self.animate_textures):
                self.current_texture = 0
            self.texture = self.animate_textures[self.current_texture]


class Elin_call(NPC):
    def __init__(self):
        super().__init__("Elin_call", 'resurses/NPC/Empty.png', ALL_DIALOGUES["Elin_call"], scale=0.1)
        self.center_x = SCREEN_WIDTH // 2
        self.center_y = SCREEN_HEIGHT // 2

    def on_dialogue_end(self):
        self.remove_from_sprite_lists()


class Elin(NPC):
    def __init__(self, on_complete_callback=None):
        super().__init__("Elin", 'resurses/NPC/Elin.png', ALL_DIALOGUES["Elin_visit"], scale=0.1)
        self.center_x = SCREEN_WIDTH // 2 + 1100
        self.center_y = SCREEN_HEIGHT // 2 + 300
        self.on_complete = on_complete_callback

    def on_dialogue_end(self):
        if self.on_complete and all(NPC_uni.values()):
            self.on_complete()


class Mechanic(NPC):
    def __init__(self):
        super().__init__("Mechanic", 'resurses/NPC/mechanic.png', ALL_DIALOGUES["mechanic_quest"], scale=0.2)
        self.center_x = SCREEN_WIDTH // 2 + 700
        self.center_y = SCREEN_HEIGHT // 2 + 100


class Governor(NPC):
    def __init__(self):
        super().__init__("Governor", 'resurses/NPC/Governor/Governor1.png', ALL_DIALOGUES["governor_quest"], scale=0.1)
        self.center_x = SCREEN_WIDTH // 2 - 250
        self.center_y = SCREEN_HEIGHT // 2 + 10
        self.current_texture = 0
        self.texture_change_time = 0
        self.texture_change_delay = 0.3
        self.animate_textures = []
        for i in range(1, 3):
            texture = arcade.load_texture(f'resurses/NPC/Governor/Governor{i}.png')
            self.animate_textures.append(texture)

    def update_animation(self, delta_time):
        self.texture_change_time += delta_time
        if self.texture_change_time >= self.texture_change_delay:
            self.texture_change_time = 0
            self.current_texture += 1
            if self.current_texture >= len(self.animate_textures):
                self.current_texture = 0
            self.texture = self.animate_textures[self.current_texture]


class Speaker(arcade.Sprite):
    def __init__(self, x, y, sound_object, max_distance=1000):
        super().__init__(scale=0.2)
        self.texture = arcade.load_texture('resurses/NPC/speaker.png')
        self.center_x = x
        self.center_y = y
        self.max_distance = max_distance

        self.sound = sound_object
        self.player = None

    def play(self):
        self.player = arcade.play_sound(self.sound, loop=True, volume=0)


class City(arcade.View):
    def __init__(self):
        super().__init__()
        self.background = arcade.load_texture('resurses/map.jpg')

        self.world_camera = arcade.camera.Camera2D()
        self.gui_camera = arcade.camera.Camera2D()
        self.world_width = world_width
        self.world_height = world_height

        self.active_npc = None

        self.batch = Batch()

        self.text_object_name = arcade.Text(
            text="",
            x=70, y=110,
            color=arcade.color.GOLD, font_size=18, bold=True,
            batch=self.batch
        )

        self.text_object_text = arcade.Text(
            text="",
            x=70, y=80,
            color=arcade.color.WHITE, font_size=14,
            batch=self.batch
        )

        self.text_next = arcade.Text(
            text='Нажми [SPACE] для продолжения',
            x=700, y=40,
            color=arcade.color.GRAY, font_size=10,
            batch=self.batch
        )

    def setup(self):
        self.player_list = arcade.SpriteList()
        self.NPC_list = arcade.SpriteList()
        self.speakers_list = arcade.SpriteList()

        self.player = Player()
        self.player_list.append(self.player)

        self.NPC_list.append(Granma())
        El =(NPC_uni['Elin_call'])
        if not El:
            self.NPC_list.append(Elin_call())
        self.NPC_list.append(Elin(on_complete_callback=self.start_combat))
        self.NPC_list.append(Mechanic())
        self.NPC_list.append(Governor())
        musik = arcade.load_sound('resurses/ost.mp3')

        self.speaker_1 = Speaker(SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 + 150, musik)
        self.speaker_2 = Speaker(SCREEN_WIDTH // 2 - 400, SCREEN_HEIGHT // 2 + 50, musik)
        self.speaker_1.play()
        self.speaker_2.play()
        self.speakers_list.append(self.speaker_1)
        self.speakers_list.append(self.speaker_2)
        self.keys_pressed = set()

    def start_combat(self):
        from fight import CombatView
        self.window.combat_view = CombatView()
        self.window.combat_view.setup()
        self.window.show_view(self.window.combat_view)

    def on_draw(self):
        self.clear()
        self.world_camera.use()
        arcade.draw_texture_rect(self.background,
                                 arcade.rect.XYWH(world_width // 2, world_height // 2, world_width, world_height))
        self.player_list.draw()
        self.NPC_list.draw()
        self.speakers_list.draw()

        self.gui_camera.use()

        if self.active_npc:
            arcade.draw_lrbt_rectangle_filled(50, 950, 20, 150, arcade.color.BLACK_OLIVE)
            arcade.draw_lrbt_rectangle_outline(50, 950, 20, 150, arcade.color.WHITE, 2)

            line = self.active_npc.get_current_line()
            self.text_object_name.text = line["name"]
            self.text_object_text.text = line["text"]
            self.batch.draw()

    def on_update(self, delta_time):
        if self.active_npc:
            return
        self.player_list.update_animation()
        self.NPC_list.update_animation()
        self.player_list.update(delta_time, self.keys_pressed)
        cam_x, cam_y = self.world_camera.position
        dz_left = cam_x - DEAD_ZONE_W // 2
        dz_right = cam_x + DEAD_ZONE_W // 2
        dz_bottom = cam_y - DEAD_ZONE_H // 2
        dz_top = cam_y + DEAD_ZONE_H // 2

        px, py = self.player_list[0].center_x, self.player_list[0].center_y
        target_x, target_y = cam_x, cam_y

        if px < dz_left:
            target_x = px + DEAD_ZONE_W // 2
        elif px > dz_right:
            target_x = px - DEAD_ZONE_W // 2
        if py < dz_bottom:
            target_y = py + DEAD_ZONE_H // 2
        elif py > dz_top:
            target_y = py - DEAD_ZONE_H // 2

        half_w = self.world_camera.viewport_width / 2
        half_h = self.world_camera.viewport_height / 2
        target_x = max(half_w, min(self.world_width - half_w, target_x))
        target_y = max(half_h, min(self.world_height - half_h, target_y))

        smooth_x = (1 - CAMERA_LERP) * cam_x + CAMERA_LERP * target_x
        smooth_y = (1 - CAMERA_LERP) * cam_y + CAMERA_LERP * target_y
        self.cam_target = (smooth_x, smooth_y)

        self.world_camera.position = (self.cam_target[0], self.cam_target[1])

        for npc in self.NPC_list:
            if arcade.check_for_collision(self.player, npc):
                if not npc.in_interaction_zone:
                    npc.in_interaction_zone = True
                    npc.start_dialogue()
                    self.active_npc = npc
                    if npc.name == 'Elin_call':
                        self.player.texture = arcade.load_texture('resurses/hero/herop.png')
                        npc.get_radio()
                    if npc.unique and npc.name == 'Elin':
                        npc.get_radio()
                    if npc.unique and NPC_uni['Elin']:
                        npc.get_radio()
                break
            else:
                npc.in_interaction_zone = False

        for speaker in self.speakers_list:
            dist = arcade.get_distance_between_sprites(self.player, speaker)

            vol = 1 - dist / speaker.max_distance
            vol = max(0, min(1, vol))
            if speaker.player:
                speaker.player.volume = vol

    def on_key_press(self, key, modifiers):
        self.keys_pressed.add(key)

        if self.active_npc:
            if key == arcade.key.SPACE:
                if not self.active_npc.advance_dialogue():
                    # self.active_npc.unique = False
                    self.active_npc = None
            return

    def on_key_release(self, key, modifiers):
        if key in self.keys_pressed:
            self.keys_pressed.remove(key)
