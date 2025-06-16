"""
Unified move generation system for both battles and dungeons
"""

from battle_system import BattleMove
from typing import List

def get_player_moves(class_name: str) -> List[BattleMove]:
    """Get comprehensive move set for a player based on their class"""
    moves = []
    
    # Basic moves for everyone
    moves.append(BattleMove("Basic Attack", 1.0, 10, description="A standard attack"))
    moves.append(BattleMove("Heavy Strike", 1.5, 25, description="A powerful but costly attack"))
    
    # Class-specific special moves
    if class_name == "Spirit Striker":
        moves.extend([
            BattleMove("Cursed Combo", 2.0, 35, "weakness", "Deal damage and weaken enemy"),
            BattleMove("Soul Siphon", 1.2, 20, "energy_restore", "Deal damage and restore energy"),
            BattleMove("Phantom Rush", 1.8, 30, "strength", "Deal damage and gain increased damage"),
            BattleMove("Spirit Drain", 0.9, 15, None, "Drain enemy energy while dealing damage")
        ])
    elif class_name == "Domain Tactician":
        moves.extend([
            BattleMove("Barrier Pulse", 0.8, 30, "shield", "Deal damage and gain a shield"),
            BattleMove("Tactical Heal", 0.5, 25, "heal", "Deal damage and heal yourself"),
            BattleMove("Domain Strike", 1.6, 35, None, "Enhanced attack within your domain"),
            BattleMove("Strategic Maneuver", 1.1, 20, "strength", "Careful positioning for advantage")
        ])
    elif class_name == "Flash Rogue":
        moves.extend([
            BattleMove("Shadowstep", 1.7, 30, "strength", "Deal damage and gain increased damage"),
            BattleMove("Quick Strikes", 0.7, 15, None, "Deal multiple quick strikes"),
            BattleMove("Assassinate", 2.2, 40, None, "High damage stealth attack"),
            BattleMove("Smoke Bomb", 0.3, 20, "shield", "Create cover and gain defense")
        ])
    elif class_name == "Mystic Guardian":
        moves.extend([
            BattleMove("Sacred Shield", 0.6, 25, "shield", "Divine protection and minor damage"),
            BattleMove("Healing Light", 0.4, 30, "heal", "Restore health with holy energy"),
            BattleMove("Guardian's Wrath", 1.4, 35, None, "Righteous fury against enemies"),
            BattleMove("Blessing", 0.2, 20, "strength", "Enhance combat abilities")
        ])
    elif class_name == "Void Walker":
        moves.extend([
            BattleMove("Void Slash", 1.6, 30, None, "Cut through reality itself"),
            BattleMove("Dark Absorption", 0.8, 25, "energy_restore", "Absorb dark energy"),
            BattleMove("Reality Tear", 2.1, 45, "weakness", "Damage and disorient enemy"),
            BattleMove("Shadow Bind", 0.5, 20, "weakness", "Restrict enemy movement")
        ])
    elif class_name == "Cursed Brawler":
        moves.extend([
            BattleMove("Cursed Punch", 1.3, 20, None, "Enhanced physical strike"),
            BattleMove("Berserker Rage", 1.9, 35, "strength", "Unleash inner fury"),
            BattleMove("Life Steal", 1.1, 25, "heal", "Drain enemy life force"),
            BattleMove("Intimidate", 0.4, 15, "weakness", "Frighten and weaken enemy")
        ])
    elif class_name == "Elemental Sage":
        moves.extend([
            BattleMove("Fire Bolt", 1.4, 25, None, "Launch a fiery projectile"),
            BattleMove("Ice Shard", 1.2, 20, "weakness", "Freeze and slow enemy"),
            BattleMove("Lightning Strike", 1.7, 35, None, "Electrifying attack"),
            BattleMove("Earth Shield", 0.5, 30, "shield", "Stone barrier protection")
        ])
    elif class_name == "Necromancer":
        moves.extend([
            BattleMove("Death Touch", 1.5, 30, "weakness", "Drain life energy"),
            BattleMove("Bone Armor", 0.3, 25, "shield", "Protective skeletal barrier"),
            BattleMove("Soul Burn", 1.8, 40, None, "Ignite the enemy's soul"),
            BattleMove("Life Leech", 1.0, 20, "heal", "Steal health from enemy")
        ])
    elif class_name == "Time Weaver":
        moves.extend([
            BattleMove("Temporal Strike", 1.6, 35, None, "Attack across time"),
            BattleMove("Time Slow", 0.6, 30, "weakness", "Slow enemy perception"),
            BattleMove("Chronos Heal", 0.4, 25, "heal", "Reverse damage through time"),
            BattleMove("Haste", 0.8, 20, "strength", "Accelerate combat speed")
        ])
    elif class_name == "Blood Mage":
        moves.extend([
            BattleMove("Blood Spike", 1.4, 25, None, "Crystallize blood into weapon"),
            BattleMove("Crimson Barrier", 0.5, 30, "shield", "Blood-formed protection"),
            BattleMove("Hemorrhage", 1.2, 20, "weakness", "Cause internal bleeding"),
            BattleMove("Blood Ritual", 0.7, 35, "heal", "Sacrifice for power")
        ])
    elif class_name == "Storm Caller":
        moves.extend([
            BattleMove("Thunder Clap", 1.5, 30, None, "Deafening sonic attack"),
            BattleMove("Wind Shield", 0.4, 25, "shield", "Deflecting air barrier"),
            BattleMove("Chain Lightning", 1.8, 40, None, "Electricity jumps between foes"),
            BattleMove("Storm's Eye", 1.0, 20, "strength", "Center of the storm")
        ])
    elif class_name == "Dream Walker":
        moves.extend([
            BattleMove("Nightmare", 1.3, 25, "weakness", "Inflict terrifying visions"),
            BattleMove("Dream Shield", 0.6, 30, "shield", "Illusory protection"),
            BattleMove("Lucid Strike", 1.7, 35, None, "Reality-bending attack"),
            BattleMove("Sleep", 0.2, 20, "weakness", "Induce drowsiness")
        ])
    elif class_name == "Crystal Monk":
        moves.extend([
            BattleMove("Crystal Fist", 1.4, 25, None, "Hardened crystalline strike"),
            BattleMove("Meditation", 0.1, 30, "heal", "Inner peace restoration"),
            BattleMove("Diamond Skin", 0.3, 35, "shield", "Ultimate crystal defense"),
            BattleMove("Resonance", 1.6, 40, None, "Harmonic frequency attack")
        ])

    # Add generic moves for any class not specifically handled
    if len(moves) == 2:  # Only basic moves were added
        moves.extend([
            BattleMove("Power Strike", 1.3, 20, None, "A stronger version of basic attack"),
            BattleMove("Defensive Stance", 0.5, 25, "shield", "Focus on defense"),
            BattleMove("Recovery", 0.2, 30, "heal", "Rest and recover health"),
            BattleMove("Focused Attack", 1.6, 35, None, "Concentrate for maximum damage")
        ])
    
    return moves

