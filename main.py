from time import sleep

import arcade
from arcade.gui import UIManager, UIFlatButton, UITextureButton, UILabel, UIInputText, UITextArea, UISlider, UIDropdown, \
    UIMessageBox  # Это разные виджеты
from arcade.gui.widgets.layout import UIAnchorLayout, UIBoxLayout
from fight import CombatView
from city import City

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

        self.menu_view = MenuView()
        self.combat_view = CombatView()  # PvZ режим
        self.explore_view = City()  # Stardew режим

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

        self.fade_alpha = 0  # Текущая прозрачность (0 - прозрачно, 255 - темно)
        self.fade_speed = 150
        self.is_fading = False

        self.all_lines = [
            "Когда почувствуешь,",
            "Что дно уже видно,",
            "И высь сокрыта тьмой,",
            "Непробиваемой браней,",
            "То не глупи",
            "И будь смелей:",
            "Не только тьма на дне морей."
        ]
        self.text_objects = []  #
        self.current_line_index = 0
        self.visible_chars = 0
        self.typing_speed = 0.02
        self.timer = 0
        self.intro = True



    def setup_widgets(self):
        label = UILabel("Шум против Тишины",
                        font_size=20,
                        text_color=arcade.color.WHITE)
        start_text = UIFlatButton(text='Начать',
                                  font_size=16,
                                  text_color=arcade.color.WHITE)

        def start_game(event):
            self.is_fading = True

        start_text.on_click = start_game
        settings_text = UIFlatButton(text='Настройки',
                                     font_size=16,
                                     text_color=arcade.color.WHITE)
        exit_text = UIFlatButton(text='Выход',
                                 font_size=16,
                                 text_color=arcade.color.WHITE)
        exit_text.on_click = lambda event: arcade.exit()

        self.box_layout.add(label)
        self.box_layout.add(start_text)
        self.box_layout.add(settings_text)
        self.box_layout.add(exit_text)

    def on_draw(self):
        self.clear()
        arcade.draw_texture_rect(self.background,
                                 arcade.rect.XYWH(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, SCREEN_WIDTH, SCREEN_HEIGHT))
        self.manager.draw()
        if self.fade_alpha > 0:
            arcade.draw_lrbt_rectangle_filled(
                0, SCREEN_WIDTH, 0, SCREEN_HEIGHT,
                (0, 0, 0, int(self.fade_alpha))
            )
        if self.fade_alpha == 255:
            for i in range(self.current_line_index):
                arcade.draw_text(self.all_lines[i], 100, 500 - i * 40, arcade.color.WHITE, 20)



            if self.current_line_index < len(self.all_lines):
                current_text = self.all_lines[self.current_line_index][:self.visible_chars]

                arcade.draw_text(current_text, 100, 500 - self.current_line_index * 40, arcade.color.WHITE, 20)

    def on_update(self, delta_time):
        if self.is_fading:
            self.fade_alpha += self.fade_speed * delta_time
            if self.fade_alpha >= 255:
                self.fade_alpha = 255
                if self.current_line_index < len(self.all_lines):
                    self.timer += delta_time
                    if self.timer >= self.typing_speed:
                        self.timer = 0
                        self.visible_chars += 1
                        if self.visible_chars > len(self.all_lines[self.current_line_index]):
                            self.current_line_index += 1
                            self.visible_chars = 0
                else:
                    sound = arcade.load_sound('resurses/ring.mp3')
                    arcade.play_sound(sound)
                    self.window.explore_view.setup()
                    self.window.show_view(self.window.explore_view)
            return



# Запуск
def main():
    window = GameWindow()
    window.setup()
    arcade.run()


if __name__ == "__main__":
    main()
