import discord
from discord.ui import Button, View, Select
from typing import Dict, List, Optional, Any, Union
from data_models import DataManager, PlayerData, Item, InventoryItem
from materials import MATERIAL_CATEGORIES, MATERIAL_RARITIES, GATHERING_TOOLS
from crafting_system import CRAFTING_CATEGORIES, CRAFTING_STATIONS

# Main encyclopedia sections
ENCYCLOPEDIA_SECTIONS = {
    "Weapons": {
        "description": "All weapons and combat tools",
        "icon": "⚔️",
        "subsections": ["Swords", "Axes", "Maces", "Daggers", "Bows", "Staves"]
    },
    "Armor": {
        "description": "Protective equipment and armor sets",
        "icon": "🛡️",
        "subsections": ["Helmets", "Chestplates", "Leggings", "Boots", "Shields", "Robes"]
    },
    "Accessories": {
        "description": "Jewelry and magical trinkets",
        "icon": "💍",
        "subsections": ["Rings", "Necklaces", "Belts", "Earrings", "Bracelets"]
    },
    "Materials": {
        "description": "Crafting materials and resources",
        "icon": "📦",
        "subsections": list(MATERIAL_CATEGORIES.keys())
    },
    "Potions": {
        "description": "Consumable potions and elixirs",
        "icon": "🧪",
        "subsections": ["Health Potions", "Mana Potions", "Stat Potions", "Resistance Potions", "Utility Potions"]
    },
    "Tools": {
        "description": "Gathering and crafting tools",
        "icon": "🔨",
        "subsections": ["Mining Tools", "Foraging Tools", "Fishing Tools", "Crafting Tools", "Magical Tools"]
    },
    "Special Items": {
        "description": "Rare and unique items",
        "icon": "✨",
        "subsections": ["Guild Items", "Class Items", "Quest Items", "Dungeon Keys"]
    },
    "All Items": {
        "description": "Full catalogue of all items in the game",
        "icon": "📚",
        "subsections": []  # Will show everything
    }
}

