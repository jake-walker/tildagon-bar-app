import app
import ujson
import urequests
from app_components import Menu, clear_background, line_height, one_pt
from events.input import Buttons


class BarApp(app.App):
    data = {}

    # what bar to get data for - main/cybar
    bar = "main"
    # what drink category - first level of data keys
    category = None
    # what drink index within the category
    drink_index = None

    # font size for main menu
    main_menu_font_size = 12
    # font size for drink and drink details menus
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
        # this is set to zero to prevent it being larger than the number of items in the list
        self.menu.position = 0

        # set the menu style
        if self.category is None:
            # main menu
            self.menu.item_font_size = self.main_menu_font_size * one_pt
            self.menu.focused_item_font_size = (self.main_menu_font_size + 4) * one_pt
            self.menu.item_line_height = self.menu.item_font_size * line_height
        else:
            # drinks menu or drink details
            self.menu.item_font_size = self.sub_menu_font_size * one_pt
            self.menu.focused_item_font_size = (self.sub_menu_font_size + 4) * one_pt
            self.menu.item_line_height = self.menu.item_font_size * 1.1

        # set the menu items for a selected drink
        if self.drink_index is not None:
            drink = self.data[self.category][self.drink_index]
            self.menu.menu_items = [
                f"{drink['stocktype']['manufacturer']} {drink['stocktype']['name']}",
                f"{drink['stocktype']['abv']}% ABV",
                f"{float(drink['remaining_pct']):.01f}% Remaining",
                f"£{drink['stocktype']['price']}/{drink['stocktype']['sale_unit_name']}",
            ]
            return

        # set the menu items for the main menu
        if self.category is None:
            self.menu.menu_items = [
                category.title() for category in self.data.keys()
            ] + [f"Bar: {self.bar}", "Refresh"]
            return

        # set the menu item for if there's no drinks in the category
        if len(self.data[self.category]) == 0:
            self.menu.menu_items = ["Nothing here :("]
            return

        # set the menu items for drinks in the category
        self.menu.menu_items = list(
            [
                (item["stocktype"]["manufacturer"] + " " + item["stocktype"]["name"])
                for item in self.data[self.category]
            ]
        )

    def select_handler(self, item):
        if self.category is None:
            # main menu
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

            # convert the item back to lower (as it is converted to title when displayed)
            self.category = item.lower()
        elif self.drink_index is None:
            self.drink_index = self.menu.position

        self.update_menu()

    def back_handler(self):
        if self.drink_index is not None:
            # if in drink details, unsetting the drink id takes back to the drinks list
            self.drink_index = None
            self.update_menu()
        elif self.category is not None:
            # if in drinks list, unsetting the category goes back to the main menu
            self.category = None
            self.update_menu()
        else:
            # if at the main menu, quit the app
            self.minimise()

    def draw(self, ctx):
        clear_background(ctx)
        self.menu.draw(ctx)

    def update(self, delta):
        self.menu.update(delta)

    def _refresh_data(self):
        try:
            bar_json = urequests.get("http://localhost:8000/api/on-tap.json")
            # todo: confirm ujson is on the badge
            self.data = ujson.loads(bar_json.text)
        except:  # noqa
            # todo: show this error message somewhere
            self.error = "Could not get bar data"
            self.data = {}

        self.sub_menu = None
        self.update_menu()
