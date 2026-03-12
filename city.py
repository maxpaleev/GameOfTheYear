import enum

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
        self.texture = arcade.load_texture('resurses/hero_r.png')
        self.speed = 300
        self.center_x = SCREEN_WIDTH // 2
        self.center_y = SCREEN_HEIGHT // 2

        self.face_direction = FaceDirection.RIGHT
        self.texture_r = arcade.load_texture('resurses/hero_r.png')
        self.texture_l = arcade.load_texture('resurses/hero_l.png')

    def update_animation(self, delta_time: float = 1 / 60):
        if self.face_direction == FaceDirection.RIGHT:
            self.texture = self.texture_r
        else:
            self.texture = self.texture_l

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


class NPC(arcade.Sprite):
    def __init__(self, name, image, dialogue_script, scale=1):
        super().__init__(image, scale)
        self.name = name
        self.dialogue_script = dialogue_script
        self.dialogue_index = 0
        self.in_interaction_zone = False

    def start_dialogue(self):
        self.dialogue_index = 0

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


class Granma(NPC):
    def __init__(self):
        super().__init__("Granma", "resurses/grandma.png", ALL_DIALOGUES["granma_quest"], scale=0.1)
        self.center_x = SCREEN_WIDTH // 2 - 100
        self.center_y = SCREEN_HEIGHT // 2 + 150


class Military(NPC):
    def __init__(self, on_complete_callback=None):
        super().__init__("Military", 'resurses/military.jpg', ALL_DIALOGUES["military_quest"], scale=0.2)
        self.center_x = SCREEN_WIDTH // 2 + 1100
        self.center_y = SCREEN_HEIGHT // 2 + 300
        self.on_complete = on_complete_callback

    def on_dialogue_end(self):
        if self.on_complete:
            self.on_complete()


class Mechanic(NPC):
    def __init__(self):
        super().__init__("Mechanic", 'resurses/mechanic.png', ALL_DIALOGUES["mechanic_quest"], scale=0.2)
        self.center_x = SCREEN_WIDTH // 2 + 700
        self.center_y = SCREEN_HEIGHT // 2 + 100


class Governor(NPC):
    def __init__(self):
        super().__init__("Governor", 'resurses/governor.png', ALL_DIALOGUES["governor_quest"], scale=0.6)
        self.center_x = SCREEN_WIDTH // 2 - 250
        self.center_y = SCREEN_HEIGHT // 2 + 60


class Speaker(arcade.Sprite):
    def __init__(self, x, y, sound_object, max_distance=1000):
        super().__init__(scale=0.2)
        self.texture = arcade.load_texture('resurses/speaker.png')
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
        self.NPC_list.append(Military(on_complete_callback=self.start_combat))
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
                    self.active_npc = None
            return

    def on_key_release(self, key, modifiers):
        if key in self.keys_pressed:
            self.keys_pressed.remove(key)

