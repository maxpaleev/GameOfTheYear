import random

import arcade
from pyglet.graphics import Batch
import math

SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 600
TILE_SIZE = 64
GRID_ROWS = 5
GRID_COLS = 9
GRID_START_X = 200  # Отступ слева (место для Зомби/Тишины)
GRID_START_Y = 100


class Unit(arcade.Sprite):
    def __init__(self, unit_type, image, price=0, health=100, scale=1):
        super().__init__(image, scale)
        self.unit_type = unit_type
        self.price = price
        self.health = health

class Enemy(arcade.Sprite):
    def __init__(self, unit_type, image, damage=0, coaldown=1, health=100, scale=1):
        super().__init__(image, scale)
        self.unit_type = unit_type
        self.damage = damage
        self.health = health
        self.coaldown = coaldown


class Strings(Unit):
    def __init__(self):
        self.price = 50
        self.unit_type = 'Strings'
        self.health = 100
        self.bullet_speed = 1000
        self.bullet_damage = 100
        texture = 'resurses/strings.png'
        self.timer = 0
        super().__init__(self.unit_type, texture, self.price, self.health, scale=0.1)

    def clone(self):
        return Strings()


class Metronome(Unit):
    def __init__(self):
        price = 10
        unit_type = 'Metronome'
        health = 100
        image = 'resurses/metronome.png'
        super().__init__(unit_type, image, price, health, scale=0.1)

    def clone(self):
        return Metronome()


class Ghost(Enemy):
    def __init__(self):
        unit_type = 'Ghost'
        health = 10
        damage = 50
        image = 'resurses/ghost.png'
        super().__init__(unit_type, image, damage, 2, health, scale=0.2)

    def update(self, delta_time):
        if self.center_x < 0 or self.center_x > SCREEN_WIDTH:
            self.remove_from_sprite_lists()
        self.center_x -= 50 * delta_time



class Bullet(arcade.Sprite):
    def __init__(self, start_x, start_y, target_x, target_y, speed=800, damage=10):
        super().__init__(scale=0.1)
        self.texture = arcade.load_texture("resurses/note.png")
        self.center_x = start_x
        self.center_y = start_y
        self.speed = speed
        self.damage = damage

        # Рассчитываем направление
        x_diff = target_x - start_x
        y_diff = target_y - start_y
        angle = math.atan2(y_diff, x_diff)
        # И скорость
        self.change_x = math.cos(angle) * speed
        self.change_y = math.sin(angle) * speed
        # Если текстура ориентирована по умолчанию вправо, то поворачиваем пулю в сторону цели
        # Для другой ориентации нужно будет подправить угол
        self.angle = math.degrees(-angle)  # Поворачиваем пулю

    def update(self, delta_time):
        # Удаляем пулю, если она ушла за экран
        if (self.center_x < 0 or self.center_x > SCREEN_WIDTH or
                self.center_y < 0 or self.center_y > SCREEN_HEIGHT):
            self.remove_from_sprite_lists()

        self.center_x += self.change_x * delta_time
        self.center_y += self.change_y * delta_time


