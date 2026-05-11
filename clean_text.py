import os
import re

def remove_emojis_and_em_dashes(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Remplacer le tiret quadratin (—) par un tiret simple (-)
    content = content.replace('—', '-')

    # Regex pour les emojis. On enlève les caractères Unicode au-delà des caractères standards.
    # Les emojis se trouvent généralement dans les blocs U+1F300 - U+1FAFF, U+2600 - U+27BF, etc.
    # On peut utiliser une regex simplifiée pour matcher tout ce qui n'est pas ASCII basique + latin accentué + symboles courants
    # Mais le plus simple est de cibler les emojis utilisés dans le code : 🌳, ✅, 🎯, 🚨, 🔔, 📦, 👥, 📁, 🔍, ⚠, ↩
    emojis_to_remove = ['🌳', '✅', '🎯', '🚨', '🔔', '📦', '👥', '📁', '🔍', '⚠', '↩', '✨', '🚀']
    for emoji in emojis_to_remove:
        # If there's a trailing space after the emoji, we might want to remove it too if it's orphaned, 
        # but just removing the emoji string is safer.
        content = content.replace(emoji + ' ', '')
        content = content.replace(emoji, '')

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

def main():
    src_dir = '/home/jolan/Developpement/Arbor/frontend/src'
    for root, dirs, files in os.walk(src_dir):
        for file in files:
            if file.endswith(('.ts', '.tsx', '.html', '.css', '.json')):
                remove_emojis_and_em_dashes(os.path.join(root, file))
                
    # Also clean README.md and DEX
    for md_file in ['/home/jolan/Developpement/Arbor/README.md', '/home/jolan/Developpement/Arbor/docs/DEX_ARBOR.md']:
        if os.path.exists(md_file):
            remove_emojis_and_em_dashes(md_file)
            
    # And install.sh
    if os.path.exists('/home/jolan/Developpement/Arbor/install.sh'):
        remove_emojis_and_em_dashes('/home/jolan/Developpement/Arbor/install.sh')

if __name__ == '__main__':
    main()
