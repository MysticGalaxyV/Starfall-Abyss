import discord
from discord.ui import Button, View
import random
import asyncio
import datetime
from typing import Dict, List, Optional, Tuple

from data_models import PlayerData, DataManager
from user_restrictions import RestrictedView


class BattleMove:

    def __init__(self,
                 name: str,
                 damage_multiplier: float,
                 energy_cost: int,
                 effect: Optional[str] = None,
                 description: Optional[str] = None):
        self.name = name
        self.damage_multiplier = damage_multiplier
        self.energy_cost = energy_cost
        self.effect = effect or ""
        self.description = description or f"Deal {int(damage_multiplier * 100)}% damage"


class BattleEntity:

    def __init__(self,
                 name: str,
                 stats: Dict[str, int],
                 moves: Optional[List[BattleMove]] = None,
                 is_player: bool = False,
                 player_data: Optional[PlayerData] = None):
        self.name = name
        self.stats = stats.copy()
        self.current_hp = stats["hp"]

        # Use the player's dynamic max energy calculation if player is present
        if player_data and is_player and hasattr(player_data,
                                                 "get_max_battle_energy"):
            self.max_energy = player_data.get_max_battle_energy()
            self.current_energy = min(player_data.battle_energy,
                                      self.max_energy)
        else:
            self.max_energy = stats.get("energy", 100)
            self.current_energy = self.max_energy

        self.moves = moves or []
        self.is_player = is_player
        self.player_data = player_data
        self.level: Optional[int] = None  # Will be set for display purposes
        self.status_effects = {
        }  # Effect name -> (turns remaining, effect strength)

        # Process active effects from special items
        if is_player and player_data and hasattr(player_data,
                                                 "active_effects"):
            # Apply any HP boosts from active effects
            for effect_name, effect_data in player_data.active_effects.items():
                if effect_data.get("effect") == "hp_boost":
                    boost_amount = effect_data.get("boost_amount", 0)
                    self.stats["hp"] += boost_amount
                    self.current_hp += boost_amount
                elif effect_data.get("effect") == "all_stats_boost":
                    boost_amount = effect_data.get("boost_amount", 0)
                    for stat in ["power", "defense", "speed", "hp"]:
                        if stat in self.stats:
                            self.stats[stat] += boost_amount
                            if stat == "hp":
                                self.current_hp += boost_amount

        # Activate special abilities for this battle
        if is_player and player_data and hasattr(player_data,
                                                 "special_abilities"):
            for ability_name, ability_data in player_data.special_abilities.items(
            ):
                # Check if ability has been used and is currently active
                if ability_data.get("last_used"):
                    try:
                        last_used = datetime.datetime.fromisoformat(
                            ability_data["last_used"])
                        now = datetime.datetime.now()
                        hours_passed = (now - last_used).total_seconds() / 3600

                        # If ability is not on cooldown, mark it as active for this battle
                        if hours_passed >= ability_data.get("cooldown", 0):
                            ability_data["active_in_battle"] = True

                            # Apply permanent stat boosts from special abilities
                            if ability_data.get(
                                    "effect"
                            ) == "special_ability" and ability_name == "Infinity":
                                self.stats[
                                    "defense"] += 15  # Bonus defense from Infinity
                    except (ValueError, TypeError):
                        pass

    def is_alive(self) -> bool:
        return self.current_hp > 0

    def get_skill_level(self, skill_name: str) -> int:
        """Get the level of a specific skill from player's skill tree"""
        if not self.is_player or not self.player_data:
            return 0
        
        # Search through all skill trees for the skill
        for tree_name, tree_skills in self.player_data.skill_tree.items():
            if skill_name in tree_skills:
                return tree_skills[skill_name]
        return 0

    def calculate_damage(self, move: BattleMove,
                         target: 'BattleEntity') -> int:
        """Calculate damage for a move against a target"""
        # Base damage is attacker's power * move's damage multiplier
        base_damage = int(self.stats["power"] * move.damage_multiplier)

        # Apply skill tree effects for players
        if self.is_player and self.player_data:
            # Critical Eye skill - increased critical chance
            crit_chance = 0.1  # Base 10% crit chance
            critical_eye_level = self.get_skill_level("Critical Eye")
            if critical_eye_level > 0:
                crit_chance += critical_eye_level * 0.05  # +5% per level
            
            # Check for critical hit
            if random.random() < crit_chance:
                base_damage = int(base_damage * 1.5)  # 1.5x damage on crit
                
            # Exploit Weakness skill - increased critical damage
            exploit_weakness_level = self.get_skill_level("Exploit Weakness")
            if exploit_weakness_level > 0 and random.random() < crit_chance:
                crit_multiplier = 1.5 + (exploit_weakness_level * 0.1)  # +10% crit damage per level
                base_damage = int(self.stats["power"] * move.damage_multiplier * crit_multiplier)

        # Apply Brute Force skill - chance to ignore defense
        ignore_defense = False
        if self.is_player and self.player_data:
            brute_force_level = self.get_skill_level("Brute Force")
            if brute_force_level > 0:
                ignore_chance = brute_force_level * 0.1  # 10% per level
                if random.random() < ignore_chance:
                    ignore_defense = True

        # Defense reduces damage by a percentage (50 defense = 25% reduction)
        if ignore_defense:
            reduced_damage = base_damage  # Skip defense calculation
        else:
            defense_reduction = target.stats["defense"] / 200
            reduced_damage = base_damage * (1 - defense_reduction)

        # Apply random variance (±10%)
        variance = random.uniform(0.9, 1.1)
        final_damage = max(1, int(reduced_damage * variance))

        # Apply status effects
        if "weakness" in target.status_effects:
            _, strength = target.status_effects["weakness"]
            final_damage = int(final_damage * (1 + strength))

        if "strength" in self.status_effects:
            _, strength = self.status_effects["strength"]
            final_damage = int(final_damage * (1 + strength))

        if "shield" in target.status_effects:
            _, strength = target.status_effects["shield"]
            final_damage = int(final_damage * (1 - strength))

        return final_damage

    def apply_move(self, move: BattleMove,
                   target: 'BattleEntity') -> Tuple[int, str]:
        """Apply a move to a target and return damage dealt and effect message"""
        # Check energy cost
        if self.current_energy < move.energy_cost:
            # Player is out of energy but can regain energy
            if self.is_player:
                # Restore some energy so they can continue
                energy_gained = 50
                self.current_energy += energy_gained

                # Set a special status effect to indicate they lose 2 turns
                self.status_effects["energy_recovery"] = (
                    2, 0)  # 2 turns of recovery

                return 0, f"🔄 You're out of energy! You regained {energy_gained} energy but will lose your next 2 turns."
            else:
                return 0, "❌ Not enough energy!"

        # Apply Spell Mastery skill - reduces energy cost
        actual_energy_cost = move.energy_cost
        if self.is_player and self.player_data:
            spell_mastery_level = self.get_skill_level("Spell Mastery")
            if spell_mastery_level > 0:
                energy_reduction = spell_mastery_level * 0.1  # 10% reduction per level
                actual_energy_cost = max(1, int(move.energy_cost * (1 - energy_reduction)))
        
        self.current_energy -= actual_energy_cost

        # Check for evasion skills on target before calculating damage
        if target.is_player and target.player_data:
            # Evasive Maneuvers skill - increased dodge chance
            evasive_level = target.get_skill_level("Evasive Maneuvers")
            shadow_step_level = target.get_skill_level("Shadow Step")
            
            dodge_chance = 0
            if evasive_level > 0:
                dodge_chance += evasive_level * 0.05  # 5% per level
            if shadow_step_level > 0:
                dodge_chance += shadow_step_level * 0.08  # 8% per level (better skill)
            
            if dodge_chance > 0 and random.random() < dodge_chance:
                return 0, f"💨 {target.name} dodged the attack!"

        # Calculate and apply damage
        damage = self.calculate_damage(move, target)
        effect_msg = ""

        # Quick Draw skill - chance for extra attack
        if self.is_player and self.player_data:
            quick_draw_level = self.get_skill_level("Quick Draw")
            if quick_draw_level > 0:
                extra_attack_chance = quick_draw_level * 0.1  # 10% per level
                if random.random() < extra_attack_chance:
                    extra_damage = self.calculate_damage(move, target)
                    damage += extra_damage
                    effect_msg += f"\n⚡ Quick Draw activated! Extra attack for {extra_damage} bonus damage!"

        # Check for active effects (special items) on attacker
        if self.is_player and self.player_data and hasattr(
                self.player_data, "active_effects"):
            for effect_name, effect_data in self.player_data.active_effects.items(
            ):
                # Double attack chance
                if effect_data.get("effect") == "double_attack":
                    chance = effect_data.get("chance", 0)
                    if random.random() * 100 < chance:
                        extra_damage = self.calculate_damage(move, target)
                        damage += extra_damage
                        effect_msg += f"\n⚡ {effect_name} activated! Double attack for {extra_damage} bonus damage!"

        # Check for special abilities on attacker
        if self.is_player and self.player_data and hasattr(
                self.player_data, "special_abilities"):
            for ability_name, ability_data in self.player_data.special_abilities.items(
            ):
                # Only check abilities marked as active in battle
                if ability_data.get("active_in_battle", False):
                    ability_effect = ability_data.get("effect")

                    # Critical hit ability (Black Flash)
                    if ability_effect == "critical" and random.random(
                    ) < 0.25:  # 25% chance
                        crit_bonus = int(damage * 1.5)
                        damage += crit_bonus
                        effect_msg += f"\n⚡ {ability_name} activated! Critical hit for {crit_bonus} bonus damage!"

                    # Domain Expansion damage boost
                    elif ability_effect == "special_ability" and ability_name == "Domain Expansion":
                        domain_bonus = int(damage * 0.4)
                        damage += domain_bonus
                        effect_msg += f"\n🌌 {ability_name} is active! {domain_bonus} bonus damage!"

                    # Ten Shadows summon
                    elif ability_effect == "summon" and ability_name == "Ten Shadows Technique":
                        summon_damage = int(self.stats["power"] * 0.3)
                        damage += summon_damage
                        effect_msg += f"\n🐺 Shadow Beast attacks for {summon_damage} bonus damage!"

        # Apply dodge chance from effects
        dodge_chance = 0
        active_dodge_effect = None
        if target.is_player and target.player_data and hasattr(
                target.player_data, "active_effects"):
            for effect_name, effect_data in target.player_data.active_effects.items(
            ):
                if effect_data.get("effect") == "dodge_boost":
                    dodge_chance = effect_data.get("boost_amount", 0)
                    active_dodge_effect = effect_name
                    break

        # Check for dodge
        if dodge_chance > 0 and random.random() * 100 < dodge_chance:
            effect_msg += f"\n👁️ {target.name} dodged the attack with {active_dodge_effect}!"
            damage = 0
        # Check for Infinity special ability on target (damage reduction)
        elif target.is_player and target.player_data and hasattr(
                target.player_data, "special_abilities"):
            for ability_name, ability_data in target.player_data.special_abilities.items(
            ):
                if ability_data.get(
                        "active_in_battle", False
                ) and ability_name == "Infinity" and ability_data.get(
                        "effect") == "special_ability":
                    # Infinity reduces damage by 30%
                    reduced = int(damage * 0.3)
                    damage -= reduced
                    effect_msg += f"\n♾️ {target.name}'s {ability_name} stopped {reduced} damage!"

        # Apply damage to target
        target.current_hp = max(0, target.current_hp - damage)

        # Apply move effects
        if move.effect:
            if move.effect == "heal":
                heal_amount = int(self.stats["hp"] * 0.2)

                # Apply skill-based healing bonuses
                if self.is_player and self.player_data:
                    # Healing Touch skill - increases healing effectiveness
                    healing_touch_level = self.get_skill_level("Healing Touch")
                    if healing_touch_level > 0:
                        healing_bonus = 1 + (healing_touch_level * 0.05)  # 5% per level
                        heal_amount = int(heal_amount * healing_bonus)
                        effect_msg += f"\n💚 Healing Touch enhanced the healing!"

                # Check for healing boost from Reverse Cursed Technique
                if self.is_player and self.player_data and hasattr(
                        self.player_data, "special_abilities"):
                    for ability_name, ability_data in self.player_data.special_abilities.items(
                    ):
                        if ability_data.get(
                                "active_in_battle", False
                        ) and ability_name == "Reverse Cursed Technique" and ability_data.get(
                                "effect") == "healing":
                            heal_amount = int(heal_amount * 1.5)
                            effect_msg += f"\n💚 {ability_name} boosted healing effect!"

                self.current_hp = min(self.stats["hp"],
                                      self.current_hp + heal_amount)
                effect_msg += f"\n💚 {self.name} healed for {heal_amount} HP!"
            elif move.effect == "energy_restore":
                energy_amount = int(30)
                self.current_energy = min(self.stats.get("energy", 100),
                                          self.current_energy + energy_amount)
                effect_msg += f"\n⚡ {self.name} restored {energy_amount} energy!"
            elif move.effect == "weakness":
                # Check for Counterspell skill - chance to nullify negative effects
                resisted = False
                if target.is_player and target.player_data:
                    counterspell_level = target.get_skill_level("Counterspell")
                    unbreakable_level = target.get_skill_level("Unbreakable")
                    
                    resistance_chance = 0
                    if counterspell_level > 0:
                        resistance_chance += counterspell_level * 0.15  # 15% per level
                    if unbreakable_level > 0:
                        resistance_chance += unbreakable_level * 0.1   # 10% per level
                    
                    if resistance_chance > 0 and random.random() < resistance_chance:
                        resisted = True
                        effect_msg += f"\n🛡️ {target.name} resisted the weakness effect!"
                
                if not resisted:
                    target.status_effects["weakness"] = (2, 0.25)  # 2 turns, 25% more damage
                    effect_msg += f"\n🟣 {target.name} is weakened for 2 turns!"
                    
            elif move.effect == "strength":
                self.status_effects["strength"] = (
                    2, 0.25)  # 2 turns, 25% more damage
                effect_msg += f"\n💪 {self.name} is strengthened for 2 turns!"
            elif move.effect == "shield":
                self.status_effects["shield"] = (2, 0.3
                                                 )  # 2 turns, 30% less damage
                effect_msg += f"\n🛡️ {self.name} is shielded for 2 turns!"

        # Check for summoned ally from consumables
        if self.is_player and self.player_data and hasattr(
                self.player_data, "active_effects"):
            for effect_name, effect_data in self.player_data.active_effects.items(
            ):
                if effect_data.get("effect") == "summon_ally":
                    ally_power = effect_data.get("ally_power", 0)
                    ally_damage = int(self.stats["power"] * ally_power)
                    target.current_hp = max(0, target.current_hp - ally_damage)
                    effect_msg += f"\n👥 Summoned ally attacks for {ally_damage} additional damage!"

        return damage, effect_msg

    def update_status_effects(self) -> str:
        """Update status effects at the end of turn. Return status message."""
        status_msg = ""
        expired_effects = []

        for effect, (turns, strength) in self.status_effects.items():
            if turns <= 1:
                expired_effects.append(effect)
                status_msg += f"\n❌ {effect.title()} effect expired for {self.name}!"
            else:
                self.status_effects[effect] = (turns - 1, strength)

        for effect in expired_effects:
            del self.status_effects[effect]

        return status_msg


