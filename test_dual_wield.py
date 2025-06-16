#!/usr/bin/env python3

"""
Test script for dual weapon equipping system
"""

from data_models import PlayerData, DataManager
from equipment import generate_random_item, add_item_to_inventory
from utils import can_dual_wield, GAME_CLASSES

def test_dual_wield_system():
    """Test the dual weapon equipping functionality"""
    
    # Create test player with Flash Rogue class (supports dual wielding)
    player = PlayerData(12345)
    player.class_name = "Flash Rogue"
    player.user_level = 10
    
    print(f"Testing dual wield system for {player.class_name}")
    print(f"Can dual wield: {can_dual_wield(player.class_name)}")
    print(f"Initial equipped items: {player.equipped_items}")
    
    # Generate two test weapons
    weapon1 = generate_random_item(5)
    weapon1.name = "Test Sword"
    weapon1.item_type = "weapon"
    weapon1.stats = {"power": 15}
    
    weapon2 = generate_random_item(5)
    weapon2.name = "Test Dagger"
    weapon2.item_type = "weapon"
    weapon2.stats = {"power": 12}
    
    # Add weapons to inventory
    add_item_to_inventory(player, weapon1)
    add_item_to_inventory(player, weapon2)
    
    print(f"\nAdded weapons to inventory:")
    for item in player.inventory:
        print(f"- {item.item.name} ({item.item.item_type}) - Power: {item.item.stats.get('power', 0)}")
    
    # Manually equip first weapon to main hand
    player.inventory[0].equipped = True
    player.equipped_items["weapon"] = player.inventory[0].item.item_id
    
    print(f"\nEquipped main hand weapon: {player.inventory[0].item.name}")
    print(f"Equipped items after main hand: {player.equipped_items}")
    
    # Manually equip second weapon to off hand
    player.inventory[1].equipped = True
    player.equipped_items["weapon2"] = player.inventory[1].item.item_id
    
    print(f"\nEquipped off hand weapon: {player.inventory[1].item.name}")
    print(f"Equipped items after off hand: {player.equipped_items}")
    
    # Test stats calculation with dual weapons
    stats = player.get_stats(GAME_CLASSES)
    print(f"\nFinal stats with dual weapons:")
    print(f"Power: {stats['power']} (should include both weapons with off-hand penalty)")
    print(f"Defense: {stats['defense']}")
    print(f"Speed: {stats['speed']}")
    print(f"HP: {stats['hp']}")
    
    # Test with non-dual wield class
    print(f"\n" + "="*50)
    print("Testing with Spirit Striker (non-dual wield class)")
    
    player2 = PlayerData(67890)
    player2.class_name = "Spirit Striker"
    player2.user_level = 10
    
    print(f"Can dual wield: {can_dual_wield(player2.class_name)}")
    
    # Add same weapons
    add_item_to_inventory(player2, weapon1)
    add_item_to_inventory(player2, weapon2)
    
    # Try to equip both (should only allow one)
    player2.inventory[0].equipped = True
    player2.equipped_items["weapon"] = player2.inventory[0].item.item_id
    
    print(f"Equipped main weapon: {player2.inventory[0].item.name}")
    print(f"Equipped items: {player2.equipped_items}")
    
    # Second weapon should not be equippable to weapon2 slot for non-dual wield class
    stats2 = player2.get_stats(GAME_CLASSES)
    print(f"Stats with single weapon:")
    print(f"Power: {stats2['power']} (should only include main weapon)")
    
    print("\nDual wield system test completed!")

if __name__ == "__main__":
    test_dual_wield_system()