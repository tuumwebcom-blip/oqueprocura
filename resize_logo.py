import os

html_files = [f for f in os.listdir('.') if f.endswith('.html')]

for f in html_files:
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Increase the standard logo size from 80px to 160px, and super_admin from 55px to 80px
    new_content = content.replace('height: 80px;', 'height: 160px;').replace('height: 55px;', 'height: 80px;')
    
    if new_content != content:
        with open(f, 'w', encoding='utf-8') as file:
            file.write(new_content)
        print(f"Updated sizes in {f}")
