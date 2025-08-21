import os
import requests
import asyncio
import time
from aiogram import Dispatcher, types
from aiogram.fsm.context import FSMContext
from bot.states.states import AuthStates
from bot.keyboards.inline_keyboards import (
    get_auth_menu_keyboard,
    get_auth_service_menu_keyboard,
    get_main_menu_back_keyboard
)
from bot.utils.misc import has_admin_permissions

# Конфигурация
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://localhost:8000")
TELEGRAM_API_ID = os.getenv("API_ID", "27259576")
TELEGRAM_API_HASH = os.getenv("API_HASH", "f9662a5c2300c4d881b05fb63344ba93")

async def auth_menu_callback(callback_query: types.CallbackQuery):
    """Обработчик меню авторизации"""
    user_id = callback_query.from_user.id
    username = callback_query.from_user.username
    
    if not await has_admin_permissions(user_id, username):
        await callback_query.answer("❌ У вас нет прав для доступа к этому разделу")
        return
    
    keyboard = get_auth_menu_keyboard()
    await callback_query.message.edit_text(
        "🔐 Авторизация Telegram аккаунтов:\nВыберите действие:",
        reply_markup=keyboard
    )

async def auth_service_menu_callback(callback_query: types.CallbackQuery):
    """Обработчик меню сервиса авторизации"""
    user_id = callback_query.from_user.id
    username = callback_query.from_user.username
    
    if not await has_admin_permissions(user_id, username):
        await callback_query.answer("❌ У вас нет прав для доступа к этому разделу")
        return
    
    keyboard = get_auth_service_menu_keyboard()
    await callback_query.message.edit_text(
        "🔧 Управление сервисом авторизации:\nВыберите действие:",
        reply_markup=keyboard
    )

