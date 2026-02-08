import random
import arcade
import math
from city import City

SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 600
TILE_SIZE = 64
GRID_ROWS = 5
GRID_COLS = 9
GRID_START_X = 200
GRID_START_Y = 100


class Unit(arcade.Sprite):
    def __init__(self, unit_type, image, price=0, health=100, scale=1):
        super().__init__(image, scale)
        self.unit_type = unit_type
        self.price = price
        self.health = health
        self.timer = 0

    def clone(self):
        # Универсальный клон для всех наследников
        return self.__class__()


class Enemy(arcade.Sprite):
    def __init__(self, unit_type, image, damage=0, cooldown=1.0, health=100, scale=1):
        super().__init__(image, scale)
        self.unit_type = unit_type
        self.damage = damage
        self.health = health
        self.max_cooldown = cooldown
        self.current_cooldown = 0  # Начинаем без задержки


class Strings(Unit):
    def __init__(self):
        super().__init__('Strings', 'resurses/strings.png', price=50, health=100, scale=0.1)
        self.bullet_speed = 800
        self.bullet_damage = 50


class Metronome(Unit):
    def __init__(self):
        super().__init__('Metronome', 'resurses/metronome.png', price=10, health=100, scale=0.1)


class Ghost(Enemy):
    def __init__(self):
        # Увеличил здоровье, так как 10 — это на один выстрел
        super().__init__('Ghost', 'resurses/ghost.png', damage=25, cooldown=1.5, health=60, scale=0.2)
        self.speed = 50

    def update(self, delta_time):
        # Движение влево, если не остановлен (логика остановки в CombatView)
        self.center_x -= self.speed * delta_time  # Упрощенное движение
        if self.right < 0:
            self.remove_from_sprite_lists()