class BattleMoveButton(Button):

    def __init__(self, move: BattleMove, row: int = 0):
        # Choose button style based on move type
        if "heal" in (move.effect or ""):
            style = discord.ButtonStyle.green
            emoji = "💚"
        elif "energy" in (move.effect or ""):
            style = discord.ButtonStyle.blurple
            emoji = "⚡"
        elif "shield" in (move.effect or ""):
            style = discord.ButtonStyle.gray
            emoji = "🛡️"
        else:
            style = discord.ButtonStyle.red
            emoji = "⚔️"

        super().__init__(label=f"{move.name} ({move.energy_cost} ⚡)",
                         style=style,
                         emoji=emoji,
                         row=row)
        self.move = move

    async def callback(self, interaction: discord.Interaction):
        view = self.view
        if view is not None and hasattr(view, 'on_move_selected'):
            await view.on_move_selected(interaction, self.move)
        else:
            await interaction.response.send_message(
                "This battle has expired. Please start a new one.",
                ephemeral=True)


class ItemButton(Button):

    def __init__(self, item_name: str, item_effect: str, row: int = 0):
        # Choose emoji based on item effect
        if "heal" in item_effect.lower():
            emoji = "💊"
            style = discord.ButtonStyle.green
        elif "energy" in item_effect.lower():
            emoji = "🔋"
            style = discord.ButtonStyle.blurple
        else:
            emoji = "🧪"
            style = discord.ButtonStyle.gray

        super().__init__(label=item_name, style=style, emoji=emoji, row=row)
        self.item_name = item_name
        self.item_effect = item_effect

    async def callback(self, interaction: discord.Interaction):
        view = self.view
        if view is not None and hasattr(view, 'on_item_selected'):
            await view.on_item_selected(interaction, self.item_name,
                                        self.item_effect)
        else:
            await interaction.response.send_message(
                "This battle has expired. Please start a new one.",
                ephemeral=True)


