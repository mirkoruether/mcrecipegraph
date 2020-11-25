# -*- coding: utf-8 -*-
"""

@author: Mirko Ruether
"""

from abc import ABC, abstractmethod
import re
import threading
from collections import Counter
from typing import List, Tuple, Dict
import pandas as pd

class RecipeGraphError(RuntimeError):
    pass

class RecipeNotFoundError(RecipeGraphError):
    pass

class Recipe():
    def __init__(self, name, recipetype, results, ingredients, recipegraph) -> None:
        self.name:str = name
        self.recipetype:str = recipetype
        self.recipegraph:RecipeGraph = recipegraph
        self.results:List[Tuple[Item, int]] = results
        self.ingredients:List[Tuple[Item, int]] = ingredients

    def __repr__(self) -> str:
        return f'<Recipe name={self.name}>'

class Item():
    def __init__(self, name, designation, recipegraph) -> None:
        self.name:str = name
        self.designation:str = designation
        self.recipegraph:RecipeGraph = recipegraph
        self.recipes_resolved:bool = False
        self.recipes:List[Recipe] = []
        self.usages_resolved:bool = False
        self.usages:List[Recipe] = []
        self.atomicrecipe:Recipe = None

    def resolve_recipes(self, recursive:bool=False):
        if self.recipes_resolved:
            return
        self.recipegraph.resolve_recipes(self)
        if recursive:
            for recipe in self.recipes:
                for item, _ in recipe.ingredients:
                    item.resolve_recipes(recursive=True)

    def resolve_usages(self, recursive:bool=False):
        if self.usages_resolved:
            return
        self.recipegraph.resolve_usages(self)
        if recursive:
            for usage in self.usages:
                for item, _ in usage.results:
                    item.resolve_usages(recursive=True)

    @property
    def recipes_full(self) -> list:
        return self.recipes + [self.atomicrecipe]

    def __repr__(self) -> str:
        return f'<Item name={self.name}>'

class RecipeGraph(ABC):
    @staticmethod
    def resolve_itemname(itemname:str):
        itemname = itemname.replace(':*', '')
        return re.search(r'<.*>', itemname).group(0)

    @abstractmethod
    def get_item(self, itemname:str) -> Item:
        pass

    @abstractmethod
    def get_recipe(self, recipename:str) -> Recipe:
        pass

    @abstractmethod
    def resolve_recipes(self, item:Item) -> List[Recipe]:
        pass

    @abstractmethod
    def resolve_usages(self, item:Item) -> List[Recipe]:
        pass

    def _clean_tree(self):
        pass

    def get_item_and_resolve_recipes(self, itemname:str):
        item = self.get_item(itemname)
        item.resolve_recipes(recursive=True)
        self._clean_tree()
        return item

class BasicRecipeGraph(RecipeGraph):
    _items:Dict[str, Item] = {}
    _recipes:Dict[str, Recipe] = {}
    _lock = threading.RLock()

    def __init__(self, df_recipes:pd.DataFrame, forceatomic:List[str]=None) -> None:
        self.df_recipes:pd.DataFrame = df_recipes
        self.forceatomic:List[str] = forceatomic if forceatomic else []   

    def get_item(self, itemname:str) -> Item:
        with self._lock:
            if itemname in self._items:
                return self._items[itemname]
            itemobj = Item(itemname, itemname, self)
            self._items[itemname] = itemobj
            itemobj.atomicrecipe = self.get_recipe(f'atomic:{itemobj.name[1:-1]}')
            return itemobj

    def get_recipe(self, recipename:str):
        with self._lock:
            if recipename in self._recipes:
                return self._recipes[recipename]
            if recipename.startswith('atomic:'):
                recipe = Recipe(
                    recipename,
                    'atomic',
                    [(self.get_item(f'<{recipename.split(":", 1)[1]}>'), 1)],
                    [],
                    self
                )
                self._recipes[recipename] = recipe
                return recipe
            elif recipename in self.df_recipes['id'].to_list():
                row = self.df_recipes.loc[self.df_recipes['id'] == recipename].iloc[0]
                recipe = Recipe(
                    recipename,
                    row['crafttype'],
                    [(self.get_item(row['resitem']), row['amount'])],
                    [(self.get_item(k), v) for k, v in Counter([
                        RecipeGraph.resolve_itemname(x) for x in re.findall(r'<.+?>', row['craftraw'])
                    ]).items()],
                    self
                )
                self._recipes[recipename] = recipe
                return recipe
            raise RecipeNotFoundError

    def resolve_recipes(self, item:Item) -> List[Recipe]:
        if item.recipes_resolved:
            return item.recipes
        if item.name in self.forceatomic:
            item.recipes_resolved = True
            return item.recipes
        for _, row in self.df_recipes.loc[self.df_recipes['resitem'] == item.name].iterrows():
            recipe = self.get_recipe(row['id'])
            item.recipes.append(recipe)
        item.recipes_resolved = True
        return item.recipes

    def resolve_usages(self, item:Item) -> List[Recipe]:
        raise RuntimeError('Unsupported')

    def _clean_tree(self):
        self.remove_unnecessary_oredicts()

    def remove_unnecessary_oredicts(self):
        with self._lock:
            unnecessary_oredicts:Dict[str, Item] = {}
            for item in self._items.values():
                if item.name.startswith('<ore:') and len(item.recipes) == 1:
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

    rg = BasicRecipeGraph(df_r, [])

    myitem = rg.get_item_and_resolve_recipes('<harvestcraft:thankfuldinneritem>')
    # myitem = get_item('<minecraft:sticky_piston>')
    print(myitem)
