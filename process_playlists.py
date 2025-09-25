import requests
import json
import os
from pathlib import Path


PLAYLIST_URLS = {
    "http://epg.one/edem_epg_ico.m3u8": "standard.m3u8",
    "http://epg.one/edem_epg_ico2.m3u8": "thematic_1.m3u8",
    "http://epg.one/edem_epg_ico3.m3u8": "thematic_2.m3u8"
}


ICONS_MAP_URL = "https://raw.githubusercontent.com/Lorax121/epg_v2/main/icons_map.json"


OLD_EPG_URL = 'x-tvg-url="http://epg.one/epg.xml.gz"'
NEW_EPG_URL = 'x-tvg-url="https://raw.githubusercontent.com/Lorax121/epg_v2/main/data/epg.xml.gz"'


NEW_ICONS_BASE_URL = "https://raw.githubusercontent.com/Lorax121/epg_v2/main/"


OUTPUT_DIR = "playlists"



def main():
    """
    Главная функция для выполнения всего процесса.
    """
    print("🚀 Запуск скрипта обновления плейлистов...")

    
    repo_name = os.getenv('GITHUB_REPOSITORY')
    if not repo_name:
        raise ValueError("Ошибка: Переменная окружения GITHUB_REPOSITORY не установлена.")

    
    output_path = Path(OUTPUT_DIR)
    output_path.mkdir(exist_ok=True)
    print(f"✅ Директория для результатов: '{OUTPUT_DIR}'")

    
    try:
        print(f"🔄 Скачиваю карту иконок с: {ICONS_MAP_URL}")
        response = requests.get(ICONS_MAP_URL, timeout=30)
        response.raise_for_status()
        icons_data = response.json()
        icon_pool = icons_data.get("icon_pool", {})
        if not icon_pool:
            print("⚠️ Предупреждение: 'icon_pool' в карте иконок пуст или отсутствует.")
        else:
            print(f"✅ Карта иконок успешно загружена. Найдено {len(icon_pool)} иконок в 'icon_pool'.")
    except requests.RequestException as e:
        print(f"❌ Критическая ошибка: Не удалось скачать карту иконок: {e}")
        return
    except json.JSONDecodeError as e:
        print(f"❌ Критическая ошибка: Не удалось разобрать JSON из карты иконок: {e}")
        return

    
    processed_files = []
    for url, filename in PLAYLIST_URLS.items():
        print(f"\n--- Обработка: {filename} ---")
        try:
            
            print(f"📥 Скачиваю плейлист с: {url}")
            playlist_content = requests.get(url, timeout=30).text

            
            original_lines = len(playlist_content.splitlines())
            playlist_content = playlist_content.replace(OLD_EPG_URL, NEW_EPG_URL)
            print("🔧 Заменил ссылку на EPG.")

            
            replacements_count = 0
            for old_icon_url, new_icon_path in icon_pool.items():
                if old_icon_url in playlist_content:
                    
                    full_new_icon_url = f"{NEW_ICONS_BASE_URL}{new_icon_path}"
                    
                    playlist_content = playlist_content.replace(old_icon_url, full_new_icon_url)
                    replacements_count += 1
            
            if replacements_count > 0:
                print(f"🖼️ Заменил {replacements_count} ссылок на иконки.")
            else:
                print("ℹ️  Совпадений по иконкам не найдено.")

            
            file_path = output_path / filename
            file_path.write_text(playlist_content, encoding='utf-8')
            print(f"💾 Файл сохранен: {file_path}")
            processed_files.append(filename)

        except requests.RequestException as e:
            print(f"❌ Ошибка при обработке {url}: {e}")

    
    print("\n--- Обновление README.md ---")
    update_readme(processed_files, repo_name)
    print("✅ README.md успешно обновлен.")
    print("\n🎉 Все задачи выполнены!")


def update_readme(playlist_files, repo_name):
    """
    Генерирует и сохраняет новый README.md с ссылками на плейлисты.
    """
    readme_content = [
        "
        "Этот репозиторий автоматически скачивает и модифицирует плейлисты, заменяя ссылки на EPG и иконки каналов.\n",
        "Обновление происходит раз в неделю или при ручном запуске.\n",
        "
    ]

    base_url = f"https://raw.githubusercontent.com/{repo_name}/main/{OUTPUT_DIR}/"

    for filename in playlist_files:
        
        playlist_name = Path(filename).stem.replace('_', ' ').capitalize()
        full_url = f"{base_url}{filename}"
        readme_content.append(f"* **{playlist_name}**")
        readme_content.append(f"  ```\n  {full_url}\n  ```")

    readme_path = Path("README.md")
    readme_path.write_text("\n".join(readme_content), encoding='utf-8')


if __name__ == "__main__":
    main()
