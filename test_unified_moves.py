#!/usr/bin/env python3
"""
Test unified move system integration in battles and dungeons
"""

from unified_moves import get_player_moves, get_enemy_moves
from battle_system import BattleMove

def test_unified_move_system():
    """Test that all classes and enemies get comprehensive move sets"""
    
    print("Testing unified move system...\n")
    
    # Test all player classes get proper move sets
    test_classes = [
        "Spirit Striker", "Domain Tactician", "Flash Rogue", "Mystic Guardian",
        "Void Walker", "Cursed Brawler", "Elemental Sage", "Necromancer",
        "Time Weaver", "Blood Mage", "Storm Caller", "Dream Walker", "Crystal Monk",
        "Warrior", "Unknown Class"  # Test fallback
    ]
    
    print("=== TESTING PLAYER MOVE GENERATION ===")
    for class_name in test_classes:
        moves = get_player_moves(class_name)
        
        print(f"{class_name}: {len(moves)} moves")
        for move in moves:
            print(f"  - {move.name} (DMG: {move.damage_multiplier}x, Energy: {move.energy_cost}, Effect: {move.effect or 'None'})")
        
        # Verify basic requirements
        assert len(moves) >= 4, f"{class_name} should have at least 4 moves"
        assert any(move.name == "Basic Attack" for move in moves), f"{class_name} missing Basic Attack"
        assert any(move.name == "Heavy Strike" for move in moves), f"{class_name} missing Heavy Strike"
        
        print(f"  ✅ {class_name} has proper move set\n")
    
    # Test enemy move generation
    test_enemies = [
        "Goblin Scout", "Mountain Troll", "Ancient Dragon", "Acid Slime",
        "Skeleton Warrior", "Orc Berserker", "Fire Elemental", "Ice Elemental", 
        "Earth Elemental", "Stone Golem", "Shadow Wraith", "Lesser Demon",
        "Boss Ancient", "Crystal Colossus", "Random Enemy"  # Test fallback
    ]
    
    print("=== TESTING ENEMY MOVE GENERATION ===")
    for enemy_name in test_enemies:
        moves = get_enemy_moves(enemy_name)
        
        print(f"{enemy_name}: {len(moves)} moves")
        for move in moves:
            print(f"  - {move.name} (DMG: {move.damage_multiplier}x, Energy: {move.energy_cost}, Effect: {move.effect or 'None'})")
        
        # Verify basic requirements
        assert len(moves) >= 2, f"{enemy_name} should have at least 2 moves"
        assert any(move.name == "Strike" for move in moves), f"{enemy_name} missing Strike"
        assert any(move.name == "Power Attack" for move in moves), f"{enemy_name} missing Power Attack"
        
        print(f"  ✅ {enemy_name} has proper move set\n")
    
    print("=== TESTING MOVE VARIETY ===")
    
    # Test Spirit Striker moves (should have class-specific moves)
    spirit_moves = get_player_moves("Spirit Striker")
    spirit_move_names = [move.name for move in spirit_moves]
    
    assert "Cursed Combo" in spirit_move_names, "Spirit Striker missing Cursed Combo"
    assert "Soul Siphon" in spirit_move_names, "Spirit Striker missing Soul Siphon"
    assert "Phantom Rush" in spirit_move_names, "Spirit Striker missing Phantom Rush"
    assert "Spirit Drain" in spirit_move_names, "Spirit Striker missing Spirit Drain"
    
    print("✅ Spirit Striker has all class-specific moves")
    
    # Test Dragon moves (should have dragon-specific moves)
    dragon_moves = get_enemy_moves("Ancient Dragon")
    dragon_move_names = [move.name for move in dragon_moves]
    
    assert "Fire Breath" in dragon_move_names, "Dragon missing Fire Breath"
    assert "Tail Sweep" in dragon_move_names, "Dragon missing Tail Sweep"
    assert "Wing Buffet" in dragon_move_names, "Dragon missing Wing Buffet"
    
    print("✅ Dragon has all dragon-specific moves")
    
    # Test effect variety
    all_player_moves = []
    for class_name in test_classes[:5]:  # Test first 5 classes
        all_player_moves.extend(get_player_moves(class_name))
    
    effects_found = set()
    for move in all_player_moves:
        if move.effect:
            effects_found.add(move.effect)
    
    expected_effects = {"weakness", "heal", "shield", "strength", "energy_restore"}
    assert effects_found.intersection(expected_effects), f"Missing expected effects. Found: {effects_found}"
    
    print(f"✅ Found diverse move effects: {effects_found}")
    
    print("\n🎉 All unified move system tests passed!")
    print("Both battles and dungeons now use the same comprehensive move sets!")

def test_move_balance():
    """Test that moves are properly balanced"""
    
    print("\n=== TESTING MOVE BALANCE ===")
    
    # Test that high damage moves cost more energy
    mage_moves = get_player_moves("Elemental Sage")
    
    for move in mage_moves:
        if move.damage_multiplier > 1.5:
            assert move.energy_cost >= 25, f"{move.name} high damage but low energy cost"
        if move.damage_multiplier < 0.8:
            assert move.energy_cost <= 30, f"{move.name} low damage but high energy cost"
    
    print("✅ Move damage/energy balance is proper")
    
    # Test that healing moves have appropriate costs
    healing_moves = [move for move in mage_moves if move.effect == "heal"]
    for move in healing_moves:
        assert move.energy_cost >= 20, f"Healing move {move.name} too cheap"
    
    print("✅ Healing moves properly balanced")
    
    # Test boss moves have more variety and special abilities
    boss_moves = get_enemy_moves("Boss Ancient")
    regular_moves = get_enemy_moves("Goblin Scout")
    
    boss_max_damage = max(move.damage_multiplier for move in boss_moves)
    regular_max_damage = max(move.damage_multiplier for move in regular_moves)
    
    assert boss_max_damage >= regular_max_damage, "Boss should have at least as strong max damage moves"
    assert len(boss_moves) >= len(regular_moves), "Boss should have at least as many moves"
    
    print(f"✅ Boss moves properly designed (Max DMG: {boss_max_damage:.2f} vs {regular_max_damage:.2f}, Moves: {len(boss_moves)} vs {len(regular_moves)})")

if __name__ == "__main__":
    test_unified_move_system()
    test_move_balance()
    print("\n🌟 Unified move system is fully functional and balanced!")