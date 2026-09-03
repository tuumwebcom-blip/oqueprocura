import os
import re

files = [
    'index.html', 'search.html', 'anuncie.html', 'checkout.html', 
    'profile.html', 'como-funciona.html', 'admin.html'
]

def replacer(match):
    tag = match.group(0)
    if 'filter: brightness' not in tag:
        return tag.replace('LOGO.png', 'LOGO AZUL.png')
    return tag

for file in files:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    new_content = re.sub(r'<img[^>]+src="LOGO\.png"[^>]*>', replacer, content)
    
    with open(file, 'w', encoding='utf-8') as f:
        f.write(new_content)
print("done")
