import os
import re

html_files = [f for f in os.listdir('.') if f.endswith('.html')]

# Adjust styling based on where it's used if needed, but a standard height works best
img_tag = '<img src="LOGO.png" alt="O Que Procura?" style="height: 36px; width: auto;">'

pattern = re.compile(
    r'(<a\s+[^>]*class="[^"]*\blogo\b[^"]*"[^>]*>)\s*(?:<i[^>]*></i>\s*)?O Que Procura\?\s*</a>',
    re.DOTALL | re.IGNORECASE
)

for f in html_files:
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    
    def replacer(match):
        start_tag = match.group(1)
        return start_tag + '\n        ' + img_tag + '\n      </a>'
        
    new_content, count = pattern.subn(replacer, content)
    
    if count > 0:
        with open(f, 'w', encoding='utf-8') as file:
            file.write(new_content)
        print(f"Updated {count} logos in {f}")
    else:
        print(f"No match found in {f}")
