#!/usr/bin/env python3
import json
import stats

# Load races and jobs
with open('races.json') as f:
    races = json.load(f)
with open('jobs.json') as f:
    jobs = json.load(f)

# Test character creation
elf_char = stats.create_character_stats(races, 'elf', 'archer', jobs, level=1)
print('=== Elf Archer Character ===')
print('Base Stats:', elf_char['base_stats'])
print('Level:', elf_char['level'])
print('Max HP:', elf_char['derived_stats'].get('max_hp'))
print('Max SP:', elf_char['derived_stats'].get('max_sp'))
print('ATK:', elf_char['derived_stats'].get('atk'))
print('MATK:', elf_char['derived_stats'].get('matk'))
print('DEF:', elf_char['derived_stats'].get('def'))
print('Flee:', elf_char['derived_stats'].get('flee'))
print('CRIT:', elf_char['derived_stats'].get('crit'), '%')
print()

print('=== Dwarf Blacksmith Character ===')
dwarf_char = stats.create_character_stats(races, 'dwarf', 'blacksmith', jobs, level=1)
print('Base Stats:', dwarf_char['base_stats'])
print('Max HP:', dwarf_char['derived_stats'].get('max_hp'))
print('ATK:', dwarf_char['derived_stats'].get('atk'))
print('DEF:', dwarf_char['derived_stats'].get('def'))
print('Weight Limit:', dwarf_char['derived_stats'].get('weight_limit'), 'kg')
print()

print('=== Demon Mage Character ===')
demon_char = stats.create_character_stats(races, 'demon', 'mage', jobs, level=1)
print('Base Stats:', demon_char['base_stats'])
print('Max HP:', demon_char['derived_stats'].get('max_hp'))
print('Max SP:', demon_char['derived_stats'].get('max_sp'))
print('MATK:', demon_char['derived_stats'].get('matk'))
print('MDEF:', demon_char['derived_stats'].get('mdef'))

print('\n✅ Stats system test completed successfully!')