class EncyclopediaView(View):
    def __init__(self, player_data: PlayerData, data_manager: DataManager):
        super().__init__(timeout=60)
        self.player = player_data
        self.data_manager = data_manager
        self.category = None
        self.subsection = None
        self.page = 0
        self.items_per_page = 10

        # Add category select
        self.add_category_select()

        # Add navigation buttons
        self.add_navigation_buttons()

    def add_category_select(self):
        """Add dropdown for encyclopedia categories"""
        options = []
        for category, data in ENCYCLOPEDIA_SECTIONS.items():
            options.append(discord.SelectOption(
                label=f"{data['icon']} {category}",
                description=data["description"][:100],
                value=category
            ))

        select = Select(
            placeholder="Select Category",
            options=options,
            custom_id="category_select"
        )
        select.callback = self.category_callback
        self.add_item(select)

    def add_subsection_select(self):
        """Add dropdown for encyclopedia subsections"""
        if not self.category:
            return

        subsections = ENCYCLOPEDIA_SECTIONS[self.category].get("subsections", [])
        if not subsections:
            return

        options = []
        for subsection in subsections:
            options.append(discord.SelectOption(
                label=subsection,
                value=subsection
            ))

        # Add an "All" option
        options.append(discord.SelectOption(
            label="All " + self.category,
            value="All"
        ))

        select = Select(
            placeholder="Select Subsection",
            options=options,
            custom_id="subsection_select"
        )
        select.callback = self.subsection_callback
        self.add_item(select)

    def add_navigation_buttons(self):
        """Add navigation buttons for pagination"""
        prev_button = Button(label="◀️ Previous", custom_id="prev_page", style=discord.ButtonStyle.gray)
        prev_button.callback = self.prev_page_callback

        next_button = Button(label="Next ▶️", custom_id="next_page", style=discord.ButtonStyle.gray)
        next_button.callback = self.next_page_callback

        self.add_item(prev_button)
        self.add_item(next_button)

    async def category_callback(self, interaction: discord.Interaction):
        """Handle category selection"""
        self.category = interaction.data["values"][0]
        self.subsection = None
        self.page = 0

        # Clear the view and rebuild it
        self.clear_items()
        self.add_category_select()
        self.add_subsection_select()
        self.add_navigation_buttons()

        embed = self.create_encyclopedia_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    async def subsection_callback(self, interaction: discord.Interaction):
        """Handle subsection selection"""
        self.subsection = interaction.data["values"][0]
        if self.subsection == "All":
            self.subsection = None
        self.page = 0

        embed = self.create_encyclopedia_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    async def prev_page_callback(self, interaction: discord.Interaction):
        """Handle previous page button"""
        if self.page > 0:
            self.page -= 1

        embed = self.create_encyclopedia_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    async def next_page_callback(self, interaction: discord.Interaction):
        """Handle next page button"""
        # Get list of items for the current category/subsection
        items = self.get_items_for_view()

        # Calculate total pages
        total_pages = (len(items) + self.items_per_page - 1) // self.items_per_page

        if self.page < total_pages - 1:
            self.page += 1

        embed = self.create_encyclopedia_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    def get_items_for_view(self) -> List[Dict[str, Any]]:
        """Get items for the current view based on category and subsection"""
        if not self.category:
            return []

        items = []

        # Special case for "All Items"
        if self.category == "All Items":
            # Add all weapons, armor, etc. from crafting system
            for category, category_data in CRAFTING_CATEGORIES.items():
                for type_name, type_data in category_data.get("types", {}).items():
                    for i, product in enumerate(type_data.get("products", [])):
                        level_range = type_data.get("level_ranges", [(1, 10)])[i] if i < len(type_data.get("level_ranges", [])) else (1, 10)
                        for rarity in MATERIAL_RARITIES:
                            items.append({
                                "name": f"{rarity} {product}",
                                "type": f"{category}:{type_name}",
                                "level_req": level_range[0],
                                "description": f"A {rarity.lower()} quality {product.lower()}.",
                                "rarity": rarity
                            })

            # Add all materials
            for category, category_data in MATERIAL_CATEGORIES.items():
                for i, material_type in enumerate(category_data.get("types", [])):
                    level_range = category_data.get("level_ranges", [(1, 10)])[i] if i < len(category_data.get("level_ranges", [])) else (1, 10)
                    for rarity in MATERIAL_RARITIES:
                        items.append({
                            "name": f"{rarity} {material_type}",
                            "type": f"Material:{category}",
                            "level_req": level_range[0],
                            "description": f"A {rarity.lower()} quality {material_type.lower()} used in crafting.",
                            "rarity": rarity
                        })

            # Add all gathering tools
            for category, category_data in GATHERING_TOOLS.items():
                for tool_type in category_data.get("Tool Types", []):
                    for tier in category_data.get("Tiers", []):
                        items.append({
                            "name": f"{tier.get('name')} {tool_type}",
                            "type": f"Tool:{category}",
                            "level_req": tier.get('level_req', 1),
                            "description": f"A {tier.get('name').lower()} quality {tool_type.lower()} used for gathering {category.lower()} materials.",
                            "rarity": self.get_tool_rarity(tier.get('level_req', 1))
                        })

            # Add all crafting stations
            for station_name, station_data in CRAFTING_STATIONS.items():
                items.append({
                    "name": station_name,
                    "type": "Station",
                    "level_req": station_data.get('level_req', 1),
                    "description": station_data.get('description', ''),
                    "rarity": self.get_tool_rarity(station_data.get('level_req', 1))
                })

            return items

        # Handle specific categories
        if self.category == "Materials":
            # Add materials from the specified category or all material categories
            if self.subsection:
                category_data = MATERIAL_CATEGORIES.get(self.subsection, {})
                for i, material_type in enumerate(category_data.get("types", [])):
                    level_range = category_data.get("level_ranges", [(1, 10)])[i] if i < len(category_data.get("level_ranges", [])) else (1, 10)
                    for rarity in MATERIAL_RARITIES:
                        items.append({
                            "name": f"{rarity} {material_type}",
                            "type": f"Material:{self.subsection}",
                            "level_req": level_range[0],
                            "description": f"A {rarity.lower()} quality {material_type.lower()} used in crafting.",
                            "rarity": rarity
                        })
            else:
                # All material categories
                for category, category_data in MATERIAL_CATEGORIES.items():
                    for i, material_type in enumerate(category_data.get("types", [])):
                        level_range = category_data.get("level_ranges", [(1, 10)])[i] if i < len(category_data.get("level_ranges", [])) else (1, 10)
                        for rarity in MATERIAL_RARITIES:
                            items.append({
                                "name": f"{rarity} {material_type}",
                                "type": f"Material:{category}",
                                "level_req": level_range[0],
                                "description": f"A {rarity.lower()} quality {material_type.lower()} used in crafting.",
                                "rarity": rarity
                            })
        elif self.category == "Tools":
            # Add tools from the specified category or all tool categories
            if self.subsection:
                for category, category_data in GATHERING_TOOLS.items():
                    if f"{self.subsection}" == f"{category} Tools":
                        for tool_type in category_data.get("Tool Types", []):
                            for tier in category_data.get("Tiers", []):
                                items.append({
                                    "name": f"{tier.get('name')} {tool_type}",
                                    "type": f"Tool:{category}",
                                    "level_req": tier.get('level_req', 1),
                                    "description": f"A {tier.get('name').lower()} quality {tool_type.lower()} used for gathering {category.lower()} materials.",
                                    "rarity": self.get_tool_rarity(tier.get('level_req', 1))
                                })
            else:
                # All tool categories
                for category, category_data in GATHERING_TOOLS.items():
                    for tool_type in category_data.get("Tool Types", []):
                        for tier in category_data.get("Tiers", []):
                            items.append({
                                "name": f"{tier.get('name')} {tool_type}",
                                "type": f"Tool:{category}",
                                "level_req": tier.get('level_req', 1),
                                "description": f"A {tier.get('name').lower()} quality {tool_type.lower()} used for gathering {category.lower()} materials.",
                                "rarity": self.get_tool_rarity(tier.get('level_req', 1))
                            })
        else:
            # All other categories with crafted items
            craft_category = self.category
            if craft_category in CRAFTING_CATEGORIES:
                if self.subsection:
                    # Specific subsection
                    type_data = CRAFTING_CATEGORIES[craft_category].get("types", {}).get(self.subsection, {})
                    if type_data:
                        for i, product in enumerate(type_data.get("products", [])):
                            level_range = type_data.get("level_ranges", [(1, 10)])[i] if i < len(type_data.get("level_ranges", [])) else (1, 10)
                            for rarity in MATERIAL_RARITIES:
                                items.append({
                                    "name": f"{rarity} {product}",
                                    "type": f"{craft_category}:{self.subsection}",
                                    "level_req": level_range[0],
                                    "description": f"A {rarity.lower()} quality {product.lower()}.",
                                    "rarity": rarity
                                })
                else:
                    # All subsections in this category
                    for type_name, type_data in CRAFTING_CATEGORIES[craft_category].get("types", {}).items():
                        for i, product in enumerate(type_data.get("products", [])):
                            level_range = type_data.get("level_ranges", [(1, 10)])[i] if i < len(type_data.get("level_ranges", [])) else (1, 10)
                            for rarity in MATERIAL_RARITIES:
                                items.append({
                                    "name": f"{rarity} {product}",
                                    "type": f"{craft_category}:{type_name}",
                                    "level_req": level_range[0],
                                    "description": f"A {rarity.lower()} quality {product.lower()}.",
                                    "rarity": rarity
                                })

        return items

    def get_tool_rarity(self, level_req: int) -> str:
        """Get rarity for tools based on level requirement"""
        if level_req >= 950:
            return "Divine"
        elif level_req >= 800:
            return "Transcendent"
        elif level_req >= 600:
            return "Primordial"
        elif level_req >= 400:
            return "Mythic"
        elif level_req >= 250:
            return "Legendary"
        elif level_req >= 150:
            return "Epic"
        elif level_req >= 100:
            return "Rare"
        elif level_req >= 50:
            return "Uncommon"
        else:
            return "Common"

    def create_encyclopedia_embed(self) -> discord.Embed:
        """Create the encyclopedia embed for current view"""
        icon = ""
        if self.category:
            icon = ENCYCLOPEDIA_SECTIONS.get(self.category, {}).get("icon", "📚")

        title = f"{icon} Item Encyclopedia"
        if self.category:
            title += f" - {self.category}"
            if self.subsection:
                title += f" - {self.subsection}"

        embed = discord.Embed(
            title=title,
            color=discord.Color.blue()
        )

        if not self.category:
            # Main encyclopedia page
            embed.description = "Welcome to the Ethereal Ascendancy Encyclopedia! Here you can browse all items, weapons, armors, tools, and materials available in the game."

            for category, data in ENCYCLOPEDIA_SECTIONS.items():
                embed.add_field(
                    name=f"{data['icon']} {category}",
                    value=data["description"],
                    inline=True
                )

            return embed

        # Get items for current view
        items = self.get_items_for_view()

        # Calculate start and end index for pagination
        start_idx = self.page * self.items_per_page
        end_idx = min(start_idx + self.items_per_page, len(items))

        # Calculate total pages
        total_pages = max(1, (len(items) + self.items_per_page - 1) // self.items_per_page)

        # Set description with pagination info
        embed.description = f"Showing items {start_idx + 1}-{end_idx} of {len(items)} | Page {self.page + 1}/{total_pages}"

        # Add items to embed
        if len(items) == 0:
            embed.description = "No items found for this category."
        else:
            for i in range(start_idx, end_idx):
                item = items[i]

                # Get color based on rarity
                color_name = ""
                if item["rarity"] in MATERIAL_RARITIES:
                    color_value = MATERIAL_RARITIES[item["rarity"]].get("color", 0xFFFFFF)
                    color_name = item["rarity"]

                # Format name with rarity coloring 
                name = f"[{color_name}] {item['name']} (Lvl {item['level_req']}+)"

                # Format value with type info
                value = f"**Type:** {item['type']}\n**Description:** {item['description']}"

                embed.add_field(
                    name=name,
                    value=value,
                    inline=False
                )

        # Set footer with player info
        embed.set_footer(text=f"Player: {self.player.name} | Level: {self.player.level}")

        return embed

class EncyclopediaExploreView(View):
    def __init__(self, player_data: PlayerData, data_manager: DataManager):
        super().__init__(timeout=60)
        self.player = player_data
        self.data_manager = data_manager

        # Add buttons for main sections
        self.add_section_buttons()

    def add_section_buttons(self):
        """Add buttons for main encyclopedia sections"""
        # First row
        weapons_btn = Button(
            label="⚔️ Weapons", 
            custom_id="weapons",
            style=discord.ButtonStyle.primary
        )
        weapons_btn.callback = self.weapons_callback
        self.add_item(weapons_btn)

        armor_btn = Button(
            label="🛡️ Armor", 
            custom_id="armor",
            style=discord.ButtonStyle.primary
        )
        armor_btn.callback = self.armor_callback
        self.add_item(armor_btn)

        accessories_btn = Button(
            label="💍 Accessories", 
            custom_id="accessories",
            style=discord.ButtonStyle.primary
        )
        accessories_btn.callback = self.accessories_callback
        self.add_item(accessories_btn)

        # Second row
        materials_btn = Button(
            label="📦 Materials", 
            custom_id="materials",
            style=discord.ButtonStyle.success
        )
        materials_btn.callback = self.materials_callback
        self.add_item(materials_btn)

        tools_btn = Button(
            label="🔨 Tools", 
            custom_id="tools",
            style=discord.ButtonStyle.success
        )
        tools_btn.callback = self.tools_callback
        self.add_item(tools_btn)

        potions_btn = Button(
            label="🧪 Potions", 
            custom_id="potions",
            style=discord.ButtonStyle.success
        )
        potions_btn.callback = self.potions_callback
        self.add_item(potions_btn)

        # Third row
        special_btn = Button(
            label="✨ Special Items", 
            custom_id="special",
            style=discord.ButtonStyle.secondary
        )
        special_btn.callback = self.special_callback
        self.add_item(special_btn)

        all_btn = Button(
            label="📚 All Items", 
            custom_id="all",
            style=discord.ButtonStyle.danger
        )
        all_btn.callback = self.all_callback
        self.add_item(all_btn)

    async def weapons_callback(self, interaction: discord.Interaction):
        await self.section_callback(interaction, "Weapons")

    async def armor_callback(self, interaction: discord.Interaction):
        await self.section_callback(interaction, "Armor")

    async def accessories_callback(self, interaction: discord.Interaction):
        await self.section_callback(interaction, "Accessories")

    async def materials_callback(self, interaction: discord.Interaction):
        await self.section_callback(interaction, "Materials")

    async def tools_callback(self, interaction: discord.Interaction):
        await self.section_callback(interaction, "Tools")

    async def potions_callback(self, interaction: discord.Interaction):
        await self.section_callback(interaction, "Potions")

    async def special_callback(self, interaction: discord.Interaction):
        await self.section_callback(interaction, "Special Items")

    async def all_callback(self, interaction: discord.Interaction):
        await self.section_callback(interaction, "All Items")

    async def section_callback(self, interaction: discord.Interaction, category: str):
        """Handle section button click"""
        view = EncyclopediaView(self.player, self.data_manager)
        view.category = category

        embed = view.create_encyclopedia_embed()

        # Clear the view and rebuild it
        view.clear_items()
        view.add_category_select()
        view.add_subsection_select()
        view.add_navigation_buttons()

        await interaction.response.edit_message(embed=embed, view=view)

async def encyclopedia_command(ctx, data_manager: DataManager, category: str = None):
    """Browse the item and material encyclopedia"""
    player = data_manager.get_player(ctx.author.id)

    view = EncyclopediaExploreView(player, data_manager)

    embed = discord.Embed(
        title="📚 Ethereal Ascendancy Encyclopedia",
        description="Welcome to the comprehensive encyclopedia of Ethereal Ascendancy! Browse thousands of items, materials, equipment, and more.",
        color=discord.Color.blue()
    )

    # Add sections to the embed
    for category_name, data in ENCYCLOPEDIA_SECTIONS.items():
        # Skip "All Items" from the overview to save space
        if category_name != "All Items":
            subsections = ", ".join(data.get("subsections", [])[:3])
            if len(data.get("subsections", [])) > 3:
                subsections += "..."

            embed.add_field(
                name=f"{data['icon']} {category_name}",
                value=f"{data['description']}\nIncludes: {subsections}",
                inline=True
            )

    # Add player info
    # Using user_id to get Discord username and player.user_level for level
    username = ctx.author.name if ctx.author else "Unknown"
    embed.set_footer(text=f"Player: {username} | Level: {player.user_level}")

    await ctx.send(embed=embed, view=view)

async def browser_command(ctx, data_manager: DataManager, category: str = None):
    """Alias for encyclopedia command"""
    await encyclopedia_command(ctx, data_manager, category)

async def codex_command(ctx, data_manager: DataManager, category: str = None):
    """Alias for encyclopedia command"""
    await encyclopedia_command(ctx, data_manager, category)