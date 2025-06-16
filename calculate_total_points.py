#!/usr/bin/env python3
"""
Calculate total achievement points available in the game
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from achievements import ACHIEVEMENTS

def main():
    total_points = 0
    achievement_count = 0
    categories = {}
    
    print("Achievement Points Breakdown:")
    print("=" * 50)
    
    for achievement_id, achievement in ACHIEVEMENTS.items():
        points = achievement['points']
        category = achievement['category']
        name = achievement['name']
        
        total_points += points
        achievement_count += 1
        
        if category not in categories:
            categories[category] = {'count': 0, 'points': 0, 'achievements': []}
        
        categories[category]['count'] += 1
        categories[category]['points'] += points
        categories[category]['achievements'].append(f"{name} ({points} pts)")
    
    # Display by category
    for category, data in categories.items():
        print(f"\n{category.upper()} ACHIEVEMENTS:")
        print(f"Total: {data['count']} achievements, {data['points']} points")
        for achievement in data['achievements']:
            print(f"  - {achievement}")
    
    print("\n" + "=" * 50)
    print(f"TOTAL ACHIEVEMENT POINTS AVAILABLE: {total_points}")
    print(f"TOTAL NUMBER OF ACHIEVEMENTS: {achievement_count}")
    
    return total_points

if __name__ == "__main__":
    main()