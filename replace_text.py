import os

def replace_text_in_files(directory, search_str, replace_str):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.html'):
                filepath = os.path.join(root, file)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if search_str in content:
                    content = content.replace(search_str, replace_str)
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"Updated: {filepath}")

if __name__ == '__main__':
    replace_text_in_files('templates', '한국어 아카데미', '성문사이버학원')
