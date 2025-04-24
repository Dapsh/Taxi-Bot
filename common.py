from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State, default_state

import keyboards as kb
from db import Database
from config import MESSAGES

# Initialize router and database
router = Router()
db = Database()

# States
class CommonStates(StatesGroup):
    waiting_for_help_query = State()

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Handler for the /start command"""
    # Reset any active state
    await state.clear()
    
    # Check if user is already registered
    user = await db.get_user(message.from_user.id)
    
    if user:
        # User exists, show appropriate menu
        if user['role'] == 'driver':
            await message.answer(MESSAGES["main_menu"], reply_markup=kb.get_driver_menu())
        else:
            await message.answer(MESSAGES["main_menu"], reply_markup=kb.get_passenger_menu())
    else:
        # New user, show role selection
        await message.answer(MESSAGES["welcome"], reply_markup=kb.get_role_keyboard())

@router.callback_query(F.data == "help")
async def help_menu(callback: CallbackQuery, state: FSMContext):
    """Handler for help menu"""
    await callback.answer()
    
    help_text = (
        "📋 <b>Помощь по использованию бота Fifty Drive</b>\n\n"
        "<b>Основные команды:</b>\n"
        "/start - перезапустить бота\n"
        "/help - показать это сообщение\n\n"
        
        "<b>Для пассажиров:</b>\n"
        "• Чтобы заказать такси, выберите 'Заказать такси' в главном меню\n"
        "• Следуйте инструкциям для указания адресов и выбора класса поездки\n"
        "• После заказа вы можете отслеживать статус через 'Активный заказ'\n"
        "• История поездок доступна в соответствующем разделе\n\n"
        
        "<b>Для водителей:</b>\n"
        "• Используйте 'Смотреть заказы' чтобы видеть доступные заказы\n"
        "• Вы можете изменить свой статус через меню 'Изменить статус'\n"
        "• Статистика и заработок доступны в соответствующих разделах\n\n"
        
        "Если у вас возникли вопросы, напишите их ниже:"
    )
    
    await callback.message.answer(help_text, parse_mode="HTML")
    await state.set_state(CommonStates.waiting_for_help_query)

@router.message(StateFilter(CommonStates.waiting_for_help_query))
async def process_help_query(message: Message, state: FSMContext):
    """Process help query from user"""
    # In a real bot, this could forward the message to support or provide specific help
    await message.answer(
        "Спасибо за ваш вопрос! Наша команда поддержки скоро свяжется с вами.",
        reply_markup=kb.get_back_to_menu()
    )
    await state.clear()

@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery, state: FSMContext):
    """Handler to return to the main menu"""
    await callback.answer()
    
    # Clear any active state
    await state.clear()
    
    # Check user role
    user = await db.get_user(callback.from_user.id)
    
    if user['role'] == 'driver':
        await callback.message.answer(MESSAGES["main_menu"], reply_markup=kb.get_driver_menu())
    else:
        await callback.message.answer(MESSAGES["main_menu"], reply_markup=kb.get_passenger_menu())

@router.callback_query(F.data == "my_rating")
async def show_rating(callback: CallbackQuery):
    """Show user's current rating"""
    await callback.answer()
    
    user = await db.get_user(callback.from_user.id)
    rating = user['rating']
    
    # Format rating with stars
    stars = "⭐" * int(rating) + ("✨" if rating % 1 >= 0.5 else "")
    
    await callback.message.answer(
        f"Ваш текущий рейтинг: {rating:.1f} {stars}",
        reply_markup=kb.get_back_to_menu()
    )

# Helper function to format order for display
async def format_order_info(order, include_user_info=False):
    """Format order information for display"""
    if not order:
        return "Информация о заказе недоступна."
    
    status_emoji = {
        'pending': '⏳',
        'accepted': '✅',
        'driver_started': '🚗',
        'driver_arrived': '🏁',
        'in_progress': '🚕',
        'completed': '🏆',
        'cancelled': '❌'
    }
    
    status_text = {
        'pending': 'Ожидает водителя',
        'accepted': 'Водитель принял заказ',
        'driver_started': 'Водитель в пути',
        'driver_arrived': 'Водитель прибыл',
        'in_progress': 'Поездка в процессе',
        'completed': 'Завершен',
        'cancelled': 'Отменен'
    }
    
    # Basic order info
    result = (
        f"<b>Заказ #{order['order_id']}</b>\n"
        f"<b>Статус:</b> {status_emoji.get(order['status'], '')} {status_text.get(order['status'], order['status'])}\n"
        f"<b>От:</b> {order['from_address']}\n"
        f"<b>До:</b> {order['to_address']}\n"
        f"<b>Класс:</b> {'Комфорт' if order['ride_class'] == 'comfort' else 'Эконом'}\n"
        f"<b>Расстояние:</b> {order['distance']} км\n"
        f"<b>Стоимость:</b> {order['actual_cost'] or order['estimated_cost']} руб.\n"
    )
    
    # Add timestamps if available
    if order['created_at']:
        result += f"<b>Создан:</b> {order['created_at'][:16].replace('T', ' ')}\n"
    
    if order['started_at']:
        result += f"<b>Начат:</b> {order['started_at'][:16].replace('T', ' ')}\n"
        
    if order['completed_at']:
        result += f"<b>Завершен:</b> {order['completed_at'][:16].replace('T', ' ')}\n"
    
    # Add rating info if available
    if order['passenger_rating']:
        result += f"<b>Оценка пассажира:</b> {'⭐' * order['passenger_rating']}\n"
        
    if order['driver_rating']:
        result += f"<b>Оценка водителя:</b> {'⭐' * order['driver_rating']}\n"
    
    # Add user info if requested and available
    if include_user_info:
        # In a real bot, you would fetch and include user info here
        pass
        
    return result