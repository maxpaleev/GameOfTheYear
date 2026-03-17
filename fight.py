import random
import sqlite3

import arcade

from city import City

SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 600
TILE_SIZE = 75
GRID_ROWS = 5
GRID_COLS = 9
GRID_START_X = 280
GRID_START_Y = 100

ENEMY_REWARDS = {"Ghost": 15, "Banshee": 40, "Specter": 10}
ROW_TOLERANCE = TILE_SIZE * 0.6

db = sqlite3.connect("resurses/game.db")
cursor = db.cursor()
query = "SELECT * FROM player"
LEVEL = cursor.execute(query).fetchone()[2]

CARD_INFO = [
    {"name": "Метроном", "hint": "каждые 5 сек +10 монет", "price": 10, "pos": (80, 490)},
    {"name": "Струны", "hint": "50 ур / 3 сек, 1 ряд", "price": 50, "pos": (80, 370)},
    {"name": "Бас", "hint": "20 ур / 1 сек, быстро", "price": 30, "pos": (80, 250)},
    {"name": "Барабан", "hint": "30 ур / 5 сек, AOE", "price": 75, "pos": (80, 130)},
]

CARD_H = 110
CARD_W = 155
CARD_X = 5
CARD_ICON_OFFSET = 28
CARD_TEXT_OFFSET_NAME = -22
CARD_TEXT_OFFSET_HINT = -38
CARD_TEXT_OFFSET_PRICE = -54
MISS_ENEMY = 0


