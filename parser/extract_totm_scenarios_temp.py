import pdfplumber
import re

pdf = pdfplumber.open('../data/TOTM_Rules.pdf')

scenarios = {}
for i in range(5, 60):
    text = pdf.pages[i].extract_text()
    for line in text.split('\n'):
        match = re.search(r'scenar[iI]o\s+(\d+):\s*(.+)', line, re.IGNORECASE)
        if match:
            num = int(match.group(1))
            name = match.group(2).strip()
            name = re.split(r'\s+vIctory\s+condItIons|turn\s+afterward|Accelerated', name, re.IGNORECASE)[0]
            name = name.strip()
            
            # Fix OCR issues - title case preserving
            replacements = {
                'the battle of port GIbson': 'The Battle of Port Gibson',
                'InvasIon and breakout': 'Invasion and Breakout',
                'unIte your troops': 'Unite Your Troops',
                'yankee blItzkrIeG': 'Yankee Blitzkrieg',
                'lorInG\'s memorandum': 'Loring\'s Memorandum',
                'Grant moves West': 'Grant Moves West',
                'champIon hIll': 'Champion Hill',
                'I move at once': 'I Move At Once',
                'thIs Is success': 'This Is Success',
                'army of relIef': 'Army of Relief',
                'InflIct all the punIshment you can': 'Inflict All the Punishment You Can',
                'startInG and endInG the Game': 'Starting and Ending the Game'
            }
            
            name_lower = name.lower()
            for old, new in replacements.items():
                if old.lower() == name_lower:
                    name = new
                    break
            
            if num not in scenarios:
                scenarios[num] = name

for num in sorted(scenarios.keys()):
    print(f'{num}: "{scenarios[num]}",')
