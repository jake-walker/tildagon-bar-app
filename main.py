import app
import ujson
import urequests
from app_components import Menu, clear_background, line_height, one_pt
from events.input import Buttons


class BarApp(app.App):
    data = {}

    bar = "main"
    category = None
    drink_index = None

    main_menu_font_size = 12
    sub_menu_font_size = 6

    error = None

    def __init__(self):
        self.menu = Menu(
            self,
            [],
            select_handler=self.select_handler,
            back_handler=self.back_handler,
        )
        self.button_states = Buttons(self)
        self._refresh_data()

    def update_menu(self):
        self.menu.position = 0

        if self.category is None:
            self.menu.item_font_size = self.main_menu_font_size * one_pt
            self.menu.focused_item_font_size = (self.main_menu_font_size + 4) * one_pt
            self.menu.item_line_height = self.menu.item_font_size * line_height
        else:
            self.menu.item_font_size = self.sub_menu_font_size * one_pt
            self.menu.focused_item_font_size = (self.sub_menu_font_size + 4) * one_pt
            self.menu.item_line_height = self.menu.item_font_size * 1.1

        if self.drink_index is not None:
            drink = self.data[self.category][self.drink_index]
            self.menu.menu_items = [
                f"{drink['stocktype']['manufacturer']} {drink['stocktype']['name']}",
                f"{drink['stocktype']['abv']}% ABV",
                f"{float(drink['remaining_pct']):.01f}% Remaining",
                f"£{drink['stocktype']['price']}/{drink['stocktype']['sale_unit_name']}",
            ]
            return

        if self.category is None:
            self.menu.menu_items = [
                category.title() for category in self.data.keys()
            ] + [f"Bar: {self.bar}", "Refresh"]
            return

        if len(self.data[self.category]) == 0:
            self.menu.menu_items = ["Nothing here :("]
            return

        self.menu.menu_items = list(
            [
                (item["stocktype"]["manufacturer"] + " " + item["stocktype"]["name"])
                for item in self.data[self.category]
            ]
        )

    def select_handler(self, item):
        if self.category is None:
            if item.startswith("Bar:"):
                if self.bar == "main":
                    self.bar = "cybar"
                else:
                    self.bar = "main"

                self._refresh_data()
                return
            elif item == "Refresh":
                self._refresh_data()
                return

            self.category = item.lower()
        elif self.drink_index is None:
            self.drink_index = self.menu.position

        self.update_menu()

    def back_handler(self):
        if self.drink_index is not None:
            self.drink_index = None
            self.update_menu()
        elif self.category is not None:
            self.category = None
            self.update_menu()
        else:
            self.minimise()

    def draw(self, ctx):
        clear_background(ctx)
        self.menu.draw(ctx)

    def update(self, delta):
        self.menu.update(delta)

    def _refresh_data(self):
        try:
            bar_json = urequests.get("http://localhost:8000/api/on-tap.json")
            self.data = ujson.loads(bar_json.text)
        except:
            self.error = "Could not get bar data"
            self.data = {}

        self.sub_menu = None
        self.update_menu()
