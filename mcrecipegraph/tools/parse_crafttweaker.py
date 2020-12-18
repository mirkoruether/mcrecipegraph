# -*- coding: utf-8 -*-
"""
To obtain crafttweaker.log install CraftTweaker an run the following commands ingame
https://www.curseforge.com/minecraft/mc-mods/crafttweaker

/ct blocks
/ct entities
/ct foods
/ct keyNames
/ct liquids
/ct mods
/ct names display unloc maxstack maxuse maxdamage rarity repaircost damageable repairable creativetabs enchantability burntim
/ct oredict
/ct recipes
/ct recipes furnace

@author: Mirko Ruether
"""

import re
import logging
import pandas as pd

def main():
    with open('crafttweaker.log') as fh:
        lines = pd.Series(fh.readlines())

    seperators = lines.loc[lines.str.endswith(':\n')]

    blocks = []

    for i, (fromline, linecontent) in enumerate(list(seperators.iteritems())):
        toline = seperators.index[i + 1] if (i+1) < len(seperators) else len(lines)
        blocks.append((linecontent, lines.loc[fromline+1:toline-1].to_list()))

    logging.info('%d Blocks found', len(blocks))

    dfl_mods = []
    dfl_receipes = []
    dfl_entitys = []

    for blockheader, blocklines in blocks:
        if blockheader.startswith('Mods list'):
            # Mods list:
            # minecraft - Minecraft - 1.12.2
            # mcp - Minecraft Coder Pack - 9.42
            # FML - Forge Mod Loader - 8.0.99.99
            for line in blocklines:
                lsplit = line.split('-', 2)
                dfl_mods.append(dict(
                    id=lsplit[0].strip(),
                    name=lsplit[1].strip(),
                    version=lsplit[2].strip()
                ))
        elif blockheader.startswith('Recipes'):
            # Recipes:
            # recipes.addShapeless("forestry:block_to_bronze", <forestry:ingot_bronze> * 9, [<ore:blockBronze>]);
            # recipes.addShapeless("harvestcraft:sesameoilitem", <harvestcraft:sesameoilitem>, [<ore:toolJuicer>, <ore:cropSesame>]);
            # recipes.addShaped("forestry:letter_recycling", <minecraft:paper>, [[<ore:emptiedLetter>, <ore:emptiedLetter>, <ore:emptiedLetter>]]);
            # recipes.addShaped("minecraft:chest", <minecraft:chest>, [[<ore:plankWood>, <ore:plankWood>, <ore:plankWood>], [<ore:plankWood>, null, <ore:plankWood>], [<ore:plankWood>, <ore:plankWood>, <ore:plankWood>]]);
            # recipes.addShaped("minecraft:crafting_table", <minecraft:crafting_table>, [[<ore:plankWood>, <ore:plankWood>], [<ore:plankWood>, <ore:plankWood>]]);
            for line in blocklines:
                if line.startswith('recipes.addShapeless'):
                    crafttype = 'shapeless'
                elif line.startswith('recipes.addShaped'):
                    crafttype = 'shaped'
                else:
                    continue
                inner = re.search(r'\((.*)\);', line).group(1)
                parts = inner.split(',', 2)
                resitem = parts[1].strip()
                if '*' in resitem:
                    resitemsplit = resitem.split('*')
                    resitem = resitemsplit[0].strip()
                    amount = int(resitemsplit[1].strip())
                else:
                    amount = 1
                dfl_receipes.append(dict(
                    id=parts[0].strip()[1:-1],
                    crafttype=crafttype,
                    resitem=resitem,
                    amount=amount,
                    craftraw=parts[2].strip()
                ))
        elif blockheader.startswith('Furnace Recipes'):
            # Furnace Recipes:
            # furnace.addRecipe(<minecraft:netherbrick>, <minecraft:netherrack:*>, 0.100000)
            # furnace.addRecipe(<minecraft:coal:1>, <extratrees:logs.5:*>, 0.100000)
            # furnace.addRecipe(<minecraft:gold_nugget>, <minecraft:golden_shovel:*>, 0.100000)
            for line in blocklines:
                inner = re.search(r'\((.*)\)', line).group(1)
                parts = inner.split(',', 2)
                dfl_receipes.append(dict(
                    id='furnace:' + re.search(r'<(.*)>', parts[1]).group(1),
                    crafttype='furnace',
                    resitem=parts[0].strip(),
                    amount=1,
                    craftraw=parts[1].strip()
                ))
        elif blockheader.startswith('Ore entries'):
            # Ore entries for <ore:listAllsoda> :
            # -<harvestcraft:cherrysodaitem>
            # -<harvestcraft:colasodaitem>
            # -<harvestcraft:gingersodaitem>
            for line in blocklines:
                ore=re.search(r'Ore entries for (.*):', blockheader).group(1).strip()
                item=line[1:].strip()
                dfl_receipes.append(dict(
                    id='oredict:' + re.search(r'<(.*)>', ore).group(1) + ':' + re.search(r'<(.*)>', item).group(1),
                    crafttype='oredict',
                    resitem=ore,
                    amount=1,
                    craftraw=item
                ))
        elif blockheader.startswith('Blocks'):
            pass
        elif blockheader.startswith('Entities'):
            pass
        elif blockheader.startswith('Foods'):
            pass
        elif blockheader.startswith('Liquids'):
            pass
        elif blockheader.startswith('List of all registered Items'):
            pass
        else:
            logging.warning('Unknown blockheader %s', blockheader)

    df_receipes = pd.DataFrame(dfl_receipes).drop_duplicates('id')
    df_receipes.to_csv('recipes.csv', index=False)

    df_mods = pd.DataFrame(dfl_mods)
    df_mods.to_csv('mods.csv', index=False)