class CombatView(arcade.View):
    def __init__(self):
        super().__init__()
        self.money_timer = 0
        self.background = arcade.load_texture('resurses/pole.jpg')
        self.cards_list = arcade.SpriteList()
        self.towers_list = arcade.SpriteList()
        self.bullets_list = arcade.SpriteList()
        self.enemies_list = arcade.SpriteList()
        self.batch = Batch()

        self.metronome = 0

        self.money = 100
        self.money_label = arcade.Text(f"Монеты: {self.money}", 800, 550, arcade.color.WHITE, 18, batch=self.batch)
        self.timer = 0

        self.held_unit = None
        self.held_unit_type = None
        self.held_unit_price = None

        self.grid = [[0 for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]

    def setup(self):
        card_1 = Metronome()
        card_1.center_x = 80
        card_1.center_y = 500
        self.cards_list.append(card_1)

        card_2 = Strings()
        card_2.center_x = 80
        card_2.center_y = 400
        self.cards_list.append(card_2)

    def on_draw(self):
        self.clear()
        arcade.draw_texture_rect(self.background,
                                 arcade.rect.XYWH(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, SCREEN_WIDTH, SCREEN_HEIGHT))

        for row in range(GRID_ROWS):
            for col in range(GRID_COLS):
                x = GRID_START_X + col * TILE_SIZE
                y = GRID_START_Y + row * TILE_SIZE
                arcade.draw_rect_outline(arcade.rect.XYWH(x + TILE_SIZE / 2, y + TILE_SIZE / 2, TILE_SIZE, TILE_SIZE),
                                         arcade.color.BLACK)

        self.cards_list.draw()
        self.towers_list.draw()

        if self.held_unit:
            arcade.draw_sprite(self.held_unit)
        self.batch.draw()
        self.bullets_list.draw()
        self.enemies_list.draw()

    def on_mouse_press(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_LEFT:
            cards = arcade.get_sprites_at_point((x, y), self.cards_list)

            if len(cards) > 0:
                clicked_card = cards[0]
                if clicked_card.price > self.money:
                    return

                self.held_unit = clicked_card.clone()
                self.held_unit.alpha = 150
                self.held_unit.center_x = x
                self.held_unit.center_y = y
        else:
            enemies = arcade.get_sprites_at_point((x, y), self.towers_list)
            if len(enemies) > 0:
                enemy = enemies[0]
                col = int((x - GRID_START_X) // TILE_SIZE)
                row = int((y - GRID_START_Y) // TILE_SIZE)
                self.grid[row][col] = 0
                print(f"Уничтожили {enemy.unit_type} в ячейке {row}, {col}")
                if enemy.unit_type == 'Metronome':
                    self.metronome -= 1
                self.towers_list.remove(enemy)

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if self.held_unit:
            self.held_unit.center_x = x
            self.held_unit.center_y = y

    def on_mouse_release(self, x, y, button, modifiers):
        if not self.held_unit:
            return

        col = int((x - GRID_START_X) // TILE_SIZE)
        row = int((y - GRID_START_Y) // TILE_SIZE)

        if 0 <= col < GRID_COLS and 0 <= row < GRID_ROWS:
            if self.grid[row][col] == 0 and self.held_unit.price <= self.money:

                snap_x = GRID_START_X + col * TILE_SIZE + TILE_SIZE / 2
                snap_y = GRID_START_Y + row * TILE_SIZE + TILE_SIZE / 2

                new_tower = self.held_unit.clone()
                new_tower.center_x = snap_x
                new_tower.center_y = snap_y
                self.towers_list.append(new_tower)
                if self.held_unit.unit_type == 'Metronome':
                    self.metronome += 1
                self.grid[row][col] = 1
                print(f"Поставили {self.held_unit.unit_type} в ячейку {row}, {col}")
                self.money -= self.held_unit.price

            else:
                print("Клетка занята!")
        else:
            print("Мимо поля!")
        self.held_unit = None
        print(self.towers_list)

    def on_update(self, delta_time):
        self.money_label.text = f"Монеты: {self.money}"
        self.money_timer += delta_time
        self.timer += delta_time
        self.bullets_list.update()
        self.enemies_list.update()
        if self.money_timer >= 5:
            if self.metronome >= 1:
                self.money += 10 * self.metronome
                self.money_label.text = f"Монеты: {self.money}"
            self.money_timer = 0

        elif self.timer >= 10:
            start_x = TILE_SIZE * 13
            start_y = TILE_SIZE * random.randint(1, 4)
            ghost = Ghost()
            ghost.center_x = start_x
            ghost.center_y = start_y
            self.enemies_list.append(ghost)
            print('ghost')
            self.timer = 0


        for i in self.towers_list:
            if i.unit_type == 'Strings':
                i.timer += delta_time
                if i.timer >= 5:
                    # print('fire')
                    bullet = Bullet(i.center_x, i.center_y, SCREEN_WIDTH, i.center_y, i.bullet_speed, i.bullet_damage)
                    self.bullets_list.append(bullet)
                    i.timer = 0
        for i in self.cards_list:
            if self.money < i.price:
                i.alpha = 100
            else:
                i.alpha = 255


        for bullet in self.bullets_list:
            enimes = arcade.check_for_collision_with_list(bullet, self.enemies_list)
            if enimes:
                bullet.remove_from_sprite_lists()
                for enemy in enimes:
                    if enemy.health > 0:
                        enemy.health -= bullet.damage
                        if enemy.health <= 0:
                            enemy.remove_from_sprite_lists()
                            self.money += 10
                            print(f'{enemy.unit_type} убит')
                            self.money_label.text = f"Монеты: {self.money}"

        for enemy in self.enemies_list:
            towers = arcade.check_for_collision_with_list(enemy, self.towers_list)
            if towers:
                for tower in towers:
                    if tower.health > 0 and enemy.coaldown <= 0:
                        tower.health -= enemy.damage
                        enemy.center_x = tower.center_x
                    elif tower.health > 0 and enemy.coaldown > 0:
                        enemy.coaldown -= delta_time
                        enemy.center_x = tower.center_x
                    if tower.health <= 0:
                        if tower.unit_type == 'Metronome':
                            self.metronome -= 1
                        tower.remove_from_sprite_lists()
                        print(f'{tower.unit_type} убит')





