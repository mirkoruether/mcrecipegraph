# -*- coding: utf-8 -*-
"""

@author: Mirko Ruether
"""

import pandas as pd

import dash
import dash_cytoscape as cyto
import dash_html_components as html

import recipegraph

cyto.load_extra_layouts()

ROOTITEM = '<harvestcraft:thankfuldinneritem>'
# ROOTITEM = '<minecraft:sticky_piston>'

df_r = pd.read_csv('recipes.csv')
df_r = df_r.loc[
    df_r['id'].str.startswith('minecraft') |
    df_r['id'].str.startswith('harvestcraft') |
    df_r['id'].str.startswith('furnace') |
    df_r['id'].str.startswith('oredict')
].reset_index(drop=True)
rg = recipegraph.RecipeGraph(df_r)
rg.get_item(ROOTITEM)
rg.remove_unnecessary_oredicts()

ELEMENTS = []
for item in rg.items.values():
    ELEMENTS.append(dict(data=dict(id=item.name, label=item.name)))

    if item.name.startswith('<ore:'):
        for recipe in item.recipes:
            ingredient = recipe.ingredients[0][0]
            ELEMENTS.append(dict(data=dict(source=item.name, target=ingredient.name), classes='ingredient'))
    else:
        for i, recipe in enumerate(item.recipes):
            if len(item.recipes) <= 1:
                source = item.name
            else:
                source = recipe.name
                ELEMENTS.append(dict(data=dict(id=recipe.name, label=recipe.name, parent=item.name)))
                for j in range(i):
                    ELEMENTS.append(dict(data=dict(source=recipe.name, target=item.recipes[j].name), classes='recipealternative'))

            for ingredient, i_count in recipe.ingredients:
                ELEMENTS.append(dict(data=dict(source=source, target=ingredient.name), classes='ingredient'))

app = dash.Dash(__name__)

app.layout = html.Div([
    cyto.Cytoscape(
        id='cytoscape-compound',
        responsive=True,
        # layout=dict(name='breadthfirst', root=f'[id="{ROOTITEM}"]'),
        layout=dict(name='cose'),
        style={'width': '100%', 'height': '100vh'},
        stylesheet=[
            {
                'selector': 'node',
                'style': {
                    'content': 'data(label)',
                    'opacity': 0.65,
                    'z-index': 9999
                }
            },
            {
                'selector': 'edge',
                'style': {
                    'curve-style': 'bezier',
                    'opacity': 0.45,
                    'z-index': 5000
                }
            },
            {
                'selector': '.ingredient',
                'style': {
                    'source-arrow-color': 'black',
                    'source-arrow-shape': 'triangle',
                    'line-color': 'black'
                }
            },
            {
                'selector': '.recipe',
                'style': {
                    'source-arrow-color': 'grey',
                    'source-arrow-shape': 'triangle',
                    'line-color': 'grey'
                }
            },
            {
                'selector': '.recipealternative',
                'style': {
                    'line-color': 'grey'
                }
            },
        ],
        elements=ELEMENTS
    )
])

if __name__ == '__main__':
    app.run_server(debug=True, port=5000)
