import json

import app
import requests
from app_components import Menu, clear_background, line_height, one_pt, layout
from events.input import Buttons, BUTTON_TYPES, ButtonDownEvent
from system.eventbus import eventbus

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
    loading = False

    error = None

    def __init__(self):
        self.menu = Menu(
            self,
            [],
            select_handler=self.select_handler,
            back_handler=self.back_handler,
        )
        self.menu._cleanup()
        self.layout = layout.LinearLayout(items=[])
        self.button_states = Buttons(self)
        eventbus.on_async(ButtonDownEvent, self._button_handler, self)
        self._refresh_data()

    def update_menu(self):
        # this is set to zero to prevent it being larger than the number of items in the list
        self.menu.position = 0
        self.layout.height = 0

        # set the menu items for the main menu
        if self.category is None:
            self.menu.menu_items = [
                category for category in self.data.keys()
            ] + [f"Bar: {self.bar}", "Refresh"]
            return

        # set the menu item for if there's no drinks in the category
        if len(self.data[self.category]) == 0:
            self.layout.items = [
                layout.DefinitionDisplay("", "Nothing here :(")
            ]
            return

        # set the menu items for drinks in the category
        self.layout.items = []

        for item in self.data[self.category]:
            self.layout.items.append(layout.DefinitionDisplay(
                f"£{item['stocktype']['price']}/{item['stocktype']['sale_unit_name']}, {float(item['remaining_pct']):.1f}% remaining",
                item['stocktype']['fullname']
            ))

    async def _button_handler(self, event):
        if BUTTON_TYPES["CANCEL"] in event.button:
            self.back_handler()
            return

        if self.category is None:
            self.menu._handle_buttondown(event)
        else:
            await self.layout.button_event(event)

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

            self.category = item

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

        if self.loading:
            ctx.text_align = ctx.CENTER
            ctx.gray(1).move_to(0, 0).text("Loading...")
            return

        if self.error:
            ctx.text_align = ctx.CENTER
            ctx.rgb(1, 0, 0).move_to(0, -10).text("Error!")
            ctx.rgb(1, 0, 0).move_to(0, 10).text(self.error)
            return

        if self.category is not None:
            self.layout.draw(ctx)
            return

        self.menu.draw(ctx)

    def update(self, delta):
        self.menu.update(delta)

    def background_update(self, delta):
        if self.loading:
            print("loading start")
            try:
                bar_json = requests.get(ENDPOINT_URLS[self.bar])
            except:
                self.error = "Something went wrong\nloading bar data.\nPlease try again"
                self.loading = False
                self.update_menu()
                return

            self.data = json.loads(bar_json.text)

            self.sub_menu = None
            self.update_menu()
            print("loading end")
            self.loading = False

    def _refresh_data(self):
        self.loading = True


__app_export__ = BarApp
