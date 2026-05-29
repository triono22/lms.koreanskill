import os

filepath = 'templates/landing_page.html'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('href="/accounts/register/"', 'href="https://koreanskill.my.id"')

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated registration links in landing_page.html")
