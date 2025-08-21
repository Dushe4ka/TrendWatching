#!/usr/bin/env python3
"""
Тест для проверки конфигурации
"""

import sys
import os

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Загружаем переменные окружения
from dotenv import load_dotenv
load_dotenv()

def test_config():
    """Тестирование конфигурации"""
    print("🔧 Тестирование конфигурации")
    print("=" * 50)
    
    try:
        # Тест 1: Импорт конфигурации
        print("1. Импорт конфигурации...")
        from config import get_role_system_config
        print("   ✅ Конфигурация импортирована")
        
        # Тест 2: Получение конфигурации
        print("\n2. Получение конфигурации...")
        role_config = get_role_system_config()
        print(f"   ✅ Конфигурация получена: {role_config}")
        
        # Тест 3: Проверка секции lark
        print("\n3. Проверка секции lark...")
        if "lark" in role_config:
            lark_config = role_config["lark"]
            print(f"   ✅ Секция lark найдена: {lark_config}")
            
            # Проверяем обязательные поля
            required_fields = ["app_id", "app_secret", "table_app_id", "table_id"]
            for field in required_fields:
                if field in lark_config:
                    value = lark_config[field]
                    print(f"   ✅ {field}: {value}")
                else:
                    print(f"   ❌ {field}: НЕ НАЙДЕН")
        else:
            print("   ❌ Секция lark НЕ НАЙДЕНА")
        
        # Тест 4: Проверка переменных окружения
        print("\n4. Проверка переменных окружения...")
        env_vars = {
            "LARK_APP_ID": os.getenv("LARK_APP_ID"),
            "LARK_APP_SECRET": os.getenv("LARK_APP_SECRET"),
            "LARK_TABLE_APP_ID": os.getenv("LARK_TABLE_APP_ID"),
            "LARK_TABLE_ID": os.getenv("LARK_TABLE_ID")
        }
        
        for var_name, var_value in env_vars.items():
            if var_value:
                print(f"   ✅ {var_name}: {var_value}")
            else:
                print(f"   ❌ {var_name}: НЕ УСТАНОВЛЕНА")
        
        print("\n✅ Тестирование конфигурации завершено успешно!")
        
    except Exception as e:
        print(f"\n❌ Ошибка при тестировании конфигурации: {str(e)}")
        import traceback
        traceback.print_exc()


def test_imports():
    """Тестирование импортов"""
    print("\n📦 Тестирование импортов")
    print("=" * 50)
    
    try:
        # Тест 1: Импорт UserInfo
        print("1. Импорт UserInfo...")
        from role_model.base_provider import UserInfo
        print("   ✅ UserInfo импортирован")
        
        # Тест 2: Импорт misc
        print("\n2. Импорт misc...")
        from bot.utils.misc import category_to_callback
        print("   ✅ category_to_callback импортирован")
        
        # Тест 3: Импорт inline_keyboards
        print("\n3. Импорт inline_keyboards...")
        from bot.keyboards.inline_keyboards import get_main_menu_keyboard
        print("   ✅ get_main_menu_keyboard импортирован")
        
        # Тест 4: Импорт callback_utils
        print("\n4. Импорт callback_utils...")
        from bot.utils.callback_utils import create_digest_callback
        print("   ✅ create_digest_callback импортирован")
        
        print("\n✅ Тестирование импортов завершено успешно!")
        
    except Exception as e:
        print(f"\n❌ Ошибка при тестировании импортов: {str(e)}")
        import traceback
        traceback.print_exc()


def main():
    """Основная функция"""
    print("🚀 Запуск тестов конфигурации")
    print("=" * 80)
    
    test_config()
    test_imports()
    
    print("\n🏁 Тестирование завершено")


if __name__ == "__main__":
    main() 