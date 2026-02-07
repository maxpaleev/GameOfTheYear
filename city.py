import arcade


SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 600

class City(arcade.View):
    def __init__(self):
        super().__init__()
        arcade.set_background_color(arcade.color.ASH_GREY)

        # Создаём спрайт игрока
        self.player_sprite = arcade.Sprite(":resources:images/animated_characters/female_person/femalePerson_idle.png", scale=0.5)
        self.player_sprite.center_x = SCREEN_WIDTH // 2
        self.player_sprite.center_y = SCREEN_HEIGHT // 2
        self.player_sprites = arcade.SpriteList()
        self.player_sprites.append(self.player_sprite)

    def on_draw(self):
        """Отрисовка всех спрайтов"""
        self.clear()
        self.player_sprites.draw()  # Отрисовываем игрока

    def on_update(self, delta_time):
        """Обновляем состояние игры"""
        self.player_sprite.update()


    def on_key_press(self, key, modifiers):
        """Обработка нажатий клавиш для управления игроком"""
        if key == arcade.key.W:
            self.player_sprite.change_y = 5
        elif key == arcade.key.S:
            self.player_sprite.change_y = -5
        elif key == arcade.key.A:
            self.player_sprite.change_x = -5
        elif key == arcade.key.D:
            self.player_sprite.change_x = 5

    def on_key_release(self, key, modifiers):
        """Остановка движения при отпускании клавиш"""
        if key == arcade.key.W or key == arcade.key.S:
            self.player_sprite.change_y = 0
        elif key == arcade.key.A or key == arcade.key.D:
            self.player_sprite.change_x = 0