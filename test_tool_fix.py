#!/usr/bin/env python3
"""
Test script to add some basic tools to a player's inventory for testing tool equipping
"""

import json
from data_models import DataManager, Item, InventoryItem

def add_test_tools():
    """Add some basic tools to the first player for testing"""
    data_manager = DataManager()
    
    # Get the first player (assuming there's at least one)
    if not data_manager.players:
        print("No players found!")
        return
    
    player_id = list(data_manager.players.keys())[0]
    player = data_manager.players[player_id]
    
    # Create some basic tools
    tools = [
        {
            "name": "Copper Pickaxe",
            "description": "A basic mining tool made of copper.",
            "item_type": "tool",
            "category": "Mining",
            "efficiency": 1.2,
            "level_req": 1
        },
        {
            "name": "Iron Axe", 
            "description": "An improved foraging tool made of iron.",
            "item_type": "tool", 
            "category": "Foraging",
            "efficiency": 1.5,
            "level_req": 10
        },
        {
            "name": "Steel Sickle",
            "description": "A sharp herb gathering tool made of steel.",
            "item_type": "tool",
            "category": "Herbs", 
            "efficiency": 1.8,
            "level_req": 20
        }
    ]
    
    for tool_data in tools:
        # Create the tool item
        tool = Item(
            item_id=f"tool_{tool_data['name'].lower().replace(' ', '_')}",
            name=tool_data["name"],
            description=tool_data["description"],
            item_type=tool_data["item_type"],
            rarity="common",
            stats={},
            level_req=tool_data["level_req"],
            value=100
        )
        
        # Add to player inventory
        inv_item = InventoryItem(tool, quantity=1, equipped=False)
        player.inventory.append(inv_item)
        
        print(f"Added {tool_data['name']} to player inventory")
    
    # Save the data
    data_manager.save_data()
    print(f"Updated player {player_id} with test tools")

if __name__ == "__main__":
    add_test_tools()