class Bullet(arcade.Sprite):
    def __init__(self, start_x, start_y, speed=800, damage=10):
        super().__init__("resurses/note.png", scale=0.1)
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
        self.background = arcade.load_texture('resurses/pole.jpg')
        self.cards_list = arcade.SpriteList()
        self.towers_list = arcade.SpriteList()
        self.bullets_list = arcade.SpriteList()
        self.enemies_list = arcade.SpriteList()
        self.window.city = City()

        self.money = 100
        self.metronome_count = 0
        self.money_timer = 0
        self.spawn_timer = 0


        self.held_unit = None
        self.grid = [[0 for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]

        # UI
        self.money_label = arcade.Text(f"Монеты: {self.money}", 800, 550, arcade.color.WHITE, 18)

    def setup(self):
        # Инициализация карт
        metronome_card = Metronome()
        metronome_card.position = (80, 500)
        self.cards_list.append(metronome_card)

        strings_card = Strings()
        strings_card.position = (80, 400)
        self.cards_list.append(strings_card)

    def on_draw(self):
        self.clear()
        arcade.draw_texture_rect(self.background,
                                 arcade.rect.XYWH(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, SCREEN_WIDTH, SCREEN_HEIGHT))

        # Сетка
        for row in range(GRID_ROWS):
            for col in range(GRID_COLS):
                x = GRID_START_X + col * TILE_SIZE + TILE_SIZE / 2
                y = GRID_START_Y + row * TILE_SIZE + TILE_SIZE / 2
                arcade.draw_rect_outline(arcade.rect.XYWH(x, y, TILE_SIZE, TILE_SIZE), arcade.color.BLACK)

        self.cards_list.draw()
        self.towers_list.draw()
        self.enemies_list.draw()
        self.bullets_list.draw()
        self.money_label.draw()

        if self.held_unit:
            arcade.draw_sprite(self.held_unit)

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
            # Удаление башни
            hit_towers = arcade.get_sprites_at_point((x, y), self.towers_list)
            if hit_towers:
                tower = hit_towers[0]
                col = int((tower.center_x - GRID_START_X) // TILE_SIZE)
                row = int((tower.center_y - GRID_START_Y) // TILE_SIZE)
                if tower.unit_type == 'Metronome':
                    self.metronome_count -= 1
                self.grid[row][col] = 0
                tower.remove_from_sprite_lists()

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if self.held_unit:
            self.held_unit.position = (x, y)

    def on_mouse_release(self, x, y, button, modifiers):
        if not self.held_unit:
            return

        col = int((x - GRID_START_X) // TILE_SIZE)
        row = int((y - GRID_START_Y) // TILE_SIZE)

        if 0 <= col < GRID_COLS and 0 <= row < GRID_ROWS and self.grid[row][col] == 0:
            self.held_unit.position = (GRID_START_X + col * TILE_SIZE + TILE_SIZE / 2,
                                       GRID_START_Y + row * TILE_SIZE + TILE_SIZE / 2)
            self.held_unit.alpha = 255
            self.towers_list.append(self.held_unit)
            self.grid[row][col] = 1
            self.money -= self.held_unit.price
            if self.held_unit.unit_type == 'Metronome':
                self.metronome_count += 1

        self.held_unit = None

    def on_update(self, delta_time):
        self.money_label.text = f"Монеты: {self.money}"

        if self.money > 500:
            self.window.city_view = City()
            self.window.city_view.setup()
            self.window.show_view(self.window.city_view)
        # Списки обновляются сами
        self.bullets_list.update()
        self.enemies_list.update()

        # Экономика
        self.money_timer += delta_time
        if self.money_timer >= 5:
            if self.metronome_count > 0:
                self.money += 10 * self.metronome_count
            self.money_timer = 0

        # Спавн врагов
        self.spawn_timer += delta_time
        if self.spawn_timer >= 10:
            ghost = Ghost()
            ghost.position = (SCREEN_WIDTH, GRID_START_Y + random.randint(0, 4) * TILE_SIZE + TILE_SIZE / 2)
            self.enemies_list.append(ghost)
            self.spawn_timer = 0

        # Логика башен (Стрельба)
        for tower in self.towers_list:
            if tower.unit_type == 'Strings':
                tower.timer += delta_time
                if tower.timer >= 3:  # Стреляем раз в 3 сек
                    bullet = Bullet(tower.center_x, tower.center_y, tower.bullet_speed, tower.bullet_damage)
                    self.bullets_list.append(bullet)
                    tower.timer = 0

        # Проверка карт (активны или нет)
        for card in self.cards_list:
            card.alpha = 255 if self.money >= card.price else 100

        # Коллизии: Пули -> Враги
        for bullet in self.bullets_list:
            hit_enemies = arcade.check_for_collision_with_list(bullet, self.enemies_list)
            if hit_enemies:
                for enemy in hit_enemies:
                    enemy.health -= bullet.damage
                    if enemy.health <= 0:
                        enemy.remove_from_sprite_lists()
                        self.money += 15
                bullet.remove_from_sprite_lists()

        # Коллизии: Враги -> Башни (ИСПРАВЛЕНО)
        for enemy in self.enemies_list:
            hit_towers = arcade.check_for_collision_with_list(enemy, self.towers_list)
            if hit_towers:
                # Враг останавливается
                enemy.center_x += enemy.speed * delta_time  # Компенсируем движение назад, чтобы он стоял

                target_tower = hit_towers[0]

                if enemy.current_cooldown <= 0:
                    target_tower.health -= enemy.damage
                    enemy.current_cooldown = enemy.max_cooldown  # СБРОС ТАЙМЕРА
                    print(f"Атака! У {target_tower.unit_type} осталось {target_tower.health} HP")

                    if target_tower.health <= 0:
                        if target_tower.unit_type == 'Metronome':
                            self.metronome_count -= 1

                        # Освобождаем сетку
                        t_col = int((target_tower.center_x - GRID_START_X) // TILE_SIZE)
                        t_row = int((target_tower.center_y - GRID_START_Y) // TILE_SIZE)
                        self.grid[t_row][t_col] = 0

                        target_tower.remove_from_sprite_lists()
                else:
                    enemy.current_cooldown -= delta_time
