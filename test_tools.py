#!/usr/bin/env python3
"""
Test script to verify tool equipping functionality
"""

import json
from data_models import DataManager, Item, InventoryItem

def test_tool_equipping():
    """Test tool equipping and detection functionality"""
    
    # Load or create test data
    data_manager = DataManager()
    
    # Create a test user ID
    test_user_id = 123456789
    
    # Get or create player
    player = data_manager.get_player(test_user_id)
    
    # Ensure player has a class
    if not player.class_name:
        player.class_name = "Spirit Striker"
        player.class_level = 10
    
    # Add some test tools to inventory
    test_tools = [
        Item("tool_1", "Iron Pickaxe", "A sturdy iron pickaxe for mining", "tool", "common", 
             {"power": 5}, 5, 100),
        Item("tool_2", "Steel Axe", "A sharp steel axe for foraging", "tool", "uncommon", 
             {"power": 8}, 10, 200),
        Item("tool_3", "Copper Sickle", "A basic copper sickle for herbs", "tool", "common", 
             {"power": 3}, 1, 50),
    ]
    
    # Clear existing tools and add test tools
    player.inventory = [item for item in player.inventory if not (hasattr(item, 'item') and hasattr(item.item, 'item_type') and item.item.item_type == 'tool')]
    
    for tool in test_tools:
        player.inventory.append(InventoryItem(tool, quantity=1, equipped=False))
    
    # Test equipping tools
    print("Testing tool equipping...")
    
    # Test equipping Iron Pickaxe for Mining
    player.equipped_gathering_tools["Mining"] = "Iron Pickaxe"
    print(f"Equipped Mining tool: {player.equipped_gathering_tools['Mining']}")
    
    # Test equipping Steel Axe for Foraging
    player.equipped_gathering_tools["Foraging"] = "Steel Axe"
    print(f"Equipped Foraging tool: {player.equipped_gathering_tools['Foraging']}")
    
    # Test equipping Copper Sickle for Herbs
    player.equipped_gathering_tools["Herbs"] = "Copper Sickle"
    print(f"Equipped Herbs tool: {player.equipped_gathering_tools['Herbs']}")
    
    # Save data
    data_manager.save_data()
    
    print("\nEquipped tools:")
    for category, tool_name in player.equipped_gathering_tools.items():
        print(f"  {category}: {tool_name or 'None'}")
    
    print("\nInventory tools:")
    for inv_item in player.inventory:
        if hasattr(inv_item, 'item') and hasattr(inv_item.item, 'item_type') and inv_item.item.item_type == 'tool':
            print(f"  {inv_item.item.name} (Level {inv_item.item.level_req})")
    
    print("\nTest completed successfully!")

if __name__ == "__main__":
    test_tool_equipping()