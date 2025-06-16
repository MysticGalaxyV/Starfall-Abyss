#!/usr/bin/env python3
"""
Test script to diagnose tool detection issues without Discord UI
"""

import json
from data_models import DataManager

def test_tool_detection_logic():
    """Test the core tool detection logic"""
    
    data_manager = DataManager()
    test_user_id = 123456789
    player = data_manager.get_player(test_user_id)
    
    print("=== TOOL DETECTION DIAGNOSIS ===")
    print(f"Player level: {player.class_level}")
    print(f"Player class: {player.class_name}")
    
    # Check equipped tools
    print("\nEquipped gathering tools:")
    for category, tool_name in player.equipped_gathering_tools.items():
        print(f"  {category}: {tool_name}")
    
    # Check inventory for tools
    print("\nTools in inventory:")
    tool_found = False
    for i, inv_item in enumerate(player.inventory):
        if hasattr(inv_item, 'item') and hasattr(inv_item.item, 'name'):
            item_type = getattr(inv_item.item, 'item_type', 'unknown')
            if item_type == 'tool':
                tool_found = True
                print(f"  [{i}] {inv_item.item.name}")
                print(f"      Type: {item_type}")
                print(f"      Level req: {getattr(inv_item.item, 'level_req', 'unknown')}")
    
    if not tool_found:
        print("  No tools found in inventory!")
    
    # Test the core tool matching logic from materials.py
    print("\n=== TESTING TOOL MATCHING LOGIC ===")
    
    # Test Mining category
    category = "Mining"
    equipped_tool_name = player.equipped_gathering_tools.get(category)
    
    if equipped_tool_name:
        print(f"\nTesting {category} with equipped tool: {equipped_tool_name}")
        
        # Simulate the get_best_tool logic
        found_tool = None
        for inv_item in player.inventory:
            if hasattr(inv_item, 'item') and hasattr(inv_item.item, 'name'):
                if inv_item.item.name == equipped_tool_name:
                    found_tool = inv_item
                    break
        
        if found_tool:
            print(f"  ✓ Found equipped tool in inventory: {found_tool.item.name}")
            
            # Test efficiency calculation
            efficiency = get_tool_efficiency_simple(equipped_tool_name, category)
            print(f"  ✓ Calculated efficiency: {efficiency:.1f}x")
            
            if efficiency > 1.0:
                print(f"  ✓ Tool should be detected (efficiency > 1.0)")
            else:
                print(f"  ✗ Tool won't be detected (efficiency = 1.0)")
        else:
            print(f"  ✗ Equipped tool '{equipped_tool_name}' not found in inventory!")
    else:
        print(f"\nNo tool equipped for {category}")

def get_tool_efficiency_simple(tool_name: str, category: str) -> float:
    """Replicate the efficiency calculation logic from materials.py"""
    # Tier mapping based on common material names
    tier_efficiency = {
        "Copper": 1.2, "Iron": 1.5, "Steel": 1.8, "Mithril": 2.1,
        "Adamantite": 2.5, "Runite": 3.0, "Dragon": 3.5, "Crystal": 4.0,
        "Divine": 5.0, "Apprentice": 1.2, "Journeyman": 1.5, "Adept": 1.8,
        "Master": 2.1, "Archmagus": 2.5, "Basic": 1.1, "Reinforced": 2.2,
        "Enchanted": 2.5, "Titanium": 2.2, "Celestial": 4.0, "Ethereal": 5.0,
        "Void": 7.0
    }
    
    # Check for tier keywords in tool name
    for tier, efficiency in tier_efficiency.items():
        if tier in tool_name:
            return efficiency
    
    # Default efficiency for any tool
    return 1.2

if __name__ == "__main__":
    test_tool_detection_logic()