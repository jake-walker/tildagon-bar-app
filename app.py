import json

import app
import urequests
from app_components import Menu, clear_background, line_height, one_pt
from events.input import Buttons

ENDPOINT_URLS = {
    "robot_arms": "https://bar.emf.camp/api/on-tap.json",
    "cybar": "https://bar.emf.camp/api/cybar-on-tap.json",
}


class BarApp(app.App):
    data = {}

    # what bar to get data for - main/cybar
    bar = "robot_arms"
    # what drink category - first level of data keys
    category = None

    # font size for main menu
    main_menu_font_size = 12
    # font size for drink and drink details menus
    sub_menu_font_size = 7

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
            # drinks menu
            self.menu.item_font_size = self.sub_menu_font_size * one_pt
            self.menu.focused_item_font_size = self.sub_menu_font_size * one_pt
            self.menu.item_line_height = self.menu.item_font_size * 2.1

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
                f"{item['stocktype']['fullname']}\n£{item['stocktype']['price']}/{item['stocktype']['sale_unit_name']}, {float(item['remaining_pct']):.1f}% remaining"
                for item in self.data[self.category]
            ]
        )

    def select_handler(self, item, _):
        if self.category is None:
            # main menu
            if item.startswith("Bar:"):
                if self.bar == "robot_arms":
                    self.bar = "cybar"
                else:
                    self.bar = "robot_arms"

                self._refresh_data()
                return
            elif item == "Refresh":
                self._refresh_data()
                return

            # convert the item back to lower (as it is converted to title when displayed)
            self.category = item.lower()

        self.update_menu()

    def back_handler(self):
        if self.category is None or self.error is not None:
            self.minimise()

        if self.category is not None:
            # if in drinks list, unsetting the category goes back to the main menu
            self.category = None
            self.update_menu()

    def draw(self, ctx):
        clear_background(ctx)

        if self.error:
            ctx.text_align = ctx.CENTER
            ctx.font_size = self.main_menu_font_size * one_pt
            ctx.rgb(1, 0, 0).move_to(0, -10).text("Error!")
            ctx.font_size = self.sub_menu_font_size * one_pt
            ctx.rgb(1, 0, 0).move_to(0, 10).text(self.error)
            return

        self.menu.draw(ctx)

    def update(self, delta):
        self.menu.update(delta)

    def _refresh_data(self):
        try:
            bar_json = urequests.get(ENDPOINT_URLS[self.bar])
            self.data = json.loads(bar_json.text)
        except Exception as ex:
            print("Failed to get bar data", ex)
            self.error = (
                "Could not get bar data!\n"
                "Make sure you are connected to\n"
                "the internet."
            )
            self.data = {}

        self.sub_menu = None
        self.update_menu()


__app_export__ = BarApp
