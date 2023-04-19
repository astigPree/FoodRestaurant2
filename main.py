
from kivy.core.window import Window
#Window.fullscreen = 'auto'
Window.size = (1000 , 600)

from kivymd.app import MDApp
from kivy.uix.boxlayout import BoxLayout
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.behaviors import CommonElevationBehavior, RectangularRippleBehavior
from kivymd.uix.gridlayout import MDGridLayout

from kivy.properties import ObjectProperty , ListProperty , StringProperty , BooleanProperty , NumericProperty
from kivy.lang.builder import Builder
from kivy.core.text import LabelBase
from kivy.animation import Animation
from kivy.clock import Clock

import backend
from copy import deepcopy

# ======> Activity Buttons
class ActivityButtons(BoxLayout):

    def clearData(self):
        self.parent.parent.clearData()

    def createReciept(self):
        self.parent.parent.createReciept()

# ======> Selected Items
class SelectedItemInformation(BoxLayout):
    price = NumericProperty(0)
    quantity = NumericProperty(0)
    name = StringProperty('barbeque (5 pcs)')

    def update(self , name , price , quantity):
        self.name = name
        self.price = price
        self.quantity = quantity


class SelectedItems(BoxLayout):

    list_of_data : MDGridLayout = ObjectProperty()

    total = NumericProperty(0)
    quantity = NumericProperty(0)

    def on_kv_post(self, base_widget):
        Clock.schedule_interval(self.displayTheSelectedFood , 1 /30)

    def displayTheSelectedFood(self , interval ):
        if not self.parent.parent.data.get_selected_foods() and self.list_of_data.children:
            self.list_of_data.clear_widgets()
            self.total , self.quantity = self.parent.parent.data.get_total_of_selected()
            return

        self.list_of_data.clear_widgets()
        self.parent.parent.displayAllSelectedData()
        self.total, self.quantity = self.parent.parent.data.get_total_of_selected()


# ======> List Of Items
class ItemModifier(MDBoxLayout , CommonElevationBehavior , RectangularRippleBehavior):

    food_id = StringProperty('')
    pic_source = StringProperty('')
    selected = BooleanProperty(False)
    food_name = StringProperty('')
    food_price = NumericProperty(0)


    def addButton(self):
        # add button event
        self.parent.parent.parent.parent.addButton(self.food_id)
        self.selected = self.parent.parent.parent.parent.checkInOrOut(self.food_id)

    def minButton(self):
        # minus button event
        self.parent.parent.parent.parent.minButton(self.food_id)
        self.selected = self.parent.parent.parent.parent.checkInOrOut(self.food_id)

    def update(self , food_id , picture , food_name , food_price , quantity ):
        self.food_id = food_id
        self.pic_source = picture
        self.food_name = food_name
        self.food_price = food_price
        self.selected = True if quantity else False
        Animation(elevation = 3 , shadow_softness = 9 , shadow_offset = (-5, 8) , duration=.2).start(self)


class ListOfItems(BoxLayout):

    item_displayer : MDGridLayout = ObjectProperty()

    past_finding = StringProperty('')
    finding = StringProperty('')

    def on_kv_post(self, base_widget):
        Clock.schedule_interval(self.searchFoods, 1 / 30)

    def searchFoods(self, interval) :
        if self.finding == self.past_finding :
            return
        self.past_finding = self.finding
        if not self.finding :
            self.parent.displayAllFoods()
            return
        self.item_displayer.clear_widgets()
        for key in self.parent.data.search_food(self.finding) :
            widget = self.parent.empty_widget.pop() if self.parent.empty_widget else ItemModifier()
            widget.update(
                food_id=key,
                picture=self.parent.data.foods_list[key][0],
                food_name=self.parent.data.foods_list[key][1],
                food_price=self.parent.data.foods_list[key][2],
                quantity=self.parent.data.foods_list[key][3]
            )
            self.item_displayer.add_widget(widget)
        print(f"List Of Items : {len(self.parent.empty_widget)}")
        print(f"List Of Selected Items : {len(self.parent.empty_widget_2)}")

# ======> Main Widget
class MainWidget(BoxLayout):

    data = backend.DataManagement('pictures' , 'database' , 'reciepts folder' )

    empty_widget: list = ListProperty([])  # for List Of Foods
    empty_widget_2: list = ListProperty([])  # for List Of Selected Foods

    list_of_items: ListOfItems = ObjectProperty()
    selected_items : SelectedItems = ObjectProperty()

    # ------> Activity Buttons ==========================================================
    def clearData(self):
        self.data.reset_foods_list()
        self.displayAllFoods()

    def createReciept(self):
        self.data.create_reciept('')

    # ------> Selected Items ============================================================
    def displayAllSelectedData(self):
        for food in self.data.get_selected_info():
            widget = self.empty_widget_2.pop() if self.empty_widget else SelectedItemInformation()
            widget.update(
                name=food[0],
                price=food[1] ,
                quantity= food[2]
            )
            self.selected_items.list_of_data.add_widget(widget)

    # ------> List Of Items =============================================================
    def createEmptyWidget(self, interval) :
        empty_range = len(self.data.foods_list) * 2
        for _ in range(empty_range) :
            if len(self.empty_widget) >= empty_range :
                break
            widget = ItemModifier()
            self.empty_widget.append(widget)

        for _ in range(empty_range) :
            if len(self.empty_widget_2) >= empty_range :
                break
            widget = SelectedItemInformation()
            self.empty_widget_2.append(widget)

        Clock.schedule_once(self.createEmptyWidget)

    # -----> Built In Functions
    def on_kv_post(self, base_widget) :
        Clock.schedule_once(self.createEmptyWidget)
        self.displayAllFoods()

    def addButton(self, key: str) :
        self.data.add_quantity_to(key)

    def minButton(self, key: str) :
        self.data.min_quantity_to(key)

    def checkInOrOut(self, key: str) -> bool :
        if self.data.foods_list[key][-1] > 0 :
            return True
        return False

    def displayAllFoods(self) :
        self.list_of_items.item_displayer.clear_widgets()
        for food_id, food_data in self.data.foods_list.items() :
            print(food_data)
            widget = self.empty_widget.pop() if self.empty_widget else ItemModifier()
            widget.update(food_id=food_id, picture=food_data[0], food_name=food_data[1], food_price=food_data[2],
                          quantity=food_data[3])
            self.list_of_items.item_displayer.add_widget(widget)
        print(f"List Of Items : {len(self.empty_widget)}")
        print(f"List Of Selected Items : {len(self.empty_widget_2)}")


# ======> Application
class FoodRestaurantDesktopApp(MDApp):

    icon = "pictures/coca cola,30.png"

    def build(self):
        return Builder.load_file("design.kv")

if __name__ == '__main__':
    LabelBase.register(name= 'title_font' , fn_regular="fonts/MADE Tommy Soft Bold PERSONAL USE.otf")
    LabelBase.register(name='text_font' , fn_regular="fonts/MADE Tommy Soft Black PERSONAL USE.otf")
    LabelBase.register(name='number_font' , fn_regular="fonts/MADE Tommy Soft Regular PERSONAL USE.otf")
    FoodRestaurantDesktopApp().run()