class SplashEffect:
    DURATION = 0.35

    def __init__(self, x, y, max_radius):
        self.x = x
        self.y = y
        self.max_radius = max_radius
        self.timer = 0.0
        self.alive = True

    def update(self, delta_time):
        self.timer += delta_time
        if self.timer >= self.DURATION:
            self.alive = False

    def draw(self):
        t = self.timer / self.DURATION
        radius = self.max_radius * t
        alpha = int(220 * (1.0 - t))
        color = (255, 160, 40, alpha)
        arcade.draw_circle_outline(self.x, self.y, radius, color, border_width=3)
        arcade.draw_circle_filled(self.x, self.y, radius * 0.35, (*color[:3], alpha // 2))


class Unit(arcade.Sprite):
    def __init__(self, unit_type, image, price=0, health=100, scale=1):
        super().__init__(image, scale)
        self.unit_type = unit_type
        self.price = price
        self.health = health
        self.timer = 0.0
        self.fire_rate = 999.0

    def clone(self):
        return self.__class__()

    def tick(self, delta_time):
        self.timer += delta_time
        if self.timer >= self.fire_rate:
            self.timer -= self.fire_rate
            return True
        return False


class Metronome(Unit):
    def __init__(self):
        super().__init__(
            "Metronome", "resurses/Units/metronome.png", price=10, health=100, scale=0.1
        )
        self.fire_rate = 5.0


class Strings(Unit):
    def __init__(self):
        super().__init__(
            "Strings", "resurses/Units/strings.png", price=50, health=120, scale=0.1
        )
        self.bullet_speed = 700
        self.bullet_damage = 50
        self.fire_rate = 3.0


class Bass(Unit):
    def __init__(self):
        super().__init__(
            "Bass", "resurses/Units/boombox.png", price=30, health=80, scale=0.1
        )
        self.bullet_speed = 900
        self.bullet_damage = 20
        self.fire_rate = 1.0


class Drum(Unit):
    def __init__(self):
        super().__init__(
            "Drum", "resurses/Units/metronome.png", price=75, health=150, scale=0.1
        )
        self.splash_damage = 30
        self.fire_rate = 5.0
        self.splash_radius = TILE_SIZE * 2.5


class Enemy(arcade.Sprite):
    def __init__(self, unit_type, image, damage=0, cooldown=1.0, health=100, scale=1):
        super().__init__(image, scale)
        self.unit_type = unit_type
        self.damage = damage
        self.health = health
        self.max_health = health
        self.max_cooldown = cooldown
        self.current_cooldown = 0.0
        self.speed = 50
        self.blocked = False

    def move(self, delta_time):
        global MISS_ENEMY
        if not self.blocked:
            self.center_x -= self.speed * delta_time
        if self.right < 0:
            self.remove_from_sprite_lists()
            MISS_ENEMY += 1


class Ghost(Enemy):
    def __init__(self):
        super().__init__(
            "Ghost", "resurses/Enemy/ghost.png",
            damage=25, cooldown=1.5, health=60, scale=0.2,
        )
        self.speed = 50


class Banshee(Enemy):
    def __init__(self):
        super().__init__(
            "Banshee", "resurses/Enemy/ghost.png",
            damage=50, cooldown=2.0, health=180, scale=0.3,
        )
        self.speed = 25


class Specter(Enemy):
    def __init__(self):
        super().__init__(
            "Specter", "resurses/Enemy/ghost.png",
            damage=10, cooldown=0.8, health=40, scale=0.15,
        )
        self.speed = 120


class Bullet(arcade.Sprite):
    def __init__(self, start_x, start_y, speed=700, damage=10):
        super().__init__("resurses/Enemy/note.png", scale=0.1)
        self.center_x = start_x
        self.center_y = start_y
        self.change_x = speed
        self.damage = damage

    def update(self, delta_time):
        self.center_x += self.change_x * delta_time
        if self.left > SCREEN_WIDTH:
            self.remove_from_sprite_lists()


class CombatView(arcade.View):
    def __init__(self):
        super().__init__()
        self.keys_pressed = set()
        self.background = arcade.load_texture("resurses/pol.png")

        self.cards_list = arcade.SpriteList()
        self.towers_list = arcade.SpriteList()
        self.bullets_list = arcade.SpriteList()
        self.enemies_list = arcade.SpriteList()
        self.splash_effects = []

        self.money = 150
        self.wave = 1
        self.wave_timer = 0.0
        self.wave_interval = 15.0

        self.held_unit = None
        self.grid = [[0] * GRID_COLS for _ in range(GRID_ROWS)]

        self.money_label = arcade.Text(
            f"Монеты: {self.money}", 800, 570, arcade.color.WHITE, 16
        )
        self.wave_label = arcade.Text(
            f"Волна: {self.wave}", 800, 545, arcade.color.YELLOW, 14
        )

    def setup(self):
        classes = [Metronome, Strings, Bass, Drum]
        for cls, info in zip(classes, CARD_INFO):
            card = cls()
            card.scale = 0.1
            cx, cy = info["pos"]
            card.position = (cx, cy + CARD_ICON_OFFSET)
            self.cards_list.append(card)

    def on_draw(self):
        self.clear()
        if MISS_ENEMY >= 1:
            arcade.set_background_color(arcade.color.BLACK)
            arcade.draw_text('Вы проиграли!', SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2, arcade.color.WHITE, 40)
            arcade.draw_text('Чтобы вернуться в город, нажмите [R]', SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 - 50, arcade.color.WHITE, 20)
            return
        if LEVEL >= 1:
            arcade.set_background_color(arcade.color.BLACK)
            arcade.draw_text('Вы победили', SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2, arcade.color.WHITE, 40)
            arcade.draw_text('Чтобы вернуться в город, нажмите [R]', SCREEN_WIDTH // 2 - 250,
                             SCREEN_HEIGHT // 2 - 50, arcade.color.WHITE, 20)
            return
        arcade.draw_texture_rect(
            self.background,
            arcade.rect.XYWH(
                SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, SCREEN_WIDTH, SCREEN_HEIGHT
            ),
        )

        # for row in range(GRID_ROWS):
        #     for col in range(GRID_COLS):
        #         x = GRID_START_X + col * TILE_SIZE + TILE_SIZE / 2
        #         y = GRID_START_Y + row * TILE_SIZE + TILE_SIZE / 2
        #         arcade.draw_rect_outline(
        #             arcade.rect.XYWH(x, y, TILE_SIZE, TILE_SIZE), arcade.color.BLACK
        #         )

        for effect in self.splash_effects:
            effect.draw()

        self._draw_card_labels()
        self.cards_list.draw()

        self.towers_list.draw()
        self.enemies_list.draw()
        self.bullets_list.draw()

        for enemy in self.enemies_list:
            self._draw_hp_bar(enemy)

        self.money_label.draw()
        self.wave_label.draw()

        if self.held_unit:
            arcade.draw_sprite(self.held_unit)

    def _draw_hp_bar(self, enemy):
        bar_w = 40
        bar_h = 5
        x = enemy.center_x - bar_w / 2
        y = enemy.top + 4
        pct = max(0.0, enemy.health / enemy.max_health)
        arcade.draw_lrbt_rectangle_filled(
            x, x + bar_w, y, y + bar_h, arcade.color.DARK_RED
        )
        arcade.draw_lrbt_rectangle_filled(
            x, x + bar_w * pct, y, y + bar_h, arcade.color.GREEN
        )

    def _draw_card_labels(self):
        for info in CARD_INFO:
            cx, cy = info["pos"]
            top = cy + CARD_H // 2
            bot = cy - CARD_H // 2
            can_afford = self.money >= info["price"]

            border_color = (80, 200, 80, 255) if can_afford else (180, 50, 50, 255)
            bg_color = (18, 28, 18, 220) if can_afford else (28, 12, 12, 220)

            arcade.draw_lrbt_rectangle_filled(
                CARD_X + 8, CARD_X - 8 + CARD_W, bot, top, bg_color
            )
            arcade.draw_lrbt_rectangle_outline(
                CARD_X + 8, CARD_X - 8 + CARD_W, bot, top, border_color, 2
            )

            divider_y = cy + CARD_TEXT_OFFSET_NAME + 16
            arcade.draw_lrbt_rectangle_filled(
                CARD_X + 4 + 8, CARD_X - 8 + CARD_W - 4,
                divider_y, divider_y + 1,
                (90, 90, 90, 180),
            )

            arcade.draw_text(
                info["name"],
                CARD_X + CARD_W // 2, cy + CARD_TEXT_OFFSET_NAME,
                arcade.color.WHITE,
                font_size=13,
                bold=True,
                anchor_x="center",
            )
            arcade.draw_text(
                info["hint"],
                CARD_X + CARD_W // 2, cy + CARD_TEXT_OFFSET_HINT,
                arcade.color.GOLD,
                font_size=9,
                anchor_x="center",
            )
            price_color = (100, 210, 100, 255) if can_afford else (200, 80, 80, 255)
            arcade.draw_text(
                f"{info['price']} монет",
                CARD_X + CARD_W // 2, cy + CARD_TEXT_OFFSET_PRICE,
                price_color,
                font_size=9,
                anchor_x="center",
            )

    def on_mouse_press(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_LEFT:
            hit_cards = arcade.get_sprites_at_point((x, y), self.cards_list)
            if hit_cards:
                card = hit_cards[0]
                if self.money >= card.price:
                    self.held_unit = card.clone()
                    self.held_unit.alpha = 150
                    self.held_unit.position = (x, y)
        elif button == arcade.MOUSE_BUTTON_RIGHT:
            hit_towers = arcade.get_sprites_at_point((x, y), self.towers_list)
            if hit_towers:
                self._remove_tower(hit_towers[0])

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if self.held_unit:
            self.held_unit.position = (x, y)

    def on_mouse_release(self, x, y, button, modifiers):
        if not self.held_unit:
            return

        col = int((x - GRID_START_X) // TILE_SIZE)
        row = int((y - GRID_START_Y) // TILE_SIZE)

        if 0 <= col < GRID_COLS and 0 <= row < GRID_ROWS and self.grid[row][col] == 0:
            self.held_unit.position = (
                GRID_START_X + col * TILE_SIZE + TILE_SIZE / 2,
                GRID_START_Y + row * TILE_SIZE + TILE_SIZE / 2,
            )
            self.held_unit.alpha = 255
            self.towers_list.append(self.held_unit)
            self.grid[row][col] = 1
            self.money -= self.held_unit.price

        self.held_unit = None

    def on_update(self, delta_time):
        self.money_label.text = f"Монеты: {self.money}"
        self.wave_label.text = f"Волна: {self.wave}"

        if self.money > 500:
            global LEVEL
            LEVEL += 1
            query = 'UPDATE player SET levels = levels + 1'
            cursor.execute(query)
            db.commit()
            if arcade.key.R in self.keys_pressed:
                city = City()
                city.setup()
                self.window.show_view(city)
                return
        if MISS_ENEMY >= 1:
            if arcade.key.R in self.keys_pressed:
                city = City()
                city.setup()
                self.window.show_view(city)
                return

        self._resolve_enemy_attacks(delta_time)

        for enemy in list(self.enemies_list):
            enemy.move(delta_time)

        for enemy in self.enemies_list:
            enemy.blocked = False

        self.bullets_list.update()

        for effect in self.splash_effects:
            effect.update(delta_time)
        self.splash_effects = [e for e in self.splash_effects if e.alive]

        self.wave_timer += delta_time
        if self.wave_timer >= self.wave_interval:
            self._spawn_wave()
            self.wave += 1
            self.wave_timer = 0.0
            self.wave_interval = max(6.0, self.wave_interval - 1.0)

        self._update_towers(delta_time)
        self._resolve_bullet_hits()

        for card in self.cards_list:
            card.alpha = 255 if self.money >= card.price else 160

    def on_key_press(self, key, modifiers):
        self.keys_pressed.add(key)

    def on_key_release(self, key, modifiers):
        if key in self.keys_pressed:
            self.keys_pressed.remove(key)

    def _update_towers(self, delta_time):
        for tower in self.towers_list:
            fired = tower.tick(delta_time)

            if tower.unit_type == "Metronome":
                if fired:
                    self.money += 10

            elif tower.unit_type in ("Strings", "Bass"):
                if fired and self._has_enemy_in_row(tower.center_y):
                    self.bullets_list.append(
                        Bullet(
                            tower.center_x, tower.center_y,
                            tower.bullet_speed, tower.bullet_damage,
                        )
                    )

            elif tower.unit_type == "Drum":
                if fired:
                    self._drum_splash(tower)

    def _resolve_bullet_hits(self):
        for bullet in list(self.bullets_list):
            hit_enemies = arcade.check_for_collision_with_list(
                bullet, self.enemies_list
            )
            if hit_enemies:
                for enemy in hit_enemies:
                    self._damage_enemy(enemy, bullet.damage)
                bullet.remove_from_sprite_lists()

    def _resolve_enemy_attacks(self, delta_time):
        for enemy in list(self.enemies_list):
            hit_towers = arcade.check_for_collision_with_list(enemy, self.towers_list)
            if not hit_towers:
                continue

            enemy.blocked = True

            if enemy.current_cooldown > 0.0:
                enemy.current_cooldown -= delta_time
                continue

            target = hit_towers[0]
            target.health -= enemy.damage
            enemy.current_cooldown = enemy.max_cooldown

            if target.health <= 0:
                self._destroy_tower(target)

    def _spawn_wave(self):
        row_indices = list(range(GRID_ROWS))
        random.shuffle(row_indices)
        count = 2 + self.wave

        for i in range(count):
            row = row_indices[i % GRID_ROWS]
            y = GRID_START_Y + row * TILE_SIZE + TILE_SIZE / 2
            x = SCREEN_WIDTH + random.randint(0, 200)
            roll = random.random()

            if self.wave >= 3 and roll < 0.25:
                enemy = Banshee()
            elif self.wave >= 2 and roll < 0.5:
                enemy = Specter()
            else:
                enemy = Ghost()

            enemy.position = (x, y)
            self.enemies_list.append(enemy)

    def _has_enemy_in_row(self, tower_y):
        return any(
            abs(e.center_y - tower_y) < ROW_TOLERANCE
            for e in self.enemies_list
        )

    def _drum_splash(self, tower):
        self.splash_effects.append(
            SplashEffect(tower.center_x, tower.center_y, tower.splash_radius)
        )
        for enemy in list(self.enemies_list):
            dx = enemy.center_x - tower.center_x
            dy = enemy.center_y - tower.center_y
            if (dx * dx + dy * dy) ** 0.5 <= tower.splash_radius:
                self._damage_enemy(enemy, tower.splash_damage)

    def _damage_enemy(self, enemy, damage):
        if enemy not in self.enemies_list:
            return
        enemy.health -= damage
        if enemy.health <= 0:
            self.money += ENEMY_REWARDS.get(enemy.unit_type, 15)
            enemy.remove_from_sprite_lists()

    def _remove_tower(self, tower):
        col = int((tower.center_x - GRID_START_X) // TILE_SIZE)
        row = int((tower.center_y - GRID_START_Y) // TILE_SIZE)
        if 0 <= row < GRID_ROWS and 0 <= col < GRID_COLS:
            self.grid[row][col] = 0
        tower.remove_from_sprite_lists()

    def _destroy_tower(self, tower):
        self._remove_tower(tower)