class TurnBasedPvPView(View):
    """Turn-based PvP battle view that alternates between players"""
    
    def __init__(self, player1: BattleEntity, player2: BattleEntity, 
                 player1_user, player2_user, timeout: int = 300):
        super().__init__(timeout=timeout)
        self.player1 = player1
        self.player2 = player2
        self.player1_user = player1_user
        self.player2_user = player2_user
        self.current_turn = 1  # 1 for player1, 2 for player2
        self.turn_count = 0
        self.battle_log = []
        self.data_manager = None
        
        # Add initial battle log
        self.battle_log.append(f"⚔️ **PvP Battle Started!**")
        self.battle_log.append(f"{player1.name} vs {player2.name}")
        
        # Set up initial buttons for current player
        self.update_buttons()
    
    def get_current_player(self) -> BattleEntity:
        """Get the player whose turn it is"""
        return self.player1 if self.current_turn == 1 else self.player2
    
    def get_current_user(self):
        """Get the Discord user whose turn it is"""
        return self.player1_user if self.current_turn == 1 else self.player2_user
    
    def get_other_player(self) -> BattleEntity:
        """Get the player who is not currently taking a turn"""
        return self.player2 if self.current_turn == 1 else self.player1
    
    def update_buttons(self):
        """Update buttons for the current player's turn"""
        self.clear_items()
        
        current_player = self.get_current_player()
        
        # Add move buttons for current player
        for i, move in enumerate(current_player.moves):
            if i >= 20:  # Discord limit
                break
            
            # Check if player has enough energy
            can_use = current_player.current_energy >= move.energy_cost
            
            btn = BattleMoveButton(move, row=i//5)
            btn.disabled = not can_use
            
            if not can_use:
                btn.style = discord.ButtonStyle.gray
                btn.label = f"{move.name} (Need {move.energy_cost}⚡)"
            
            self.add_item(btn)
    
    async def check_interaction_permission(self, interaction: discord.Interaction) -> bool:
        """Check if the user can interact with this view"""
        current_user = self.get_current_user()
        if interaction.user.id != current_user.id:
            await interaction.response.send_message(
                f"❌ It's {current_user.display_name}'s turn!", ephemeral=True
            )
            return False
        return True
    
    def create_battle_embed(self) -> discord.Embed:
        """Create the battle status embed"""
        current_player = self.get_current_player()
        other_player = self.get_other_player()
        
        embed = discord.Embed(
            title="⚔️ Turn-Based PvP Battle",
            description=f"**Turn {self.turn_count + 1}** - {current_player.name}'s Turn",
            color=discord.Color.gold()
        )
        
        # Player 1 status
        embed.add_field(
            name=f"{self.player1.name} {'🎯' if self.current_turn == 1 else ''}",
            value=f"❤️ HP: {self.player1.current_hp}/{self.player1.stats['hp']}\n"
                  f"⚡ Energy: {self.player1.current_energy}/{self.player1.max_energy}\n"
                  f"⚔️ Power: {self.player1.stats['power']}\n"
                  f"🛡️ Defense: {self.player1.stats['defense']}",
            inline=True
        )
        
        # Player 2 status  
        embed.add_field(
            name=f"{self.player2.name} {'🎯' if self.current_turn == 2 else ''}",
            value=f"❤️ HP: {self.player2.current_hp}/{self.player2.stats['hp']}\n"
                  f"⚡ Energy: {self.player2.current_energy}/{self.player2.max_energy}\n"
                  f"⚔️ Power: {self.player2.stats['power']}\n"
                  f"🛡️ Defense: {self.player2.stats['defense']}",
            inline=True
        )
        
        # Status effects
        status_text = ""
        for player in [self.player1, self.player2]:
            if player.status_effects:
                effects = []
                for effect, (turns, strength) in player.status_effects.items():
                    effects.append(f"{effect} ({turns} turns)")
                if effects:
                    status_text += f"{player.name}: {', '.join(effects)}\n"
        
        if status_text:
            embed.add_field(name="🔮 Status Effects", value=status_text, inline=False)
        
        # Battle log (last 5 entries)
        if self.battle_log:
            log_text = "\n".join(self.battle_log[-5:])
            embed.add_field(name="📜 Battle Log", value=log_text, inline=False)
        
        return embed
    
    async def on_move_selected(self, interaction: discord.Interaction, move: BattleMove):
        """Handle when a player selects a move"""
        if not await self.check_interaction_permission(interaction):
            return
        
        current_player = self.get_current_player()
        target_player = self.get_other_player()
        
        # Check if player has enough energy
        if current_player.current_energy < move.energy_cost:
            await interaction.response.send_message(
                f"Not enough energy! You need {move.energy_cost} energy but only have {current_player.current_energy}.",
                ephemeral=True
            )
            return
        
        # Apply the move
        damage, effect_msg = current_player.apply_move(move, target_player)
        
        # Add to battle log with turn indicator
        turn_indicator = "🔥" if self.current_turn == 1 else "⚔️"
        self.battle_log.append(f"{turn_indicator} **{current_player.name}** used {move.name}!")
        if damage > 0:
            self.battle_log.append(f"💥 Dealt {damage} damage to {target_player.name}!")
        if effect_msg and "❌" not in effect_msg:
            self.battle_log.append(f"✨ {effect_msg}")
        
        # Apply damage (already handled in apply_move, but ensure consistency)
        if damage > 0:
            target_player.current_hp = max(0, target_player.current_hp - damage)
        
        # Update status effects for both players
        for player in [current_player, target_player]:
            status_msg = player.update_status_effects()
            if status_msg:
                self.battle_log.append(f"🔄 {status_msg}")
        
        # Check for battle end
        if not target_player.is_alive():
            await self.end_battle(interaction, current_player, target_player)
            return
        elif not current_player.is_alive():
            await self.end_battle(interaction, target_player, current_player)
            return
        
        # Switch turns
        self.current_turn = 2 if self.current_turn == 1 else 1
        self.turn_count += 1
        
        # Regenerate energy for both players at turn end
        current_player.current_energy = min(current_player.max_energy, current_player.current_energy + 2)
        target_player.current_energy = min(target_player.max_energy, target_player.current_energy + 2)
        
        # Update buttons for new turn
        self.update_buttons()
        
        # Update the message
        embed = self.create_battle_embed()
        await interaction.response.edit_message(embed=embed, view=self)
    
    async def end_battle(self, interaction: discord.Interaction, winner: BattleEntity, loser: BattleEntity):
        """Handle battle end and process rewards"""
        import datetime
        from achievements import QuestManager
        
        self.battle_log.append(f"🏆 **{winner.name} wins the battle!**")
        
        # Determine which player data objects correspond to winner and loser
        if winner == self.player1:
            winner_data = self.player1.player_data
            loser_data = self.player2.player_data
        else:
            winner_data = self.player2.player_data
            loser_data = self.player1.player_data
        
        # Check if we have valid data and data manager
        if not winner_data or not loser_data or not hasattr(self, 'data_manager') or not self.data_manager:
            await interaction.response.edit_message(
                embed=discord.Embed(
                    title="🏆 Battle Concluded!",
                    description=f"**{winner.name}** defeated **{loser.name}**!",
                    color=discord.Color.green()
                ),
                view=None
            )
            self.stop()
            return
        
        # Calculate rewards
        base_exp = 20
        base_gold = 15
        level_multiplier = 1.0 + (loser_data.class_level / 50.0)
        challenge_bonus = 1.0 + (max(0, loser_data.class_level - winner_data.class_level) * 0.1)
        
        exp_reward = int(base_exp * loser_data.class_level * level_multiplier * challenge_bonus)
        base_gold_reward = int(base_gold * loser_data.class_level * level_multiplier * challenge_bonus)
        
        # Apply gold multiplier from active events
        from utils import apply_gold_multiplier
        gold_reward = apply_gold_multiplier(base_gold_reward, self.data_manager)
        
        # Add rewards to winner
        exp_result = winner_data.add_exp(exp_reward, data_manager=self.data_manager)
        winner_data.add_gold(gold_reward)
        
        # Deduct gold from loser (but not too much)
        gold_penalty = min(gold_reward // 3, loser_data.gold // 10)
        loser_data.remove_gold(gold_penalty)
        
        # Set cooldowns
        current_time = datetime.datetime.now()
        pvp_cooldown_key = "pvp_cooldown"
        
        winner_data.skill_cooldowns[pvp_cooldown_key] = current_time + datetime.timedelta(minutes=30)
        loser_data.skill_cooldowns[pvp_cooldown_key] = current_time + datetime.timedelta(minutes=60)
        
        # Update win/loss stats
        winner_data.wins += 1
        loser_data.losses += 1
        
        # Update quest progress
        quest_manager = QuestManager(self.data_manager)
        quest_manager.update_quest_progress(winner_data, "daily_pvp")
        quest_manager.update_quest_progress(winner_data, "weekly_pvp")
        quest_manager.update_quest_progress(winner_data, "daily_gold", gold_reward)
        
        # Save data
        self.data_manager.save_data()
        
        # Create final embed
        embed = discord.Embed(
            title="🏆 Battle Concluded!",
            description=f"**{winner.name}** defeated **{loser.name}**!",
            color=discord.Color.green()
        )
        
        # Show final stats
        embed.add_field(
            name=f"🏆 {winner.name} (Winner)",
            value=f"❤️ HP: {winner.current_hp}/{winner.stats['hp']}\n"
                  f"⚡ Energy: {winner.current_energy}/{winner.max_energy}",
            inline=True
        )
        
        embed.add_field(
            name=f"💀 {loser.name} (Defeated)",
            value=f"❤️ HP: 0/{loser.stats['hp']}\n"
                  f"⚡ Energy: {loser.current_energy}/{loser.max_energy}",
            inline=True
        )
        
        # Show rewards
        xp_display = f"EXP: +{exp_reward} 📊"
        if exp_result["event_multiplier"] > 1.0:
            xp_display = f"EXP: {exp_reward} → {exp_result['adjusted_exp']} 📊 (🎉 {exp_result['event_name']} {exp_result['event_multiplier']}x!)"
        
        embed.add_field(
            name="🎁 Rewards",
            value=f"{xp_display}\nGold: +{gold_reward} 💰",
            inline=False
        )
        
        if exp_result["leveled_up"]:
            embed.add_field(
                name="🆙 Level Up!",
                value=f"You reached Level {winner_data.class_level}!\nYou gained 2 skill points!",
                inline=False
            )
        
        # Battle summary
        embed.add_field(
            name="📊 Battle Summary", 
            value=f"Total Turns: {self.turn_count + 1}",
            inline=False
        )
        
        # Final battle log
        if self.battle_log:
            log_text = "\n".join(self.battle_log[-6:])
            embed.add_field(name="📜 Final Battle Log", value=log_text, inline=False)
        
        await interaction.response.edit_message(embed=embed, view=None)
        self.stop()

class BattleView(RestrictedView):

    def __init__(self,
                 player: BattleEntity,
                 enemy: BattleEntity,
                 authorized_user,
                 timeout: int = 30):
        super().__init__(authorized_user, timeout=timeout)
        self.player = player
        self.enemy = enemy
        self.data_manager: Optional[
            DataManager] = None  # Will be set by start_battle
        self.battle_log = []  # Track battle actions
        self.update_buttons()

    def get_safe_message_content(self,
                                 interaction: discord.Interaction) -> str:
        """Safely extract message content from interaction, returning empty string if not possible"""
        try:
            if (hasattr(interaction, 'message') and interaction.message
                    and hasattr(interaction.message, 'content')
                    and interaction.message.content):
                return interaction.message.content
        except (AttributeError, TypeError):
            pass
        return ""

    def create_battle_embed(self) -> discord.Embed:
        """Create a formatted battle embed matching the desired layout"""
        # Create embed with dark theme
        embed = discord.Embed(
            title=f"⚔️ {self.player.name} vs {self.enemy.name}",
            color=0x2F3136  # Dark gray color to match image
        )
        
        # Action log section (show last 8 actions for better visibility)
        if self.battle_log:
            action_text = "\n".join(self.battle_log[-8:])  # Show last 8 actions
        else:
            action_text = "⚔️ Battle begins!"
        
        embed.description = action_text
        
        # Player stats section
        player_level = ""
        if self.player.is_player and self.player.player_data:
            player_level = f" (Level {self.player.player_data.class_level})"
        
        player_stats = (
            f"HP: {self.player.current_hp}/{self.player.stats['hp']} ❤️\n"
            f"Energy: {self.player.current_energy}/{self.player.max_energy} ⚡\n"
            f"Power: {self.player.stats['power']} ⚔️\n"
            f"Defense: {self.player.stats['defense']} 🛡️"
        )
        
        embed.add_field(
            name=f"{self.player.name}{player_level}",
            value=player_stats,
            inline=True
        )
        
        # Enemy stats section
        enemy_level = ""
        if hasattr(self.enemy, 'level') and self.enemy.level:
            enemy_level = f" (Level {self.enemy.level})"
        
        enemy_stats = (
            f"HP: {self.enemy.current_hp}/{self.enemy.stats['hp']} ❤️\n"
            f"Energy: {self.enemy.current_energy}/{getattr(self.enemy, 'max_energy', 100)} ⚡\n"
            f"Power: {self.enemy.stats['power']} ⚔️\n"
            f"Defense: {self.enemy.stats['defense']} 🛡️"
        )
        
        embed.add_field(
            name=f"{self.enemy.name}{enemy_level}",
            value=enemy_stats,
            inline=True
        )
        
        # Status effects section
        status_text = ""
        
        # Player status effects
        if self.player.status_effects:
            player_effects = []
            for effect, (turns, strength) in self.player.status_effects.items():
                effect_name = effect.replace("_", " ").title()
                player_effects.append(f"**{self.player.name}:** {effect_name}")
            if player_effects:
                status_text += "\n".join(player_effects)
        
        # Enemy status effects
        if self.enemy.status_effects:
            enemy_effects = []
            for effect, (turns, strength) in self.enemy.status_effects.items():
                effect_name = effect.replace("_", " ").title()
                enemy_effects.append(f"**{self.enemy.name}:** {effect_name}")
            if enemy_effects:
                if status_text:
                    status_text += "\n"
                status_text += "\n".join(enemy_effects)
        
        if status_text:
            embed.add_field(
                name="Status Effects",
                value=status_text,
                inline=False
            )
        
        return embed

    def update_buttons(self):
        # Clear existing buttons
        self.clear_items()

        # Add move buttons
        for i, move in enumerate(self.player.moves):
            # Disable buttons if not enough energy
            disabled = self.player.current_energy < move.energy_cost
            btn = BattleMoveButton(move, row=i // 2)
            btn.disabled = disabled
            self.add_item(btn)

        # Add item button if player
        if self.player.is_player and self.player.player_data:
            # Check for usable items (consumables)
            usable_items = []
            if hasattr(self.player.player_data,
                       'inventory') and self.player.player_data.inventory:
                for inv_item in self.player.player_data.inventory:
                    if inv_item.quantity > 0:
                        # Check if item has necessary attributes
                        if not hasattr(inv_item, 'item') or not inv_item.item:
                            continue

                        # Enhanced potion detection - this is the key fix for potion visibility
                        item_name = inv_item.item.name.lower() if hasattr(
                            inv_item.item, 'name') else ""
                        item_desc = inv_item.item.description.lower(
                        ) if hasattr(inv_item.item, 'description') else ""
                        item_type = inv_item.item.item_type if hasattr(
                            inv_item.item, 'item_type') else ""

                        is_usable = False

                        # First check item type (most reliable)
                        if item_type == "consumable" or item_type == "potion":
                            is_usable = True
                        # Then check item name for potion-related terms
                        elif any(
                                term in item_name for term in
                            ["potion", "elixir", "tonic", "vial", "flask"]):
                            is_usable = True
                        # Finally check description for effect-related terms
                        elif any(term in item_desc for term in [
                                "health", "heal", "energy", "restore",
                                "strength", "hp", "shield", "battle",
                                "defense", "buff", "boost"
                        ]):
                            is_usable = True

                        if is_usable:
                            usable_items.append(
                                (inv_item.item.name,
                                 getattr(inv_item.item, 'description',
                                         'A usable item')))

            # Add up to 5 item buttons (increased from 3)
            for i, (item_name, item_effect) in enumerate(usable_items[:5]):
                self.add_item(
                    ItemButton(item_name, item_effect, row=2 + (i // 2)))

    async def on_move_selected(self, interaction: discord.Interaction,
                               move: BattleMove):
        # Check if player has enough energy for the move
        if self.player.current_energy < move.energy_cost:
            # Player doesn't have enough energy, they lose their turn and regenerate
            self.player.current_energy = self.player.max_energy  # Full energy regeneration
            
            # Add to battle log
            energy_log = f"🔄 **{self.player.name}** is exhausted and cannot attack! Energy fully restored!"
            self.battle_log.append(energy_log)
            
            # Update with new embed format
            embed = self.create_battle_embed()
            await interaction.response.edit_message(embed=embed, view=self)
            
            # Skip to enemy turn
            damage, effect_msg = 0, ""
        elif "energy_recovery" in self.player.status_effects:
            # Check if player is in energy recovery mode (lost turns)
            turns_left, _ = self.player.status_effects["energy_recovery"]

            # Update turns left
            if turns_left > 1:
                self.player.status_effects["energy_recovery"] = (turns_left -
                                                                 1, 0)
                await interaction.response.edit_message(
                    content=
                    f"⚖️ You're still recovering energy! {turns_left-1} more turn(s) until you can act again.\n"
                    f"Waiting for enemy move...",
                    view=self)
                # Skip player's turn but continue with enemy turn
                damage, effect_msg = 0, ""
            else:
                # Last turn of recovery, remove the effect
                del self.player.status_effects["energy_recovery"]
                await interaction.response.edit_message(
                    content=
                    f"⚖️ You've recovered your energy and can act normally next turn!\n"
                    f"Waiting for enemy move...",
                    view=self)
                # Skip player's turn but continue with enemy turn
                damage, effect_msg = 0, ""
        else:
            # Normal turn, apply player move
            damage, effect_msg = self.player.apply_move(move, self.enemy)
            
            # Add to battle log with detailed information
            move_log = f"⚔️ **{self.player.name}** executes **{move.name}** dealing {damage} damage!"
            if effect_msg:
                move_log += f" {effect_msg}"
            self.battle_log.append(move_log)
            
            # Add HP status if significant damage
            if damage > 0:
                hp_status = f"💔 **{self.enemy.name}** HP: {self.enemy.current_hp}/{self.enemy.stats['hp']}"
                self.battle_log.append(hp_status)
            
            # Update with new embed format
            embed = self.create_battle_embed()
            await interaction.response.edit_message(embed=embed, view=self)

        # Check if enemy is defeated
        if not self.enemy.is_alive():
            # Add victory message to battle log
            self.battle_log.append(f"🎉 **VICTORY!** {self.player.name} defeated {self.enemy.name}!")
            
            # Create final battle embed
            embed = self.create_battle_embed()
            embed.color = 0x00ff00  # Green for victory
            embed.title = "🎉 Battle Result: Victory"
            
            self.stop()
            await asyncio.sleep(1)
            await interaction.edit_original_response(embed=embed, view=None)
            return

        # Enemy turn
        await asyncio.sleep(1)

        # Choose enemy move (prioritize moves they have energy for)
        available_moves = [
            m for m in self.enemy.moves
            if self.enemy.current_energy >= m.energy_cost
        ]
        if not available_moves:
            # If no moves available, enemy skips turn to regain full energy
            self.enemy.current_energy = self.enemy.max_energy  # Full energy regeneration
            
            # Add to battle log
            energy_log = f"🔄 **{self.enemy.name}** is exhausted and cannot attack! Energy fully restored!"
            self.battle_log.append(energy_log)
            
            # Update with new embed format
            embed = self.create_battle_embed()
            await interaction.edit_original_response(embed=embed, view=self)
        else:
            enemy_move = random.choice(available_moves)
            enemy_damage, enemy_effect_msg = self.enemy.apply_move(
                enemy_move, self.player)

            # Add enemy action to battle log with detailed information
            enemy_log = f"⚔️ **{self.enemy.name}** unleashes **{enemy_move.name}** dealing {enemy_damage} damage!"
            if enemy_effect_msg:
                enemy_log += f" {enemy_effect_msg}"
            self.battle_log.append(enemy_log)
            
            # Add HP status if significant damage
            if enemy_damage > 0:
                hp_status = f"💔 **{self.player.name}** HP: {self.player.current_hp}/{self.player.stats['hp']}"
                self.battle_log.append(hp_status)

            # Update with new embed format
            embed = self.create_battle_embed()
            await interaction.edit_original_response(embed=embed, view=self)

            # Check if player is defeated
            if not self.player.is_alive():
                # Battle lost
                self.stop()
                await asyncio.sleep(1)
                await interaction.edit_original_response(
                    content=
                    f"💀 Defeat! You were defeated by {self.enemy.name}!",
                    view=None)
                return

        # Update status effects and log changes
        player_status_msg = self.player.update_status_effects()
        enemy_status_msg = self.enemy.update_status_effects()
        
        # Add status effect updates to battle log if they exist
        if player_status_msg:
            self.battle_log.append(f"🔄 **{self.player.name}**: {player_status_msg}")
        if enemy_status_msg:
            self.battle_log.append(f"🔄 **{self.enemy.name}**: {enemy_status_msg}")

        # Update buttons for next turn
        self.update_buttons()

        # Update with complete battle state
        embed = self.create_battle_embed()
        await interaction.edit_original_response(embed=embed, view=self)

    async def on_item_selected(self, interaction: discord.Interaction,
                               item_name: str, item_effect: str):
        # Process item use
        player_data = self.player.player_data

        # Find the item in inventory
        item_found = False
        item_effect_applied = False
        if player_data and hasattr(player_data,
                                   'inventory') and player_data.inventory:
            for inv_item in player_data.inventory:
                if (hasattr(inv_item, 'item') and inv_item.item
                        and hasattr(inv_item.item, 'name')
                        and inv_item.item.name == item_name
                        and inv_item.quantity > 0):
                    # Found the item, reduce quantity
                    inv_item.quantity -= 1
                    item_found = True
                    break

        if not item_found:
            await interaction.response.send_message(
                "❌ Item not found or out of stock!", ephemeral=True)
            return

        # Apply item effect
        effect_msg = ""
        item_effect_applied = True

        # Extract numerical values from effect description
        import re
        number_matches = re.findall(r'\d+', item_effect)
        effect_number = int(number_matches[0]) if number_matches else 0

        # Determine effect type and apply it
        item_effect_lower = item_effect.lower()

        # Healing items
        if any(heal_term in item_effect_lower
               for heal_term in ["heal", "health", "hp", "restore health"]):
            # Calculate healing amount
            heal_amount = effect_number if effect_number > 0 else int(
                self.player.stats["hp"] * 0.3)  # Default 30% heal
            self.player.current_hp = min(self.player.stats["hp"],
                                         self.player.current_hp + heal_amount)
            effect_msg = f"💚 You used {item_name} and healed for {heal_amount} HP!"

        # Energy items
        elif any(energy_term in item_effect_lower for energy_term in
                 ["energy", "mana", "stamina", "restore energy"]):
            # Calculate energy amount
            energy_amount = effect_number if effect_number > 0 else 50  # Default energy restore
            self.player.current_energy = min(
                100, self.player.current_energy + energy_amount)
            effect_msg = f"⚡ You used {item_name} and restored {energy_amount} energy!"

        # Buff items
        elif any(buff_term in item_effect_lower
                 for buff_term in ["strength", "power", "damage", "attack"]):
            # Apply strength buff
            buff_duration = effect_number if effect_number > 0 else 3  # Default 3 turns
            buff_strength = 0.3  # 30% more damage
            self.player.status_effects["strength"] = (buff_duration,
                                                      buff_strength)
            effect_msg = f"💪 You used {item_name} and gained increased strength for {buff_duration} turns!"

        # Defense items
        elif any(def_term in item_effect_lower for def_term in
                 ["shield", "defense", "protect", "barrier", "armor"]):
            # Apply shield buff
            shield_duration = effect_number if effect_number > 0 else 3  # Default 3 turns
            shield_strength = 0.4  # 40% less damage
            self.player.status_effects["shield"] = (shield_duration,
                                                    shield_strength)
            effect_msg = f"🛡️ You used {item_name} and gained a protective shield for {shield_duration} turns!"

        # Dual effect items (healing + energy)
        elif any(dual_term in item_effect_lower for dual_term in
                 ["potion", "elixir", "restoration", "recovery"]):
            # Apply both healing and energy
            heal_amount = int(self.player.stats["hp"] * 0.2)  # 20% heal
            energy_amount = 30  # 30 energy
            self.player.current_hp = min(self.player.stats["hp"],
                                         self.player.current_hp + heal_amount)
            self.player.current_energy = min(
                100, self.player.current_energy + energy_amount)
            effect_msg = f"✨ You used {item_name} and restored {heal_amount} HP and {energy_amount} energy!"

        else:
            # Generic effect for unknown item types
            heal_amount = int(self.player.stats["hp"] *
                              0.1)  # Small heal as fallback
            self.player.current_hp = min(self.player.stats["hp"],
                                         self.player.current_hp + heal_amount)
            effect_msg = f"🧪 You used {item_name} and gained a minor effect (+{heal_amount} HP)!"

        # Add item usage to battle log
        self.battle_log.append(f"🧪 **{self.player.name}** uses **{item_name}**!")
        if "heal" in effect_msg.lower() or "hp" in effect_msg.lower():
            hp_status = f"💚 **{self.player.name}** HP: {self.player.current_hp}/{self.player.stats['hp']}"
            self.battle_log.append(hp_status)
        if "energy" in effect_msg.lower():
            energy_status = f"⚡ **{self.player.name}** Energy: {self.player.current_energy}"
            self.battle_log.append(energy_status)
        
        # Update embed with item usage
        embed = self.create_battle_embed()
        await interaction.response.edit_message(embed=embed, view=self)

        # Save player data
        if player_data and hasattr(
                self, 'data_manager') and self.data_manager is not None:
            self.data_manager.save_data()

        # Enemy turn (items don't consume a turn, but enemy still attacks)
        await asyncio.sleep(1)

        # Choose enemy move
        available_moves = [
            m for m in self.enemy.moves
            if self.enemy.current_energy >= m.energy_cost
        ]
        if not available_moves:
            # If no moves available, enemy skips turn to regain energy
            self.enemy.current_energy = min(
                self.enemy.stats.get("energy", 100),
                self.enemy.current_energy + 30)
            
            # Add enemy energy recovery to battle log
            energy_log = f"🔄 **{self.enemy.name}** is exhausted and regains 30 energy!"
            self.battle_log.append(energy_log)
            
            # Update embed
            embed = self.create_battle_embed()
            await interaction.edit_original_response(embed=embed, view=self)
        else:
            enemy_move = random.choice(available_moves)
            enemy_damage, enemy_effect_msg = self.enemy.apply_move(
                enemy_move, self.player)

            # Add enemy action to battle log
            enemy_log = f"⚔️ **{self.enemy.name}** unleashes **{enemy_move.name}** dealing {enemy_damage} damage!"
            if enemy_effect_msg:
                enemy_log += f" {enemy_effect_msg}"
            self.battle_log.append(enemy_log)
            
            # Add HP status if significant damage
            if enemy_damage > 0:
                hp_status = f"💔 **{self.player.name}** HP: {self.player.current_hp}/{self.player.stats['hp']}"
                self.battle_log.append(hp_status)
            
            # Update embed
            embed = self.create_battle_embed()
            await interaction.edit_original_response(embed=embed, view=self)

            # Check if player is defeated
            if not self.player.is_alive():
                # Add defeat message to battle log
                self.battle_log.append(f"💀 **DEFEAT!** {self.player.name} was defeated by {self.enemy.name}!")
                
                # Create final battle embed
                embed = self.create_battle_embed()
                embed.color = 0xff0000  # Red for defeat
                embed.title = "💀 Battle Result: Defeat"
                
                self.stop()
                await asyncio.sleep(1)
                await interaction.edit_original_response(embed=embed, view=None)
                return

        # Update status effects and log changes
        player_status_msg = self.player.update_status_effects()
        enemy_status_msg = self.enemy.update_status_effects()
        
        # Add status effect updates to battle log if they exist
        if player_status_msg:
            self.battle_log.append(f"🔄 **{self.player.name}**: {player_status_msg}")
        if enemy_status_msg:
            self.battle_log.append(f"🔄 **{self.enemy.name}**: {enemy_status_msg}")

        # Update buttons for next turn
        self.update_buttons()

        # Update with complete battle state
        embed = self.create_battle_embed()
        await interaction.edit_original_response(embed=embed, view=self)


async def start_battle(ctx, player_data: PlayerData, enemy_name: str,
                       enemy_level: int, data_manager: DataManager):
    """Start a battle between the player and an enemy"""
    from utils import GAME_CLASSES

    # Get player class data
    if player_data.class_name not in GAME_CLASSES:
        await ctx.send(
            "❌ Invalid player class. Please use !start to choose a class.")
        return

    class_data = GAME_CLASSES[player_data.class_name]

    # Calculate player stats including equipment and level
    player_stats = player_data.get_stats(GAME_CLASSES)

    # Use unified move generation system
    from unified_moves import get_player_moves
    player_moves = get_player_moves(player_data.class_name or "Warrior")

    # Create player entity
    player_entity = BattleEntity(ctx.author.display_name,
                                 player_stats,
                                 player_moves,
                                 is_player=True,
                                 player_data=player_data)

    # Create enemy entity using unified move system
    enemy_stats = generate_enemy_stats(enemy_name, enemy_level,
                                       player_data.class_level)
    from unified_moves import get_enemy_moves
    enemy_moves = get_enemy_moves(enemy_name)

    enemy_entity = BattleEntity(enemy_name, enemy_stats, enemy_moves)
    enemy_entity.level = enemy_level  # Set level for display

    # Create battle embed
    embed = discord.Embed(
        title=f"⚔️ Battle: {ctx.author.display_name} vs {enemy_name}",
        description=f"A {enemy_name} (Level {enemy_level}) appears!",
        color=discord.Color.red())

    # Show active special abilities if any
    active_abilities_text = ""
    if hasattr(player_data,
               "special_abilities") and player_data.special_abilities:
        for ability_name, ability_data in player_data.special_abilities.items(
        ):
            # Check if ability is active (not on cooldown)
            if ability_data.get("last_used"):
                try:
                    last_used = datetime.datetime.fromisoformat(
                        ability_data["last_used"])
                    now = datetime.datetime.now()
                    hours_passed = (now - last_used).total_seconds() / 3600

                    if hours_passed >= ability_data.get("cooldown", 0):
                        active_abilities_text += f"• {ability_name} - {ability_data.get('description', 'Special ability')}\n"
                except (ValueError, TypeError):
                    pass

    # Show active effects if any
    active_effects_text = ""
    if hasattr(player_data, "active_effects") and player_data.active_effects:
        for effect_name, effect_data in player_data.active_effects.items():
            active_effects_text += f"• {effect_name} ({effect_data.get('duration', 0)} battles remaining)\n"

    # Add fields for abilities and effects if any
    if active_abilities_text:
        embed.add_field(name="⚡ Active Abilities",
                        value=active_abilities_text,
                        inline=False)

    if active_effects_text:
        embed.add_field(name="🧪 Active Effects",
                        value=active_effects_text,
                        inline=False)

    # Add player stats
    embed.add_field(
        name=f"{ctx.author.display_name} (Level {player_data.class_level})",
        value=f"HP: {player_entity.current_hp}/{player_entity.stats['hp']} ❤️\n"
        f"Battle Energy: {player_entity.current_energy}/{player_data.max_battle_energy} ⚡\n"
        f"Power: {player_entity.stats['power']} ⚔️\n"
        f"Defense: {player_entity.stats['defense']} 🛡️",
        inline=True)

    # Add enemy stats
    embed.add_field(
        name=f"{enemy_name} (Level {enemy_level})",
        value=f"HP: {enemy_entity.current_hp}/{enemy_entity.stats['hp']} ❤️\n"
        f"Energy: {enemy_entity.current_energy}/{enemy_entity.stats.get('energy', 100)} ⚡\n"
        f"Power: {enemy_entity.stats['power']} ⚔️\n"
        f"Defense: {enemy_entity.stats['defense']} 🛡️",
        inline=True)

    # Create battle view
    battle_view = BattleView(player_entity, enemy_entity, ctx.author, timeout=180)
    battle_view.data_manager = data_manager
    
    # Add enemy level to enemy entity for display purposes
    enemy_entity.level = enemy_level
    
    # Add battle start message to log
    battle_view.battle_log.append(f"⚔️ **Battle begins!** {ctx.author.display_name} vs {enemy_name}")
    
    # Use new embed format
    embed = battle_view.create_battle_embed()

    battle_msg = await ctx.send(embed=embed, view=battle_view)

    # Wait for battle to end
    await battle_view.wait()

    # Process battle results
    if not enemy_entity.is_alive():
        # Player won
        # Calculate rewards
        exp_reward = calculate_exp_reward(enemy_level, player_data.class_level)
        base_gold_reward = calculate_gold_reward(enemy_level)
        
        # Apply gold multiplier from active events
        from utils import apply_gold_multiplier
        gold_reward = apply_gold_multiplier(base_gold_reward, data_manager)

        # Add rewards
        exp_result = player_data.add_exp(exp_reward, data_manager=data_manager)
        leveled_up = exp_result["leveled_up"]
        player_data.add_gold(gold_reward)

        # Update stats
        player_data.wins += 1
        
        # Track achievement stats
        if not hasattr(player_data, 'gold_earned'):
            player_data.gold_earned = 0
        player_data.gold_earned += gold_reward

        # Update quest progress for daily and weekly quest tracking
        from achievements import QuestManager
        quest_manager = QuestManager(data_manager)

        # Collect all quest completion messages
        quest_messages = []

        # Update various quest types that would be triggered by a battle win
        completed_quests = quest_manager.update_quest_progress(player_data, "daily_wins")
        for quest in completed_quests:
            quest_messages.append(quest_manager.create_quest_completion_message(quest))

        completed_quests = quest_manager.update_quest_progress(player_data, "weekly_wins")
        for quest in completed_quests:
            quest_messages.append(quest_manager.create_quest_completion_message(quest))
        
        # Update long-term battle tracking
        completed_quests = quest_manager.update_quest_progress(player_data, "total_wins")
        for quest in completed_quests:
            quest_messages.append(quest_manager.create_quest_completion_message(quest))

        # Update gold quest tracking  
        completed_quests = quest_manager.update_quest_progress(player_data, "daily_gold", gold_reward)
        for quest in completed_quests:
            quest_messages.append(quest_manager.create_quest_completion_message(quest))

        if "boss" in enemy_name.lower():
            # This is a boss battle
            completed_quests = quest_manager.update_quest_progress(player_data, "weekly_bosses")
            for quest in completed_quests:
                quest_messages.append(quest_manager.create_quest_completion_message(quest))

        # Check for item drops
        drop_msg = ""
        if random.random() < 0.2:  # 20% chance for regular item drop
            from equipment import generate_random_item
            new_item = generate_random_item(player_data.class_level)

            # Add to inventory
            from equipment import add_item_to_inventory
            add_item_to_inventory(player_data, new_item)

            # Update item collection quest progress
            completed_quests = quest_manager.update_quest_progress(player_data, "daily_items")
            for quest in completed_quests:
                quest_messages.append(quest_manager.create_quest_completion_message(quest))

            drop_msg = f"\n⚡ The {enemy_name} dropped: **{new_item.name}**!"

        # Check for special item drop (rarer)
        special_drop_msg = ""
        if random.random() < 0.05:  # 5% chance for special drop
            from special_items import get_random_special_drop
            special_item = await get_random_special_drop(
                player_data.class_level)

            if special_item:
                # Add to inventory
                from equipment import add_item_to_inventory
                add_item_to_inventory(player_data, special_item)

                # Update item collection quest progress for special items too
                completed_quests = quest_manager.update_quest_progress(player_data, "daily_items")
                for quest in completed_quests:
                    quest_messages.append(quest_manager.create_quest_completion_message(quest))

                special_drop_msg = f"\n🌟 Rare drop! You found: **{special_item.name}**!"

        # Handle consumable duration reduction
        expired_effects = []
        if hasattr(player_data, "active_effects"):
            for effect_name, effect_data in player_data.active_effects.items():
                # Reduce duration by 1 battle
                effect_data["duration"] -= 1

                # If duration is 0, mark for removal
                if effect_data["duration"] <= 0:
                    expired_effects.append(effect_name)

            # Remove expired effects
            for effect_name in expired_effects:
                del player_data.active_effects[effect_name]

        # Check for achievements
        new_achievements = data_manager.check_player_achievements(player_data)

        # Save data
        data_manager.save_data()

        # Send results
        result_embed = discord.Embed(
            title="🎉 Victory!",
            description=f"You defeated the {enemy_name}!",
            color=discord.Color.green())

        # Create proper EXP display with event information
        exp_display = f"EXP Gained: {exp_reward}"
        if exp_result["event_multiplier"] > 1.0:
            exp_display = f"EXP Gained: {exp_reward} → {exp_result['adjusted_exp']} (🎉 {exp_result['event_name']} {exp_result['event_multiplier']}x!)"
        else:
            exp_display = f"EXP Gained: {exp_result['adjusted_exp']}"
        
        result_embed.add_field(
            name="Rewards",
            value=f"{exp_display} 📊\n"
            f"Gold: +{gold_reward} 💰{drop_msg}{special_drop_msg}",
            inline=False)

        # Show quest completion messages if any
        if quest_messages:
            quest_text = "\n".join(quest_messages)
            result_embed.add_field(name="🎯 Quest Progress", value=quest_text, inline=False)

        # Show achievement completions if any
        if new_achievements:
            achievement_text = ""
            for achievement in new_achievements:
                badge = achievement.get("badge", "🏆")
                points = achievement.get("points", 0)
                achievement_text += f"{badge} **{achievement['name']}** ({points} pts)\n"
                achievement_text += f"*{achievement['description']}*\n"
                
                # Add rewards info
                if achievement.get("reward"):
                    rewards = []
                    reward_data = achievement["reward"]
                    if "exp" in reward_data:
                        rewards.append(f"EXP: +{reward_data['exp']}")
                    if "gold" in reward_data:
                        rewards.append(f"Gold: +{reward_data['gold']}")
                    
                    # Add achievement points to rewards
                    if "points" in achievement:
                        rewards.append(f"Achievement Points: +{achievement['points']}")
                    
                    if rewards:
                        achievement_text += f"Rewards: {', '.join(rewards)}\n"
                achievement_text += "\n"
            
            result_embed.add_field(name="🏆 New Achievements!", value=achievement_text.strip(), inline=False)

        # Show info about expired effects if any
        if expired_effects:
            expired_text = "\n".join(
                [f"• {effect_name}" for effect_name in expired_effects])
            result_embed.add_field(name="⏱️ Effects Expired",
                                   value=expired_text,
                                   inline=False)

        if leveled_up:
            # Check for additional achievements after leveling up
            level_achievements = data_manager.check_player_achievements(player_data)
            
            # Add level achievements to the existing ones and update display
            if level_achievements:
                all_new_achievements = new_achievements + level_achievements
                achievement_text = ""
                for achievement in all_new_achievements:
                    badge = achievement.get("badge", "🏆")
                    points = achievement.get("points", 0)
                    achievement_text += f"{badge} **{achievement['name']}** ({points} pts)\n"
                    achievement_text += f"*{achievement['description']}*\n"
                    
                    # Add rewards info
                    if achievement.get("reward"):
                        rewards = []
                        reward_data = achievement["reward"]
                        if "exp" in reward_data:
                            rewards.append(f"EXP: +{reward_data['exp']}")
                        if "gold" in reward_data:
                            rewards.append(f"Gold: +{reward_data['gold']}")
                        
                        # Add achievement points to rewards
                        if "points" in achievement:
                            rewards.append(f"Achievement Points: +{achievement['points']}")
                        
                        if rewards:
                            achievement_text += f"Rewards: {', '.join(rewards)}\n"
                    achievement_text += "\n"
                
                # Update achievement display
                for i, field in enumerate(result_embed.fields):
                    if field.name == "🏆 New Achievements!":
                        result_embed.set_field_at(i, name="🏆 New Achievements!", value=achievement_text.strip(), inline=False)
                        break
                else:
                    result_embed.add_field(name="🏆 New Achievements!", value=achievement_text.strip(), inline=False)
            
            result_embed.add_field(
                name="Level Up!",
                value=f"🆙 You reached Level {player_data.class_level}!\n"
                f"You gained 3 skill points! Use !skills to allocate them.",
                inline=False)

        await ctx.send(embed=result_embed)

    elif not player_entity.is_alive():
        # Player lost
        # Update stats
        player_data.losses += 1

        # Small consolation reward
        pity_exp = calculate_exp_reward(enemy_level,
                                        player_data.class_level) // 3
        exp_result = player_data.add_exp(pity_exp, data_manager=data_manager)

        # Save data
        data_manager.save_data()

        # Send results
        result_embed = discord.Embed(
            title="💀 Defeat",
            description=f"You were defeated by the {enemy_name}!",
            color=discord.Color.red())

        # Create proper EXP display with event information for defeat case
        exp_display = f"EXP: {pity_exp}"
        if exp_result["event_multiplier"] > 1.0:
            exp_display = f"EXP: {pity_exp} → {exp_result['adjusted_exp']} (🎉 {exp_result['event_name']} {exp_result['event_multiplier']}x!)"
        else:
            exp_display = f"EXP: {exp_result['adjusted_exp']}"
            
        result_embed.add_field(name="Consolation",
                               value=f"{exp_display} 📊\n"
                               f"You'll get them next time!",
                               inline=False)

        await ctx.send(embed=result_embed)
    else:
        # Battle timed out
        await ctx.send("⏱️ The battle timed out! Neither side wins.")


def generate_enemy_stats(enemy_name: str, enemy_level: int,
                         player_level: int) -> Dict[str, int]:
    """Generate enemy stats based on name and level"""
    # Base stats scaling with level
    base_power = 8 + (enemy_level * 2)
    base_defense = 5 + (enemy_level * 1.5)
    base_hp = 80 + (enemy_level * 10)
    base_speed = 6 + (enemy_level * 0.5)

    # Adjust based on enemy type
    if "Cursed" in enemy_name:
        # Cursed enemies have high power but low defense
        power_mod = 1.3
        defense_mod = 0.8
        hp_mod = 0.9
        speed_mod = 1.2
    elif "Armored" in enemy_name:
        # Armored enemies have high defense but low speed
        power_mod = 0.9
        defense_mod = 1.8
        hp_mod = 1.2
        speed_mod = 0.7
    elif "Giant" in enemy_name:
        # Giant enemies have high HP but low speed
        power_mod = 1.3
        defense_mod = 1.1
        hp_mod = 1.6
        speed_mod = 0.6
    elif "Specter" in enemy_name:
        # Specters have high speed but low HP
        power_mod = 1.1
        defense_mod = 0.7
        hp_mod = 0.8
        speed_mod = 1.7
    else:
        # Default balanced enemy
        power_mod = 1.0
        defense_mod = 1.0
        hp_mod = 1.0
        speed_mod = 1.0

    # Create stats
    stats = {
        "power": int(base_power * power_mod),
        "defense": int(base_defense * defense_mod),
        "hp": int(base_hp * hp_mod),
        "speed": int(base_speed * speed_mod),
        "energy": 100  # All enemies start with full energy
    }

    # Scale difficulty based on player level difference
    level_diff = enemy_level - player_level

    if level_diff > 0:
        # Enemy is higher level - make them MUCH harder
        # Higher level enemies should be very challenging
        power_boost = 1.0 + (level_diff * 0.15
                             )  # 15% increase per level difference
        defense_boost = 1.0 + (level_diff * 0.10
                               )  # 10% increase per level difference
        hp_boost = 1.0 + (level_diff * 0.20
                          )  # 20% increase per level difference

        stats["power"] = int(stats["power"] * power_boost)
        stats["defense"] = int(stats["defense"] * defense_boost)
        stats["hp"] = int(stats["hp"] * hp_boost)
    elif level_diff < -2:
        # Enemy is much lower level, still make them challenging
        difficulty_mod = 1.0 + (abs(level_diff) * 0.05
                                )  # 5% increase per level below player
        stats["power"] = int(stats["power"] * difficulty_mod)
        stats["defense"] = int(stats["defense"] * difficulty_mod)

    # Ensure no negative stats - enforce minimum values
    stats["power"] = max(5, stats["power"])
    stats["defense"] = max(5, stats["defense"])
    stats["hp"] = max(50, stats["hp"])
    stats["speed"] = max(5, stats["speed"])

    return stats


def generate_enemy_moves(enemy_name: str) -> List[BattleMove]:
    """Generate enemy moves based on their name"""
    moves = [
        BattleMove("Attack", 1.0, 10)  # Basic attack for all enemies
    ]

    # Add specific moves based on enemy type
    if "Cursed" in enemy_name:
        moves.append(
            BattleMove("Curse", 1.2, 25, "weakness",
                       "Deal damage and weaken target"))
        moves.append(BattleMove("Dark Blast", 1.7, 35))
    elif "Armored" in enemy_name:
        moves.append(
            BattleMove("Shield Bash", 0.8, 20, "shield",
                       "Deal damage and gain a shield"))
        moves.append(BattleMove("Heavy Swing", 1.5, 30))
    elif "Giant" in enemy_name:
        moves.append(BattleMove("Ground Slam", 1.4, 30))
        moves.append(
            BattleMove("Roar", 0.6, 25, "strength",
                       "Deal damage and gain strength"))
    elif "Specter" in enemy_name:
        moves.append(
            BattleMove("Soul Drain", 1.1, 20, "energy_restore",
                       "Deal damage and restore energy"))
        moves.append(BattleMove("Phantom Strike", 1.6, 35))
    else:
        # Default additional moves
        moves.append(BattleMove("Heavy Attack", 1.4, 25))
        moves.append(BattleMove("Quick Strike", 0.8, 15))

    return moves


def get_dungeon_exp_for_level(level: int) -> int:
    """Get the XP reward that a dungeon appropriate for this level would give"""
    # Map player levels to dungeon XP rewards based on level requirements
    if level >= 95:
        return 20000  # Realm of Eternity
    elif level >= 90:
        return 12000  # Void Citadel
    elif level >= 80:
        return 8000   # Celestial Spire
    elif level >= 70:
        return 6000   # Dragon's Lair
    elif level >= 60:
        return 4500   # Shadow Realm
    elif level >= 50:
        return 3000   # Astral Nexus
    elif level >= 40:
        return 2000   # Forbidden Library
    elif level >= 35:
        return 1500   # Sunken Temple
    elif level >= 30:
        return 1000   # Corrupted Sanctum
    elif level >= 25:
        return 750    # Crystal Caverns
    elif level >= 20:
        return 500    # Infernal Citadel
    elif level >= 15:
        return 350    # Abyssal Depths
    elif level >= 10:
        return 200    # Cursed Shrine
    elif level >= 5:
        return 120    # Forgotten Cave
    else:
        return 50     # Ancient Forest

def calculate_exp_reward(enemy_level: int, player_level: int) -> int:
    """Calculate experience reward based on enemy and player levels - 25% of total dungeon completion XP"""
    # Get the dungeon XP for player's level and take 25% (1/4 of dungeon completion)
    dungeon_exp = get_dungeon_exp_for_level(player_level)
    base_battle_exp = int(dungeon_exp * 0.25)

    # Apply level difference modifier (smaller adjustments since base is already appropriate)
    level_diff = enemy_level - player_level
    if level_diff > 0:
        # Slight bonus for defeating higher level enemies
        exp_modifier = 1.0 + (level_diff * 0.1)
    elif level_diff < 0:
        # Reduced XP for defeating lower level enemies
        exp_modifier = max(0.3, 1.0 + (level_diff * 0.15))
    else:
        # Same level
        exp_modifier = 1.0

    return int(base_battle_exp * exp_modifier)


def calculate_gold_reward(enemy_level: int) -> int:
    """Calculate gold reward based on enemy level"""
    base_gold = 10 + (enemy_level * 5)
    variance = random.uniform(0.8, 1.2)
    return int(base_gold * variance)


def calculate_cursed_energy_reward(enemy_level: int) -> int:
    """Legacy function for backward compatibility"""
    return calculate_gold_reward(
        enemy_level)  # Redirect to gold reward function


async def start_pvp_battle(ctx, target_member, player_data, target_data,
                           data_manager):
    """Start a PvP battle between two players"""
    from utils import GAME_CLASSES

    # Validate both players have classes
    if not player_data.class_name or not target_data.class_name:
        await ctx.send(
            "❌ Both players need to have selected a class to battle!")
        return

    # Check if players are within reasonable level range - making it a bit wider for more PvP opportunities
    level_diff = abs(player_data.class_level - target_data.class_level)
    max_allowed_diff = 5  # Increased from 3 to 5 for more battle opportunities

    if level_diff > max_allowed_diff:
        await ctx.send(
            f"❌ Level difference too high! You can only battle players within {max_allowed_diff} levels of your own (current difference: {level_diff})."
        )
        return

    # Check if either player is currently in a cooldown
    current_time = datetime.datetime.now()
    pvp_cooldown_key = "pvp_cooldown"

    if pvp_cooldown_key in player_data.skill_cooldowns:
        cooldown_time = player_data.skill_cooldowns[pvp_cooldown_key]
        if cooldown_time > current_time:
            time_left = (cooldown_time - current_time).total_seconds()
            minutes = int(time_left // 60)
            seconds = int(time_left % 60)
            await ctx.send(
                f"❌ You're on PvP cooldown! Try again in {minutes}m {seconds}s."
            )
            return

    if pvp_cooldown_key in target_data.skill_cooldowns:
        cooldown_time = target_data.skill_cooldowns[pvp_cooldown_key]
        if cooldown_time > current_time:
            time_left = (cooldown_time - current_time).total_seconds()
            minutes = int(time_left // 60)
            seconds = int(time_left % 60)
            await ctx.send(
                f"❌ {target_member.display_name} is on PvP cooldown! Try again in {minutes}m {seconds}s."
            )
            return

    # Get player stats
    player_stats = player_data.get_stats(GAME_CLASSES)
    target_stats = target_data.get_stats(GAME_CLASSES)

    # Get moves for both players
    player_moves = []
    target_moves = []

    # Basic moves for everyone
    player_moves.append(BattleMove("Basic Attack", 1.0, 10))
    player_moves.append(BattleMove("Heavy Strike", 1.5, 25))

    target_moves.append(BattleMove("Basic Attack", 1.0, 10))
    target_moves.append(BattleMove("Heavy Strike", 1.5, 25))

    # Add class-specific moves for player
    if player_data.class_name == "Spirit Striker":
        player_moves.append(
            BattleMove("Cursed Combo", 2.0, 35, "weakness",
                       "Deal damage and weaken enemy"))
        player_moves.append(
            BattleMove("Soul Siphon", 1.2, 20, "energy_restore",
                       "Deal damage and restore energy"))
    elif player_data.class_name == "Domain Tactician":
        player_moves.append(
            BattleMove("Barrier Pulse", 0.8, 30, "shield",
                       "Deal damage and gain a shield"))
        player_moves.append(
            BattleMove("Tactical Heal", 0.5, 25, "heal",
                       "Deal damage and heal yourself"))
    elif player_data.class_name == "Flash Rogue":
        player_moves.append(
            BattleMove("Shadowstep", 1.7, 30, "strength",
                       "Deal damage and gain increased damage"))
        player_moves.append(
            BattleMove("Quick Strikes", 0.7, 15, None,
                       "Deal multiple quick strikes"))

    # Add class-specific moves for target
    if target_data.class_name == "Spirit Striker":
        target_moves.append(
            BattleMove("Cursed Combo", 2.0, 35, "weakness",
                       "Deal damage and weaken enemy"))
        target_moves.append(
            BattleMove("Soul Siphon", 1.2, 20, "energy_restore",
                       "Deal damage and restore energy"))
    elif target_data.class_name == "Domain Tactician":
        target_moves.append(
            BattleMove("Barrier Pulse", 0.8, 30, "shield",
                       "Deal damage and gain a shield"))
        target_moves.append(
            BattleMove("Tactical Heal", 0.5, 25, "heal",
                       "Deal damage and heal yourself"))
    elif target_data.class_name == "Flash Rogue":
        target_moves.append(
            BattleMove("Shadowstep", 1.7, 30, "strength",
                       "Deal damage and gain increased damage"))
        target_moves.append(
            BattleMove("Quick Strikes", 0.7, 15, None,
                       "Deal multiple quick strikes"))

    # Create player entities
    player_entity = BattleEntity(ctx.author.display_name,
                                 player_stats,
                                 player_moves,
                                 is_player=True,
                                 player_data=player_data)

    target_entity = BattleEntity(target_member.display_name,
                                 target_stats,
                                 target_moves,
                                 is_player=True,
                                 player_data=target_data)

    # Create battle embed
    embed = discord.Embed(
        title=
        f"⚔️ PvP Battle: {ctx.author.display_name} vs {target_member.display_name}",
        description=
        f"{ctx.author.mention} has challenged {target_member.mention} to a battle!",
        color=discord.Color.gold())

    # Add player stats
    embed.add_field(
        name=f"{ctx.author.display_name} (Level {player_data.class_level})",
        value=f"HP: {player_entity.current_hp}/{player_entity.stats['hp']} ❤️\n"
        f"Battle Energy: {player_entity.current_energy}/{player_data.max_battle_energy} ⚡\n"
        f"Power: {player_entity.stats['power']} ⚔️\n"
        f"Defense: {player_entity.stats['defense']} 🛡️",
        inline=True)

    # Add target stats
    embed.add_field(
        name=f"{target_member.display_name} (Level {target_data.class_level})",
        value=f"HP: {target_entity.current_hp}/{target_entity.stats['hp']} ❤️\n"
        f"Battle Energy: {target_entity.current_energy}/{target_data.max_battle_energy} ⚡\n"
        f"Power: {target_entity.stats['power']} ⚔️\n"
        f"Defense: {target_entity.stats['defense']} 🛡️",
        inline=True)

    # Create turn-based battle view
    battle_view = TurnBasedPvPView(player_entity, target_entity, ctx.author, target_member, timeout=300)
    battle_view.data_manager = data_manager

    # Create initial battle embed
    initial_embed = battle_view.create_battle_embed()
    battle_msg = await ctx.send(embed=initial_embed, view=battle_view)

    # Wait for battle to end
    await battle_view.wait()

    # Battle results are handled in the turn-based view's end_battle method
    # No additional processing needed here
