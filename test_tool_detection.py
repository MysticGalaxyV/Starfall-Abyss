#!/usr/bin/env python3

import json
from data_models import DataManager, PlayerData

def test_tool_detection():
    """Test the tool detection fix"""
    # Load player data
    data_manager = DataManager()
    
    # Load player data directly from file
    try:
        with open('player_data.json', 'r') as f:
            data = json.load(f)
        
        if not data.get('players'):
            print("No players found")
            return
        
        # Get first player ID and load their data
        first_player_id = list(data['players'].keys())[0]
        player = data_manager.get_player(int(first_player_id))
    except Exception as e:
        print(f"Error loading player data: {e}")
        return
        
    print(f"Testing tool detection for player: {player.name}")
    print(f"Level: {player.class_level}")
    
    # Check equipped tools
    print("\nEquipped gathering tools:")
    for category, tool_name in player.equipped_gathering_tools.items():
        print(f"  {category}: {tool_name or 'None'}")
    
    # Check inventory for tools
    print("\nTools in inventory:")
    for inv_item in player.inventory:
        if hasattr(inv_item, 'item') and hasattr(inv_item.item, 'name'):
            item_name = inv_item.item.name
            # Check if it's a tool by looking for tool keywords
            tool_keywords = ['Pickaxe', 'Axe', 'Sickle', 'Wand', 'Spear', 'Drill', 'Saw', 'Harvester']
            if any(keyword in item_name for keyword in tool_keywords):
                print(f"  {item_name} (qty: {inv_item.quantity})")
    
    print("\nTool detection test completed.")

if __name__ == "__main__":
    test_tool_detection()