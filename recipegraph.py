# -*- coding: utf-8 -*-
"""

@author: Mirko Ruether
"""

import copy
import re
import threading
from collections import Counter
from typing import List, Tuple, Dict
import pandas as pd

class Recipe():
    def __init__(self, resitemobj, rid, rtype, name, resamount, ingredients) -> None:
        self.rid:int = rid
        self.rtype:str = rtype
        self.name:str = name
        self.resitemobj:Item = resitemobj
        self.resamount:int = resamount
        self.ingredients:List[Tuple[Item, int]] = ingredients

    def __repr__(self) -> str:
        return f'<Recipe name={self.name}>'

class Item():
    def __init__(self, name:str) -> None:
        self.name:str = name
        self.recipes:List[Recipe] = []
        self.atomicrecipe:Recipe = self._build_recipe(
            'atomic', 'atomic:' + re.search(r'<(.*)>', name).group(1),
            1, [], id_override=999
        )

    def _build_recipe(
        self, rtype:str, recipename:str, resamount:int, ingredients:list, id_override=None
    ) -> Recipe:
        return Recipe(
            self, id_override if id_override else len(self.recipes),
            rtype, recipename, resamount, ingredients
        )

    def register_recipe(self, rtype:str, recipename:str, resamount:int, ingredients:list) -> None:
        self.recipes.append(self._build_recipe(rtype, recipename, resamount, ingredients))

    @property
    def recipes_full(self) -> list:
        return self.recipes + [self.atomicrecipe]

    def __repr__(self) -> str:
        return f'<Item name={self.name}>'

class RecipeGraph():
    _items:Dict[str, Item] = {}
    _lock = threading.RLock()

    def __init__(self, df_recipes:pd.DataFrame, forceatomic:List[str]=None) -> None:
        self.df_recipes:pd.DataFrame = df_recipes
        self.forceatomic:List[str] = forceatomic if forceatomic else []

    @property
    def items(self) -> Dict[str, Item]:
        with self._lock:
            return copy.deepcopy(self._items)

    @staticmethod
    def resolve_itemname(itemname:str):
        itemname = itemname.replace(':*', '')
        return re.search(r'<.*>', itemname).group(0)

    def get_item(self, itemname:str):
        with self._lock:
            if itemname in self._items:
                return self._items[itemname]
            itemobj = Item(itemname)
            self._items[itemname] = itemobj
            self.register_recipes(itemobj)
            return itemobj

    def register_recipes(self, itemobj:Item):
        if itemobj.name in self.forceatomic:
            return
        df_rf = self.df_recipes.loc[self.df_recipes['resitem'] == itemobj.name]
        for _, row in df_rf.iterrows():
            ingredient_name_amounts = Counter([
                RecipeGraph.resolve_itemname(x) for x in re.findall(r'<.+?>', row['craftraw'])
            ])
            itemobj.register_recipe(
                row['crafttype'], row['id'], row['amount'],
                [(self.get_item(k), v) for k, v in ingredient_name_amounts.items()]
            )

    def remove_unnecessary_oredicts(self):
        with self._lock:
            unnecessary_oredicts:Dict[str, Item] = {}
            for item in self._items.values():
                if item.name.startswith('<ore:'):
                    if len(item.recipes) == 1:
                        unnecessary_oredicts[item.name] = item.recipes[0].ingredients[0][0]

            for item in self._items.values():
                for recipe in item.recipes:
                    for i in range(len(recipe.ingredients)):
                        ingr_name = recipe.ingredients[i][0].name
                        ingr_amount = recipe.ingredients[i][1]
                        if ingr_name in unnecessary_oredicts:
                            recipe.ingredients[i] = (unnecessary_oredicts[ingr_name], ingr_amount)

            for un_ordict in unnecessary_oredicts:
                self._items.pop(un_ordict)

if __name__ == "__main__":
    df_r = pd.read_csv('recipes.csv')
    df_r = df_r.loc[
        df_r['id'].str.startswith('minecraft') |
        df_r['id'].str.startswith('harvestcraft') |
        df_r['id'].str.startswith('furnace') |
        df_r['id'].str.startswith('oredict')
    ].reset_index(drop=True)

    rg = RecipeGraph(df_r)

    myitem = rg.get_item('<harvestcraft:thankfuldinneritem>')
    # myitem = get_item('<minecraft:sticky_piston>')
    print(myitem)
