import arcade
from arcade.gui import UIManager, UIFlatButton, UITextureButton, UILabel, UIInputText, UITextArea, UISlider, UIDropdown, \
    UIMessageBox  # Это разные виджеты
from arcade.gui.widgets.layout import UIAnchorLayout, UIBoxLayout

# Константы
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 600
TITLE = "Шум против Тишины"

# Состояния игры
STATE_MENU = 0
STATE_COMBAT = 1
STATE_EXPLORE = 2
STATE_DIALOGUE = 3


class GameWindow(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, TITLE)
        self.state = STATE_MENU

        # Инициализация "Видов"
        self.menu_view = MenuView()
        self.combat_view = CombatView()  # PvZ режим
        self.explore_view = ExploreView()  # Stardew режим

    def setup(self):
        self.show_view(self.menu_view)


class MenuView(arcade.View):
    def __init__(self):
        super().__init__()
        self.background = arcade.load_texture("resurses/menu.jpg")

        self.manager = UIManager()
        self.manager.enable()

        self.anchor_layout = UIAnchorLayout(width=SCREEN_WIDTH / 2, height=SCREEN_HEIGHT / 2, x=-SCREEN_WIDTH / 4)
        self.box_layout = UIBoxLayout(vertical=True, space_between=30, align='center', width=SCREEN_WIDTH)

        self.setup_widgets()

        self.anchor_layout.add(self.box_layout)
        self.manager.add(self.anchor_layout)

    def setup_widgets(self):
        label = UILabel("Шум против Тишины",
                        font_size=20,
                        text_color=arcade.color.WHITE)
        start_text = UIFlatButton(text='Начать',
                                  font_size=16,
                                  text_color=arcade.color.WHITE)
        start_text.on_click = lambda event: self.window.show_view(self.window.combat_view)
        settings_text = UIFlatButton(text='Настройки',
                                     font_size=16,
                                     text_color=arcade.color.WHITE)
        exit_text = UIFlatButton(text='Выход',
                                 font_size=16,
                                 text_color=arcade.color.WHITE)

        self.box_layout.add(label)
        self.box_layout.add(start_text)
        self.box_layout.add(settings_text)
        self.box_layout.add(exit_text)

    def on_draw(self):
        self.clear()
        arcade.draw_texture_rect(self.background,
                                 arcade.rect.XYWH(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, SCREEN_WIDTH, SCREEN_HEIGHT))
        self.manager.draw()


class CombatView(arcade.View):
    """ Режим PvZ """

    def __init__(self):
        super().__init__()
        self.background = arcade.load_texture("resurses/pole.jpg")
        self.boomboxes = arcade.SpriteList()
        self.towers = arcade.SpriteList()
        self.enemies = arcade.SpriteList()
        self.bullets = arcade.SpriteList()
        self.score = 0
        self.setup()

    def setup(self):
        for i in range(1,6):
            boombox = arcade.Sprite("resurses/boombox.png", 0.3)
            boombox.center_x = 100
            boombox.center_y = 100 * i
            self.boomboxes.append(boombox)

    def on_draw(self):
        self.clear()
        arcade.draw_texture_rect(self.background,
                                 arcade.rect.XYWH(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, SCREEN_WIDTH, SCREEN_HEIGHT))
        self.boomboxes.draw()

    def on_update(self, delta_time):
        pass

    def end_battle(self):
        explore = self.window.explore_view
        explore.setup()
        self.window.show_view(explore)


class ExploreView(arcade.View):
    """ Режим Stardew (Город) """

    def setup(self):
        pass

    def on_draw(self):
        self.clear()

    def on_key_press(self, key, modifiers):
        pass


# Запуск
def main():
    window = GameWindow()
    window.setup()
    arcade.run()


if __name__ == "__main__":
    main()
