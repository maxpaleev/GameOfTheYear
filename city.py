import arcade

SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 600

world_width = 4032
world_height = 2688

DEAD_ZONE_W = int(SCREEN_WIDTH * 0.35)
DEAD_ZONE_H = int(SCREEN_HEIGHT * 0.35)

CAMERA_LERP = 0.15


class Player(arcade.Sprite):
    def __init__(self):
        super().__init__()

        self.texture = arcade.load_texture(":resources:/images/animated_characters/male_person/malePerson_idle.png")
        self.speed = 300
        self.center_x = SCREEN_WIDTH // 2
        self.center_y = SCREEN_HEIGHT // 2

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

        if dx != 0 and dy != 0:
            factor = 0.7071
            dx *= factor
            dy *= factor

        self.center_x += dx
        self.center_y += dy

        self.center_x = max(self.width / 2, min(world_width - self.width / 2, self.center_x))
        self.center_y = max(self.height / 2, min(world_height - self.height / 2, self.center_y))


class City(arcade.View):
    def __init__(self):
        super().__init__()
        self.background = arcade.load_texture('resurses/city.jpg')

        self.world_camera = arcade.camera.Camera2D()
        self.world_width = world_width
        self.world_height = world_height

    def setup(self):
        self.player_list = arcade.SpriteList()
        self.player = Player()
        self.player_list.append(self.player)

        self.keys_pressed = set()

    def on_draw(self):
        self.clear()
        arcade.draw_texture_rect(self.background,
                                 arcade.rect.XYWH(world_width // 2, world_height // 2, world_width, world_height))

        self.world_camera.use()
        self.player_list.draw()  # Отрисовываем игрока

    def on_update(self, delta_time):
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

    def on_key_press(self, key, modifiers):
        self.keys_pressed.add(key)


    def on_key_release(self, key, modifiers):
        if key in self.keys_pressed:
            self.keys_pressed.remove(key)
