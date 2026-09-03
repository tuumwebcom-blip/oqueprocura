import os

files = [
    'index.html', 'search.html', 'anuncie.html', 'profile.html', 'como-funciona.html'
]

for file in files:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    new_content = content.replace("Desenvolvido pro TUUMWEB.COM", "Desenvolvido por TUUMWEB.COM")
    
    with open(file, 'w', encoding='utf-8') as f:
        f.write(new_content)
print("done")