def get_enemy_moves(enemy_name: str) -> List[BattleMove]:
    """Get comprehensive move set for enemies"""
    moves = []
    
    # Default moves that all enemies have
    moves.extend([
        BattleMove("Strike", 0.8, 10, description="A basic attack"),
        BattleMove("Power Attack", 1.3, 20, description="A stronger attack")
    ])
    
    # Add enemy-specific moves based on name
    enemy_lower = enemy_name.lower()
    
    if "goblin" in enemy_lower:
        moves.extend([
            BattleMove("Sneak Attack", 1.1, 15, effect="weakness", description="Causes bleeding damage"),
            BattleMove("Dirty Fighting", 0.9, 12, description="Underhanded tactics")
        ])
    elif "troll" in enemy_lower:
        moves.extend([
            BattleMove("Smash", 1.8, 30, description="A devastating attack"),
            BattleMove("Regenerate", 0.0, 25, effect="heal", description="Troll regeneration")
        ])
    elif "dragon" in enemy_lower:
        moves.extend([
            BattleMove("Fire Breath", 1.5, 25, effect="weakness", description="Deals fire damage"),
            BattleMove("Tail Sweep", 1.2, 20, description="Hits with massive tail"),
            BattleMove("Wing Buffet", 0.9, 15, description="Powerful wing attack")
        ])
    elif "slime" in enemy_lower:
        moves.extend([
            BattleMove("Acid Splash", 0.9, 15, effect="weakness", description="Deals acid damage"),
            BattleMove("Engulf", 1.1, 20, description="Tries to engulf target")
        ])
    elif "skeleton" in enemy_lower:
        moves.extend([
            BattleMove("Bone Throw", 0.7, 10, description="Throws a bone projectile"),
            BattleMove("Rattle", 0.5, 15, effect="weakness", description="Intimidating bone rattle")
        ])
    elif "orc" in enemy_lower:
        moves.extend([
            BattleMove("Savage Blow", 1.4, 25, description="Brutal orcish attack"),
            BattleMove("War Cry", 0.3, 20, effect="strength", description="Boosts combat prowess")
        ])
    elif "elemental" in enemy_lower:
        if "fire" in enemy_lower:
            moves.extend([
                BattleMove("Flame Burst", 1.3, 20, description="Explosive fire attack"),
                BattleMove("Ignite", 0.8, 15, effect="weakness", description="Sets target ablaze")
            ])
        elif "ice" in enemy_lower:
            moves.extend([
                BattleMove("Frost Bite", 1.1, 18, effect="weakness", description="Freezing attack"),
                BattleMove("Ice Shard", 1.2, 22, description="Sharp ice projectile")
            ])
        elif "earth" in enemy_lower:
            moves.extend([
                BattleMove("Rock Throw", 1.0, 15, description="Hurls stone projectiles"),
                BattleMove("Earthquake", 1.4, 30, description="Ground-shaking attack")
            ])
        else:
            moves.extend([
                BattleMove("Elemental Burst", 1.2, 20, description="Pure elemental energy"),
                BattleMove("Energy Shield", 0.4, 25, effect="shield", description="Elemental protection")
            ])
    elif "golem" in enemy_lower:
        moves.extend([
            BattleMove("Boulder Fist", 1.6, 30, description="Massive stone punch"),
            BattleMove("Stone Skin", 0.2, 35, effect="shield", description="Hardens exterior")
        ])
    elif "wraith" in enemy_lower or "ghost" in enemy_lower:
        moves.extend([
            BattleMove("Life Drain", 1.0, 20, effect="heal", description="Drains life force"),
            BattleMove("Terrify", 0.6, 18, effect="weakness", description="Induces fear")
        ])
    elif "demon" in enemy_lower:
        moves.extend([
            BattleMove("Hellfire", 1.5, 28, description="Demonic flame attack"),
            BattleMove("Dark Pact", 0.8, 25, effect="strength", description="Gains dark power")
        ])
    elif "boss" in enemy_lower or "ancient" in enemy_lower or "lord" in enemy_lower:
        moves.extend([
            BattleMove("Devastating Strike", 2.0, 35, description="Ultimate boss attack"),
            BattleMove("Enrage", 0.5, 30, effect="strength", description="Enters berserk mode"),
            BattleMove("Area Sweep", 1.3, 25, description="Hits multiple targets"),
            BattleMove("Boss Heal", 0.0, 40, effect="heal", description="Recovers health")
        ])
    
    return moves