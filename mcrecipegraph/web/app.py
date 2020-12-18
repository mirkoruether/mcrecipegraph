# -*- coding: utf-8 -*-
"""

@author: Mirko Ruether
"""

import itertools

from typing import Dict, List
import pandas as pd

import yaml

import flask
import dash
import dash_cytoscape as cyto
import dash_bootstrap_components as dbc

from dash.dependencies import Input, Output, State

import mcrecipegraph.core.recipegraph as recipegraph

DEFAULT_ITEM = '<harvestcraft:persimmonyogurtitem>'
# DEFAULT_ITEM = '<minecraft:sticky_piston>'

df_r = pd.read_csv('recipes.csv')
df_r = df_r.loc[
    df_r['id'].str.startswith('minecraft') |
    df_r['id'].str.startswith('harvestcraft') |
    df_r['id'].str.startswith('furnace') |
    df_r['id'].str.startswith('oredict')
].reset_index(drop=True)

with open('config.yaml') as fh:
    appcfg = yaml.safe_load(fh)

def _get_graph_data(item:recipegraph.Item, data:Dict[str, List[Dict]]):
    data[item.name] = [dict(data=dict(
        id=item.name, label=item.name
    ), classes='item')]
    for recipe in item.recipes:
        data[item.name].append(dict(data=dict(
            id=recipe.name, label=recipe.name
        ), classes='recipe'))

        for result, result_amount in recipe.results:
            data[item.name].append(dict(data=dict(
                source=result.name, target=recipe.name, amount=result_amount
            ), classes='result'))

        for ingredient, ingredient_amount in recipe.ingredients:
            data[item.name].append(dict(data=dict(
                source=recipe.name, target=ingredient.name, amount=ingredient_amount
            ), classes='ingredient'))
            if not ingredient.name in data:
                _get_graph_data(ingredient, data)

def get_graph_data(item:recipegraph.Item) -> List[Dict]:
    data = {}
    _get_graph_data(item, data)
    return list(itertools.chain.from_iterable(data.values()))

rg = recipegraph.BasicRecipeGraph(df_r, appcfg['forceatomic'])

flask_app = flask.Flask(__name__)
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], server=flask_app)

app.layout = dbc.Container([
    dbc.Row(dbc.Col(dbc.Card([
        dbc.CardHeader('Inputs'),
        dbc.CardBody(dbc.InputGroup([
            dbc.InputGroupAddon('Item ID', addon_type='prepend'),
            dbc.Input(id='input-item', placeholder=DEFAULT_ITEM),
            dbc.InputGroupAddon(dbc.Button('Submit', id='input-submit'), addon_type='append'),
        ]))
    ]))),
    dbc.Row(dbc.Col(dbc.Card([
        dbc.CardHeader('Recipe Graph'),
        dbc.CardBody(cyto.Cytoscape(
            id='mycytoscape',
            layout=dict(name='cose', animate=False),
            style={'height': '800px'},
            stylesheet=appcfg['graphstyle']
        ))
    ]))),
])

@app.callback(
    Output('mycytoscape', 'elements'),
    Input('input-submit', 'n_clicks'),
    State('input-item', 'value')
)
def update_graph(_, itemname):
    if not itemname:
        itemname = DEFAULT_ITEM
    item = rg.get_item_and_resolve_recipes(itemname)
    return get_graph_data(item)

if __name__ == '__main__':
    app.run_server(debug=True, port=5000)
