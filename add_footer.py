import os
import re

files = [
    'index.html', 'search.html', 'anuncie.html', 'profile.html', 'como-funciona.html'
]

for file in files:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # We want to replace the standard footer-bottom paragraph
    old_p = "<p>&copy; 2026 O Que Procura?. Construindo melhores conexões.</p>"
    new_p = "<p>&copy; 2026 O Que Procura?. Construindo melhores conexões.</p>\n        <p class=\"mt-2 text-white\" style=\"font-weight: 600; letter-spacing: 0.05em;\">Desenvolvido pro TUUMWEB.COM</p>"
    
    new_content = content.replace(old_p, new_p)
    
    with open(file, 'w', encoding='utf-8') as f:
        f.write(new_content)
print("done")
