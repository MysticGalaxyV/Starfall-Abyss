#!/usr/bin/env python3
"""
Test script to verify tool detection during gathering
"""

import json
from data_models import DataManager, Item, InventoryItem
from materials import GatheringView

def test_gathering_tool_detection():
    """Test if tools are properly detected during gathering"""
    
    # Load test data
    data_manager = DataManager()
    
    # Get test player
    test_user_id = 123456789
    player = data_manager.get_player(test_user_id)
    
    # Create a GatheringView instance to test tool detection
    gathering_view = GatheringView(player, data_manager)
    
    print("Testing tool detection during gathering...")
    print(f"Player level: {player.class_level}")
    
    # Test each equipped tool
    categories_to_test = ["Mining", "Foraging", "Herbs"]
    
    for category in categories_to_test:
        print(f"\nTesting {category}:")
        
        # Check equipped tool
        equipped_tool = player.equipped_gathering_tools.get(category)
        print(f"  Equipped tool: {equipped_tool}")
        
        # Test get_best_tool method
        best_tool = gathering_view.get_best_tool(category)
        if best_tool:
            tool_name, efficiency = best_tool
            print(f"  Best tool found: {tool_name} (Efficiency: {efficiency:.1f}x)")
        else:
            print(f"  No tool found for {category}")
        
        # Test get_tool_efficiency_simple method
        if equipped_tool:
            efficiency_simple = gathering_view.get_tool_efficiency_simple(equipped_tool, category)
            print(f"  Simple efficiency calculation: {efficiency_simple:.1f}x")
    
    print("\n" + "="*50)
    print("DIAGNOSIS:")
    
    # Check if tools exist in inventory
    print("\nTools in inventory:")
    tool_count = 0
    for inv_item in player.inventory:
        if hasattr(inv_item, 'item') and hasattr(inv_item.item, 'item_type'):
            if inv_item.item.item_type == 'tool':
                tool_count += 1
                print(f"  {inv_item.item.name} (Type: {inv_item.item.item_type}, Level req: {inv_item.item.level_req})")
    
    if tool_count == 0:
        print("  No tools found in inventory!")
    
    # Check equipped tools dictionary
    print("\nEquipped tools dictionary:")
    for category, tool_name in player.equipped_gathering_tools.items():
        print(f"  {category}: {tool_name}")
    
    # Test tool matching logic
    print("\nTesting tool matching for Mining:")
    equipped_mining_tool = player.equipped_gathering_tools.get("Mining")
    if equipped_mining_tool:
        print(f"  Looking for tool named: '{equipped_mining_tool}'")
        found_in_inventory = False
        for inv_item in player.inventory:
            if hasattr(inv_item, 'item') and hasattr(inv_item.item, 'name'):
                if inv_item.item.name == equipped_mining_tool:
                    found_in_inventory = True
                    print(f"  Found matching tool in inventory: {inv_item.item.name}")
                    print(f"    Item type: {getattr(inv_item.item, 'item_type', 'MISSING')}")
                    print(f"    Level req: {getattr(inv_item.item, 'level_req', 'MISSING')}")
                    break
        
        if not found_in_inventory:
            print(f"  ERROR: Equipped tool '{equipped_mining_tool}' not found in inventory!")
            print("  Available tools in inventory:")
            for inv_item in player.inventory:
                if hasattr(inv_item, 'item') and hasattr(inv_item.item, 'name'):
                    print(f"    - {inv_item.item.name}")

if __name__ == "__main__":
    test_gathering_tool_detection()