import arcade
from pyglet.graphics import Batch

SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 600
TILE_SIZE = 64
GRID_ROWS = 5
GRID_COLS = 9
GRID_START_X = 200  # Отступ слева (место для Зомби/Тишины)
GRID_START_Y = 100




class Unit(arcade.Sprite):
    def __init__(self, unit_type, image, scale=1):
        super().__init__(image, scale)
        self.unit_type = unit_type

class Strings(Unit):
    def __init__(self):
        self.price = 50
        self.unit_type = 'Strings'
        self.health = 100
        self.bullet_speed = 10
        texture = 'resurses/strings.png'
        super().__init__(self.unit_type, texture, scale=0.1)

class Metronome(Unit):
    def __init__(self):
        self.price = 10
        self.unit_type = 'Metronome'
        self.health = 100
        self.bullet_speed = 10
        image = 'resurses/metronome.png'
        super().__init__(self.unit_type, image, scale=0.1)


class CombatView(arcade.View):
    def __init__(self):
        super().__init__()
        self.background = arcade.load_texture('resurses/pole.jpg')
        self.cards_list = arcade.SpriteList()
        self.towers_list = arcade.SpriteList()
        self.batch = Batch()
        self.metronome = 0
        self.money = 100
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

        self.money_text = arcade.Text(f"Монеты: {self.money}", 800, 550, arcade.color.WHITE, 18, batch=self.batch)

        self.cards_list.draw()
        self.towers_list.draw()

        if self.held_unit:
            arcade.draw_sprite(self.held_unit)
        self.batch.draw()

    def on_mouse_press(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_LEFT:
            cards = arcade.get_sprites_at_point((x, y), self.cards_list)

            if len(cards) > 0:
                clicked_card = cards[0]
                if clicked_card.price > self.money:
                    return

                self.held_unit_type = clicked_card.unit_type
                self.held_unit_price = clicked_card.price
                self.held_unit = arcade.Sprite(clicked_card.texture, scale=clicked_card.scale)
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
            if self.grid[row][col] == 0 and self.held_unit_price <= self.money:

                snap_x = GRID_START_X + col * TILE_SIZE + TILE_SIZE / 2
                snap_y = GRID_START_Y + row * TILE_SIZE + TILE_SIZE / 2

                new_tower = Unit(self.held_unit_type, self.held_unit.texture, self.held_unit.scale)
                new_tower.center_x = snap_x
                new_tower.center_y = snap_y
                self.towers_list.append(new_tower)
                if self.held_unit_type == 'Metronome':
                    self.metronome += 1
                self.grid[row][col] = 1
                print(f"Поставили {self.held_unit_type} в ячейку {row}, {col}")
                self.money -= self.held_unit_price
            else:
                print("Клетка занята!")
        else:
            print("Мимо поля!")
        self.held_unit = None

    def on_update(self, delta_time):
        self.timer += delta_time
        if self.metronome >= 1 and self.timer >= 5:
            self.money += 10 * self.metronome
            self.money_text.text = f"Монеты: {self.money}"
            self.timer = 0
        for i in self.cards_list:
            if self.money < i.price:
                i.alpha = 100
            else:
                i.alpha = 255