async def add_new_account_callback(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик добавления нового аккаунта"""
    if not await has_admin_permissions(callback_query.from_user.id, callback_query.from_user.username):
        await callback_query.answer("❌ У вас нет прав для доступа к этому разделу")
        return
    
    await callback_query.message.edit_text(
        "📱 Добавление нового Telegram аккаунта\n\n"
        "Введите номер телефона в формате:\n"
        "+7XXXXXXXXXX\n\n"
        "Например: +79091234567",
        reply_markup=get_main_menu_back_keyboard()
    )
    await state.set_state(AuthStates.waiting_for_phone)

async def process_phone_number(message: types.Message, state: FSMContext):
    """Обработчик ввода номера телефона"""
    if not await has_admin_permissions(message.from_user.id, message.from_user.username):
        await message.answer("❌ У вас нет прав для доступа к этому разделу")
        await state.clear()
        return
    
    phone_number = message.text.strip()
    
    # Проверяем формат номера
    if not phone_number.startswith('+') or len(phone_number) < 10:
        await message.answer(
            "❌ Неверный формат номера телефона!\n\n"
            "Введите номер в формате: +7XXXXXXXXXX\n"
            "Например: +79091234567"
        )
        return
    
    await state.update_data(phone_number=phone_number)
    
    try:
        # Отправляем запрос на получение кода
        response = requests.post(
            f"{AUTH_SERVICE_URL}/auth/request_code",
            json={
                "phone_number": phone_number,
                "api_id": int(TELEGRAM_API_ID),
                "api_hash": TELEGRAM_API_HASH,
                "admin_chat_id": str(message.chat.id)
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            await message.answer(
                f"✅ Код отправлен на номер {phone_number}\n\n"
                "Введите код подтверждения, который пришел в Telegram:"
            )
            await state.set_state(AuthStates.waiting_for_code)
        else:
            error_msg = response.json().get('detail', 'Неизвестная ошибка')
            await message.answer(f"❌ Ошибка при отправке кода: {error_msg}")
            await state.clear()
            
    except Exception as e:
        await message.answer(f"❌ Ошибка при отправке кода: {str(e)}")
        await state.clear()

async def process_confirmation_code(message: types.Message, state: FSMContext):
    """Обработчик ввода кода подтверждения"""
    if not await has_admin_permissions(message.from_user.id, message.from_user.username):
        await message.answer("❌ У вас нет прав для доступа к этому разделу")
        await state.clear()
        return
    
    code = message.text.strip()
    data = await state.get_data()
    phone_number = data.get('phone_number')
    
    if not phone_number:
        await message.answer("❌ Ошибка: номер телефона не найден")
        await state.clear()
        return
    
    try:
        # Отправляем код для подтверждения
        response = requests.post(
            f"{AUTH_SERVICE_URL}/auth/confirm_code",
            json={
                "phone_number": phone_number,
                "code": code,
                "api_id": int(TELEGRAM_API_ID),
                "api_hash": TELEGRAM_API_HASH,
                "admin_chat_id": str(message.chat.id)
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            status = result.get('status')
            
            if status == 'confirmed':
                # Автоматически запускаем полное перераспределение каналов
                try:
                    distribute_response = requests.post(f"{AUTH_SERVICE_URL}/auth/redistribute_all_channels", timeout=30)
                    if distribute_response.status_code == 200:
                        # Ждем завершения перераспределения
                        task_id = distribute_response.json().get('task_id')
                        if task_id:
                            # Ждем до 60 секунд для завершения задачи
                            for _ in range(12):  # 12 * 5 секунд = 60 секунд
                                time.sleep(5)
                                try:
                                    task_status_response = requests.get(f"{AUTH_SERVICE_URL}/auth/task_status/{task_id}", timeout=10)
                                    if task_status_response.status_code == 200:
                                        task_result = task_status_response.json()
                                        if task_result.get('status') == 'SUCCESS':
                                            break
                                except:
                                    pass
                        
                        # Получаем обновленный статус после перераспределения
                        status_response = requests.get(f"{AUTH_SERVICE_URL}/auth/status", timeout=30)
                        if status_response.status_code == 200:
                            status_result = status_response.json()
                            total_accounts = status_result.get('total_accounts', 0)
                            total_channels = status_result.get('total_channels', 0)
                            available_slots = status_result.get('available_slots', 0)
                            
                            status_text = (
                                f"✅ Аккаунт {phone_number} успешно авторизован!\n\n"
                                f"🔄 Произведено полное перераспределение Telegram каналов\n\n"
                                f"📊 Статус после перераспределения:\n"
                                f"📱 Активных аккаунтов: {total_accounts}\n"
                                f"📺 Telegram каналов: {total_channels}\n"
                                f"🆓 Доступных слотов: {available_slots}\n\n"
                                f"Сессии:\n"
                            )
                            
                            sessions = status_result.get('sessions', [])
                            for i, session in enumerate(sessions, 1):
                                phone = session.get('phone_number', 'Unknown')
                                channels_count = len(session.get('channels', []))
                                status_text += f"{i}. {phone}: {channels_count} каналов\n"
                            
                            await message.answer(
                                status_text,
                                reply_markup=get_auth_menu_keyboard()
                            )
                        else:
                            await message.answer(
                                f"✅ Аккаунт {phone_number} успешно авторизован!\n\n"
                                "🔄 Произведено полное перераспределение Telegram каналов\n\n"
                                "⚠️ Не удалось получить детальный статус распределения.",
                                reply_markup=get_auth_menu_keyboard()
                            )
                    else:
                        await message.answer(
                            f"✅ Аккаунт {phone_number} успешно авторизован!\n\n"
                            "⚠️ Не удалось выполнить полное перераспределение Telegram каналов.",
                            reply_markup=get_auth_menu_keyboard()
                        )
                except Exception as e:
                    await message.answer(
                        f"✅ Аккаунт {phone_number} успешно авторизован!\n\n"
                        f"⚠️ Ошибка при полном перераспределении Telegram каналов: {str(e)}",
                        reply_markup=get_auth_menu_keyboard()
                    )
                
                await state.clear()
            elif status == 'awaiting_password':
                await message.answer(
                    f"🔐 Для аккаунта {phone_number} требуется пароль 2FA\n\n"
                    "Введите пароль от двухфакторной аутентификации:"
                )
                await state.set_state(AuthStates.waiting_for_password)
            elif status == 'restart_auth':
                await message.answer(
                    f"🔄 Требуется перезапуск авторизации для {phone_number}\n\n"
                    "Пожалуйста, начните процесс авторизации заново.",
                    reply_markup=get_auth_menu_keyboard()
                )
                await state.clear()
            elif status == 'invalid_code':
                await message.answer(
                    f"❌ Неверный код для {phone_number}\n\n"
                    "Пожалуйста, проверьте код и попробуйте снова.",
                    reply_markup=get_auth_menu_keyboard()
                )
                await state.clear()
            else:
                error_msg = result.get('error', 'Неизвестная ошибка')
                await message.answer(
                    f"❌ Ошибка при подтверждении кода: {error_msg}",
                    reply_markup=get_auth_menu_keyboard()
                )
                await state.clear()
        else:
            error_msg = response.json().get('detail', 'Неизвестная ошибка')
            await message.answer(
                f"❌ Ошибка при подтверждении кода: {error_msg}",
                reply_markup=get_auth_menu_keyboard()
            )
            await state.clear()
            
    except Exception as e:
        await message.answer(
            f"❌ Ошибка при подтверждении кода: {str(e)}",
            reply_markup=get_auth_menu_keyboard()
        )
        await state.clear()

async def process_password(message: types.Message, state: FSMContext):
    """Обработчик ввода пароля 2FA"""
    if not await has_admin_permissions(message.from_user.id, message.from_user.username):
        await message.answer("❌ У вас нет прав для доступа к этому разделу")
        await state.clear()
        return
    
    password = message.text.strip()
    data = await state.get_data()
    phone_number = data.get('phone_number')
    
    if not phone_number:
        await message.answer("❌ Ошибка: номер телефона не найден")
        await state.clear()
        return
    
    try:
        # Отправляем пароль для подтверждения
        response = requests.post(
            f"{AUTH_SERVICE_URL}/auth/confirm_password",
            json={
                "phone_number": phone_number,
                "password": password,
                "api_id": int(TELEGRAM_API_ID),
                "api_hash": TELEGRAM_API_HASH,
                "admin_chat_id": str(message.chat.id)
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            status = result.get('status')
            
            if status == 'confirmed':
                # Автоматически запускаем полное перераспределение каналов
                try:
                    distribute_response = requests.post(f"{AUTH_SERVICE_URL}/auth/redistribute_all_channels", timeout=30)
                    if distribute_response.status_code == 200:
                        # Ждем завершения перераспределения
                        task_id = distribute_response.json().get('task_id')
                        if task_id:
                            # Ждем до 60 секунд для завершения задачи
                            for _ in range(12):  # 12 * 5 секунд = 60 секунд
                                time.sleep(5)
                                try:
                                    task_status_response = requests.get(f"{AUTH_SERVICE_URL}/auth/task_status/{task_id}", timeout=10)
                                    if task_status_response.status_code == 200:
                                        task_result = task_status_response.json()
                                        if task_result.get('status') == 'SUCCESS':
                                            break
                                except:
                                    pass
                        
                        # Получаем обновленный статус после перераспределения
                        status_response = requests.get(f"{AUTH_SERVICE_URL}/auth/status", timeout=30)
                        if status_response.status_code == 200:
                            status_result = status_response.json()
                            total_accounts = status_result.get('total_accounts', 0)
                            total_channels = status_result.get('total_channels', 0)
                            available_slots = status_result.get('available_slots', 0)
                            
                            status_text = (
                                f"✅ Аккаунт {phone_number} успешно авторизован с 2FA!\n\n"
                                f"🔄 Произведено полное перераспределение Telegram каналов\n\n"
                                f"📊 Статус после перераспределения:\n"
                                f"📱 Активных аккаунтов: {total_accounts}\n"
                                f"📺 Telegram каналов: {total_channels}\n"
                                f"🆓 Доступных слотов: {available_slots}\n\n"
                                f"Сессии:\n"
                            )
                            
                            sessions = status_result.get('sessions', [])
                            for i, session in enumerate(sessions, 1):
                                phone = session.get('phone_number', 'Unknown')
                                channels_count = len(session.get('channels', []))
                                status_text += f"{i}. {phone}: {channels_count} каналов\n"
                            
                            await message.answer(
                                status_text,
                                reply_markup=get_auth_menu_keyboard()
                            )
                        else:
                            await message.answer(
                                f"✅ Аккаунт {phone_number} успешно авторизован с 2FA!\n\n"
                                "🔄 Произведено полное перераспределение Telegram каналов\n\n"
                                "⚠️ Не удалось получить детальный статус распределения.",
                                reply_markup=get_auth_menu_keyboard()
                            )
                    else:
                        await message.answer(
                            f"✅ Аккаунт {phone_number} успешно авторизован с 2FA!\n\n"
                            "⚠️ Не удалось выполнить полное перераспределение Telegram каналов.",
                            reply_markup=get_auth_menu_keyboard()
                        )
                except Exception as e:
                    await message.answer(
                        f"✅ Аккаунт {phone_number} успешно авторизован с 2FA!\n\n"
                        f"⚠️ Ошибка при полном перераспределении Telegram каналов: {str(e)}",
                        reply_markup=get_auth_menu_keyboard()
                    )
                
                await state.clear()
            else:
                error_msg = result.get('error', 'Неизвестная ошибка')
                await message.answer(
                    f"❌ Ошибка при подтверждении пароля: {error_msg}",
                    reply_markup=get_auth_menu_keyboard()
                )
                await state.clear()
        else:
            error_msg = response.json().get('detail', 'Неизвестная ошибка')
            await message.answer(
                f"❌ Ошибка при подтверждении пароля: {error_msg}",
                reply_markup=get_auth_menu_keyboard()
            )
            await state.clear()
            
    except Exception as e:
        await message.answer(
            f"❌ Ошибка при подтверждении пароля: {str(e)}",
            reply_markup=get_auth_menu_keyboard()
        )
        await state.clear()

async def check_auth_status_callback(callback_query: types.CallbackQuery):
    """Обработчик проверки статуса авторизации"""
    if not await has_admin_permissions(callback_query.from_user.id, callback_query.from_user.username):
        await callback_query.answer("❌ У вас нет прав для доступа к этому разделу")
        return
    
    try:
        response = requests.get(f"{AUTH_SERVICE_URL}/auth/status", timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            total_accounts = result.get('total_accounts', 0)
            total_channels = result.get('total_channels', 0)
            available_slots = result.get('available_slots', 0)
            
            status_text = (
                f"📊 Статус авторизации:\n\n"
                f"📱 Активных аккаунтов: {total_accounts}\n"
                f"📺 Telegram каналов: {total_channels}\n"
                f"🆓 Доступных слотов: {available_slots}\n\n"
                f"Сессии:\n"
            )
            
            sessions = result.get('sessions', [])
            for i, session in enumerate(sessions, 1):
                phone = session.get('phone_number', 'Unknown')
                channels_count = len(session.get('channels', []))
                status_text += f"{i}. {phone}: {channels_count} каналов\n"
            
            try:
                await callback_query.message.edit_text(
                    status_text,
                    reply_markup=get_auth_menu_keyboard()
                )
            except Exception as edit_error:
                # Если сообщение не изменилось, просто отвечаем на callback
                await callback_query.answer("Статус обновлен")
        else:
            await callback_query.message.edit_text(
                "❌ Ошибка при получении статуса авторизации",
                reply_markup=get_auth_menu_keyboard()
            )
            
    except Exception as e:
        await callback_query.message.edit_text(
            f"❌ Ошибка при получении статуса: {str(e)}",
            reply_markup=get_auth_menu_keyboard()
        )

async def distribute_channels_callback(callback_query: types.CallbackQuery):
    """Обработчик распределения каналов"""
    if not await has_admin_permissions(callback_query.from_user.id, callback_query.from_user.username):
        await callback_query.answer("❌ У вас нет прав для доступа к этому разделу")
        return
    
    try:
        # Сначала показываем, что процесс запущен
        await callback_query.message.edit_text(
            "🔄 Запускаем распределение каналов...",
            reply_markup=get_auth_service_menu_keyboard()
        )
        
        response = requests.post(f"{AUTH_SERVICE_URL}/auth/distribute_channels_from_db", timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            task_id = result.get('task_id')
            
            if task_id:
                # Ждем завершения распределения
                for _ in range(12):  # 12 * 5 секунд = 60 секунд
                    time.sleep(5)
                    try:
                        task_status_response = requests.get(f"{AUTH_SERVICE_URL}/auth/task_status/{task_id}", timeout=10)
                        if task_status_response.status_code == 200:
                            task_result = task_status_response.json()
                            if task_result.get('status') == 'SUCCESS':
                                break
                    except:
                        pass
            
            # Получаем обновленный статус после распределения
            status_response = requests.get(f"{AUTH_SERVICE_URL}/auth/status", timeout=30)
            if status_response.status_code == 200:
                status_result = status_response.json()
                total_accounts = status_result.get('total_accounts', 0)
                total_channels = status_result.get('total_channels', 0)
                available_slots = status_result.get('available_slots', 0)
                
                status_text = (
                    f"✅ Распределение каналов завершено!\n\n"
                    f"📊 Статус после распределения:\n"
                    f"📱 Активных аккаунтов: {total_accounts}\n"
                    f"📺 Telegram каналов: {total_channels}\n"
                    f"🆓 Доступных слотов: {available_slots}\n\n"
                    f"Сессии:\n"
                )
                
                sessions = status_result.get('sessions', [])
                for i, session in enumerate(sessions, 1):
                    phone = session.get('phone_number', 'Unknown')
                    channels_count = len(session.get('channels', []))
                    status_text += f"{i}. {phone}: {channels_count} каналов\n"
                
                await callback_query.message.edit_text(
                    status_text,
                    reply_markup=get_auth_service_menu_keyboard()
                )
            else:
                await callback_query.message.edit_text(
                    "✅ Распределение каналов завершено!\n\n"
                    "⚠️ Не удалось получить детальный статус распределения.",
                    reply_markup=get_auth_service_menu_keyboard()
                )
        else:
            error_msg = response.json().get('detail', 'Неизвестная ошибка')
            await callback_query.message.edit_text(
                f"❌ Ошибка при распределении каналов: {error_msg}",
                reply_markup=get_auth_service_menu_keyboard()
            )
            
    except Exception as e:
        await callback_query.message.edit_text(
            f"❌ Ошибка при распределении каналов: {str(e)}",
            reply_markup=get_auth_service_menu_keyboard()
        )

async def clean_duplicates_callback(callback_query: types.CallbackQuery):
    """Обработчик очистки дубликатов"""
    if not await has_admin_permissions(callback_query.from_user.id, callback_query.from_user.username):
        await callback_query.answer("❌ У вас нет прав для доступа к этому разделу")
        return
    
    try:
        # Сначала показываем, что процесс запущен
        await callback_query.message.edit_text(
            "🔄 Запускаем очистку дубликатов...",
            reply_markup=get_auth_service_menu_keyboard()
        )
        
        response = requests.post(f"{AUTH_SERVICE_URL}/auth/clean_duplicate_channels", timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            task_id = result.get('task_id')
            
            if task_id:
                # Ждем завершения очистки
                for _ in range(12):  # 12 * 5 секунд = 60 секунд
                    time.sleep(5)
                    try:
                        task_status_response = requests.get(f"{AUTH_SERVICE_URL}/auth/task_status/{task_id}", timeout=10)
                        if task_status_response.status_code == 200:
                            task_result = task_status_response.json()
                            if task_result.get('status') == 'SUCCESS':
                                break
                    except:
                        pass
            
            # Получаем результат очистки
            if task_id:
                try:
                    task_status_response = requests.get(f"{AUTH_SERVICE_URL}/auth/task_status/{task_id}", timeout=10)
                    if task_status_response.status_code == 200:
                        task_result = task_status_response.json()
                        if task_result.get('result'):
                            result_data = task_result.get('result', {})
                            removed_count = result_data.get('removed_count', 0)
                            total_duplicates = result_data.get('total_duplicates', 0)
                            
                            status_text = (
                                f"✅ Очистка дубликатов завершена!\n\n"
                                f"📊 Результаты очистки:\n"
                                f"🗑️ Удалено дубликатов: {removed_count}\n"
                                f"📋 Всего дубликатов найдено: {total_duplicates}\n\n"
                            )
                            
                            # Получаем обновленный статус
                            status_response = requests.get(f"{AUTH_SERVICE_URL}/auth/status", timeout=30)
                            if status_response.status_code == 200:
                                status_result = status_response.json()
                                total_accounts = status_result.get('total_accounts', 0)
                                total_channels = status_result.get('total_channels', 0)
                                
                                status_text += (
                                    f"📊 Текущий статус:\n"
                                    f"📱 Активных аккаунтов: {total_accounts}\n"
                                    f"📺 Telegram каналов: {total_channels}\n\n"
                                    f"Сессии:\n"
                                )
                                
                                sessions = status_result.get('sessions', [])
                                for i, session in enumerate(sessions, 1):
                                    phone = session.get('phone_number', 'Unknown')
                                    channels_count = len(session.get('channels', []))
                                    status_text += f"{i}. {phone}: {channels_count} каналов\n"
                                
                                await callback_query.message.edit_text(
                                    status_text,
                                    reply_markup=get_auth_service_menu_keyboard()
                                )
                            else:
                                await callback_query.message.edit_text(
                                    status_text + "⚠️ Не удалось получить детальный статус.",
                                    reply_markup=get_auth_service_menu_keyboard()
                                )
                        else:
                            await callback_query.message.edit_text(
                                "✅ Очистка дубликатов завершена!\n\n"
                                "⚠️ Не удалось получить детальную информацию о результатах.",
                                reply_markup=get_auth_service_menu_keyboard()
                            )
                    else:
                        await callback_query.message.edit_text(
                            "✅ Очистка дубликатов завершена!\n\n"
                            "⚠️ Не удалось получить детальную информацию о результатах.",
                            reply_markup=get_auth_service_menu_keyboard()
                        )
                except:
                    await callback_query.message.edit_text(
                        "✅ Очистка дубликатов завершена!\n\n"
                        "⚠️ Не удалось получить детальную информацию о результатах.",
                        reply_markup=get_auth_service_menu_keyboard()
                    )
            else:
                await callback_query.message.edit_text(
                    "✅ Очистка дубликатов завершена!",
                    reply_markup=get_auth_service_menu_keyboard()
                )
        else:
            error_msg = response.json().get('detail', 'Неизвестная ошибка')
            await callback_query.message.edit_text(
                f"❌ Ошибка при очистке дубликатов: {error_msg}",
                reply_markup=get_auth_service_menu_keyboard()
            )
            
    except Exception as e:
        await callback_query.message.edit_text(
            f"❌ Ошибка при очистке дубликатов: {str(e)}",
            reply_markup=get_auth_service_menu_keyboard()
        )

async def clear_all_channels_callback(callback_query: types.CallbackQuery):
    """Обработчик очистки всех каналов"""
    if not await has_admin_permissions(callback_query.from_user.id, callback_query.from_user.username):
        await callback_query.answer("❌ У вас нет прав для доступа к этому разделу")
        return
    
    try:
        # Сначала показываем, что процесс запущен
        await callback_query.message.edit_text(
            "🔄 Запускаем очистку всех каналов...",
            reply_markup=get_auth_service_menu_keyboard()
        )
        
        response = requests.post(f"{AUTH_SERVICE_URL}/auth/clear_all_channels", timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            task_id = result.get('task_id')
            
            if task_id:
                # Ждем завершения очистки
                for _ in range(12):  # 12 * 5 секунд = 60 секунд
                    time.sleep(5)
                    try:
                        task_status_response = requests.get(f"{AUTH_SERVICE_URL}/auth/task_status/{task_id}", timeout=10)
                        if task_status_response.status_code == 200:
                            task_result = task_status_response.json()
                            if task_result.get('status') == 'SUCCESS':
                                break
                    except:
                        pass
            
            # Получаем обновленный статус после очистки
            status_response = requests.get(f"{AUTH_SERVICE_URL}/auth/status", timeout=30)
            if status_response.status_code == 200:
                status_result = status_response.json()
                total_accounts = status_result.get('total_accounts', 0)
                total_channels = status_result.get('total_channels', 0)
                available_slots = status_result.get('available_slots', 0)
                
                status_text = (
                    f"✅ Очистка всех каналов завершена!\n\n"
                    f"📊 Статус после очистки:\n"
                    f"📱 Активных аккаунтов: {total_accounts}\n"
                    f"📺 Telegram каналов: {total_channels}\n"
                    f"🆓 Доступных слотов: {available_slots}\n\n"
                    f"Сессии:\n"
                )
                
                sessions = status_result.get('sessions', [])
                for i, session in enumerate(sessions, 1):
                    phone = session.get('phone_number', 'Unknown')
                    channels_count = len(session.get('channels', []))
                    status_text += f"{i}. {phone}: {channels_count} каналов\n"
                
                await callback_query.message.edit_text(
                    status_text,
                    reply_markup=get_auth_service_menu_keyboard()
                )
            else:
                await callback_query.message.edit_text(
                    "✅ Очистка всех каналов завершена!\n\n"
                    "⚠️ Не удалось получить детальный статус.",
                    reply_markup=get_auth_service_menu_keyboard()
                )
        else:
            error_msg = response.json().get('detail', 'Неизвестная ошибка')
            await callback_query.message.edit_text(
                f"❌ Ошибка при очистке каналов: {error_msg}",
                reply_markup=get_auth_service_menu_keyboard()
            )
            
    except Exception as e:
        await callback_query.message.edit_text(
            f"❌ Ошибка при очистке каналов: {str(e)}",
            reply_markup=get_auth_service_menu_keyboard()
        )

async def delete_account_callback(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик удаления аккаунта"""
    if not await has_admin_permissions(callback_query.from_user.id, callback_query.from_user.username):
        await callback_query.answer("❌ У вас нет прав для доступа к этому разделу")
        return
    
    await callback_query.message.edit_text(
        "🗑️ Удаление Telegram аккаунта\n\n"
        "Введите номер телефона аккаунта для удаления:\n"
        "+7XXXXXXXXXX\n\n"
        "Например: +79091234567\n\n"
        "⚠️ Внимание: Это действие удалит сессию и все связанные с ней данные!",
        reply_markup=get_main_menu_back_keyboard()
    )
    await state.set_state(AuthStates.waiting_for_delete_phone)

async def process_delete_phone_number(message: types.Message, state: FSMContext):
    """Обработчик ввода номера телефона для удаления"""
    if not await has_admin_permissions(message.from_user.id, message.from_user.username):
        await message.answer("❌ У вас нет прав для доступа к этому разделу")
        await state.clear()
        return

    phone_number = message.text.strip()
    
    # Проверяем формат номера
    if not phone_number.startswith('+') or len(phone_number) < 10:
        await message.answer(
            "❌ Неверный формат номера телефона!\n\n"
            "Введите номер в формате: +7XXXXXXXXXX\n"
            "Например: +79091234567"
        )
        return
    
    try:
        # Отправляем запрос на удаление аккаунта
        response = requests.delete(
            f"{AUTH_SERVICE_URL}/auth/delete_session",
            json={
                "phone_number": phone_number,
                "admin_chat_id": str(message.chat.id)
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # Ждем завершения удаления и перераспределения
            task_id = result.get('task_id')
            if task_id:
                # Ждем до 60 секунд для завершения задачи
                for _ in range(12):  # 12 * 5 секунд = 60 секунд
                    time.sleep(5)
                    try:
                        task_status_response = requests.get(f"{AUTH_SERVICE_URL}/auth/task_status/{task_id}", timeout=10)
                        if task_status_response.status_code == 200:
                            task_result = task_status_response.json()
                            if task_result.get('status') == 'SUCCESS':
                                break
                    except:
                        pass
            
            # Получаем обновленный статус после удаления и перераспределения
            try:
                status_response = requests.get(f"{AUTH_SERVICE_URL}/auth/status", timeout=30)
                if status_response.status_code == 200:
                    status_result = status_response.json()
                    total_accounts = status_result.get('total_accounts', 0)
                    total_channels = status_result.get('total_channels', 0)
                    available_slots = status_result.get('available_slots', 0)
                    
                    if total_accounts > 0:
                        status_text = (
                            f"✅ Аккаунт {phone_number} успешно удален!\n\n"
                            f"🔄 Произведено автоматическое перераспределение Telegram каналов\n\n"
                            f"📊 Статус после перераспределения:\n"
                            f"📱 Активных аккаунтов: {total_accounts}\n"
                            f"📺 Telegram каналов: {total_channels}\n"
                            f"🆓 Доступных слотов: {available_slots}\n\n"
                            f"Сессии:\n"
                        )
                        
                        sessions = status_result.get('sessions', [])
                        for i, session in enumerate(sessions, 1):
                            phone = session.get('phone_number', 'Unknown')
                            channels_count = len(session.get('channels', []))
                            status_text += f"{i}. {phone}: {channels_count} каналов\n"
                        
                        await message.answer(
                            status_text,
                            reply_markup=get_auth_menu_keyboard()
                        )
                    else:
                        await message.answer(
                            f"✅ Аккаунт {phone_number} успешно удален!\n\n"
                            "⚠️ Нет активных сессий для перераспределения каналов.\n"
                            "Привязки каналов сброшены.\n"
                            "Каналы будут перераспределены при добавлении новой сессии.",
                            reply_markup=get_auth_menu_keyboard()
                        )
                else:
                    await message.answer(
                        f"✅ Аккаунт {phone_number} успешно удален!\n\n"
                        "🔄 Произведено автоматическое перераспределение Telegram каналов\n\n"
                        "⚠️ Не удалось получить детальный статус распределения.",
                        reply_markup=get_auth_menu_keyboard()
                    )
            except Exception as e:
                await message.answer(
                    f"✅ Аккаунт {phone_number} успешно удален!\n\n"
                    f"🔄 Произведено автоматическое перераспределение Telegram каналов\n\n"
                    f"⚠️ Ошибка при получении статуса: {str(e)}",
                    reply_markup=get_auth_menu_keyboard()
                )
        else:
            error_msg = response.json().get('detail', 'Неизвестная ошибка')
            await message.answer(
                f"❌ Ошибка при удалении аккаунта: {error_msg}",
                reply_markup=get_auth_menu_keyboard()
            )
    except requests.exceptions.RequestException as e:
        await message.answer(
            f"❌ Ошибка соединения с сервисом авторизации: {str(e)}",
            reply_markup=get_auth_menu_keyboard()
        )
    except Exception as e:
        await message.answer(
            f"❌ Неожиданная ошибка: {str(e)}",
            reply_markup=get_auth_menu_keyboard()
        )
    
    await state.clear()

def register_handlers(dp: Dispatcher):
    """Регистрация всех хендлеров для авторизации"""
    # Меню авторизации
    dp.callback_query.register(auth_menu_callback, lambda c: c.data == "auth_menu")
    dp.callback_query.register(auth_service_menu_callback, lambda c: c.data == "auth_service_menu")
    
    # Добавление нового аккаунта
    dp.callback_query.register(add_new_account_callback, lambda c: c.data == "add_new_account")
    dp.message.register(process_phone_number, AuthStates.waiting_for_phone)
    dp.message.register(process_confirmation_code, AuthStates.waiting_for_code)
    dp.message.register(process_password, AuthStates.waiting_for_password)
    dp.callback_query.register(delete_account_callback, lambda c: c.data == "delete_account")
    dp.message.register(process_delete_phone_number, AuthStates.waiting_for_delete_phone)
    
    # Проверка статуса
    dp.callback_query.register(check_auth_status_callback, lambda c: c.data == "check_auth_status")
    
    # Управление сервисом авторизации
    dp.callback_query.register(distribute_channels_callback, lambda c: c.data == "distribute_channels")
    dp.callback_query.register(clean_duplicates_callback, lambda c: c.data == "clean_duplicates")
    dp.callback_query.register(clear_all_channels_callback, lambda c: c.data == "clear_all_channels") 