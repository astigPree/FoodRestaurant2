# pip install fuzzywuzzy
# pip install python-Levenshtein


import os
import sys
import typing as tp
from fuzzywuzzy import fuzz
import json
import prettytable
from datetime import datetime
from uuid import uuid4


class DataManagement:
    __slots__ = ("foods_list", "folder", "folderbase", "past_foods_list", "recieptfolder")

    def __init__(self, folder: str, database: str, f_reciept: str):
        self.folderbase = os.path.join(os.getcwd(), database)
        self.folder = os.path.join(os.getcwd(), folder)
        self.recieptfolder = os.path.join(os.getcwd(), f_reciept)
        self.foods_list = {}  # { id : [ filename , name , price , quantity  ] }
        self.past_foods_list = {}  # { filename : { id : [ filename , name , price , quantity  ] } }

        self.get_foods_in_folder()  # Load all file and datas
        print(self.foods_list)

    # ===== Calculations Of Data

    def get_selected_info(self) -> list[tuple[str, float, int], ...]:
        selected = self.get_selected_foods()
        if not selected:
            return []

        info = []
        for key in selected:
            name = self.foods_list[key][1]
            price = float(self.foods_list[key][2])
            quan = int(self.foods_list[key][3])
            info.append((name, price * quan, quan))
        return info

    def get_total_of_selected(self) -> tp.Union[None, tuple[float, int]]:
        selected = self.get_selected_foods()
        if not selected:
            return 0 , 0

        total_price = 0
        total_quan = 0
        for key in selected:
            price = float(self.foods_list[key][2])
            quan = int(self.foods_list[key][3])
            total_price = total_price + (quan * price)
            total_quan = total_quan + quan
        return (total_price, total_quan)

    # ===== File Getter and Modification
    def load_all_past_selected(self):
        for file in self.folderbase:
            self.load_past_selected(file)

    def load_past_selected(self, filename: str):
        directory = os.path.join(self.folderbase, filename)
        if not os.path.exists(directory):
            raise FileNotFoundError(f"[ ! ] File not found in past transaction : {filename} ")

        with open(directory, 'r') as jf:
            past_data = json.load(jf)
            self.past_foods_list[filename] = past_data

    def save_selected(self, filename: str):
        selected = self.get_selected_foods()
        if not selected:
            raise ValueError("[ ! ] Should atleast 1 selected foods to save it ")

        foods = {key: tuple(self.foods_list[key]) for key in selected}
        with open(os.path.join(self.folderbase, filename), "w") as jf:
            json.dump(foods, jf)

    def min_quantity_to(self, f_id=None):
        if not f_id:
            return False
        if self.foods_list[f_id][3] == 0:
            return False
        self.foods_list[f_id][3] -= 1
        return True

    def add_quantity_to(self, f_id=None) -> bool:
        if not f_id:
            return False
        self.foods_list[f_id][3] += 1
        return True

    def update_foods_list(self, key : str , values : list):
        for food_id in self.foods_list :
            if key == food_id :
                break
        else :
            raise ValueError(f"[ ! ] Can't update because {key} does not exist")
        for n , value in enumerate(values) :
            self.foods_list[key][n] = value

    def reset_foods_list(self):
        for key in self.foods_list:
            self.foods_list[key][3] = 0

    def get_selected_foods(self) -> tp.Union[list[str, ...], None]:
        found = []
        for key, values in self.foods_list.items():
            if values[3] > 0:
                found.append(key)
        if found:
            return found
        else:
            return None

    def search_food(self, find=None) -> tp.Union[list[str, ...], None]:
        if not find:
            return None

        found = []
        passing = 45
        for key, values in self.foods_list.items():
            ratio = []
            if fuzz.WRatio(str(values[2]), find) > passing:
                ratio.append(fuzz.WRatio(str(values[2]), find))
            if fuzz.WRatio(str(values[1]), find) > passing:
                ratio.append(fuzz.WRatio(str(values[1]), find))
            if fuzz.WRatio(key, find) > passing:
                ratio.append(fuzz.WRatio(key, find))
            if ratio :
                found.append( ( max(ratio) , key ) )

        found.sort(key = lambda x : x[0] , reverse=True)
        return [ food[1] for food in found  ]

    def get_foods_in_folder(self, sep=","):
        os.makedirs(self.folderbase, exist_ok=True)
        os.makedirs(self.recieptfolder, exist_ok=True)
        for num, file in enumerate(os.listdir(self.folder)):
            data = self.checking_format(file, sep)
            filename = os.path.join(self.folder, file)
            self.foods_list[f"{num + 100}"] = [filename, data[0], data[1], 0]

    def checking_format(self, file: str, sep: str) -> list[str, str]:
        data = os.path.splitext(file)[0]  # get the filename only
        data = data.split(sep)  # name , price

        if len(data) != 2:
            raise ValueError(f"[ ! ] Must be  ' filename {sep} price ' : {data} ")
        try:
            float(data[1])
            int(data[1])
        except ValueError:
            print(f"[ ! ] Must be ' filename {sep} price ' : {data[1]} should be numbers ")
            sys.exit()
        else:
            return data

    def create_reciept(self, filename: str):
        selected = self.get_selected_info() # name , total , quantity
        if not selected:
            #raise ValueError("[ ! ] Should atleast 1 selected foods to create reciept ")
            return

        if not filename :
            filename = datetime.now().strftime(f"TIME = %m-%d-%Y, %H-%M-%S [ FOOD ID = {str(uuid4().hex)[:10]} ].txt")

        myTable = prettytable.PrettyTable(["Food Name", "Price", "Quantity", "Total"])
        myTable.align = 'l'

        overall_total = 0
        overall_quantity = 0
        for data in selected :
            name = data[0]
            price = data[1] / data[2]
            quantity = data[2]
            total = data[1]
            myTable.add_row([name, f"Php {price}", f"{quantity}", f"Php {total}"])
            overall_total += total
            overall_quantity += quantity
        myTable.add_row(["" , "" , "" , ""])
        myTable.add_row(["" , "" , f"{overall_quantity}", f"Php {overall_total}" ])

        with open(os.path.join("reciepts folder" , filename), 'w' ) as rf :
            rf.write("Food Reciept : \n")
            rf.write(myTable.get_string(sortBy="Total" , reversed=True))


        os.system(f'notepad.exe {os.path.join(self.recieptfolder , filename)}')





if __name__ == "__main__":
    a = [ (20 , 'a') , (30 , 'b') , (10 , 'c') ]
    a.sort(key=lambda x : x[0] , reverse=True)
    print(a)
    #os.system('notepad.exe main.py')
    import webbrowser
    webbrowser.open('main.py')