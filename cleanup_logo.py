import os

html_files = [f for f in os.listdir('.') if f.endswith('.html')]

for f in html_files:
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Remove inline height styles from logo img tags - let CSS control the size
    new_content = content.replace(' style="height: 160px; width: auto;"', '')
    
    if new_content != content:
        with open(f, 'w', encoding='utf-8') as file:
            file.write(new_content)
        print(f"Cleaned inline styles in {f}")
    else:
        print(f"No inline styles in {f}")
