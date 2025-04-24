from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Main menu keyboards
def get_role_keyboard():
    """Keyboard for selecting user role"""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="🚖 Водитель", callback_data="register_driver"),
        InlineKeyboardButton(text="🧑‍💼 Пассажир", callback_data="register_passenger")
    )
    return builder.as_markup()

def get_passenger_menu():
    """Main menu for passengers"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🚕 Заказать такси", callback_data="order_taxi"))
    builder.row(InlineKeyboardButton(text="🔍 Активный заказ", callback_data="active_order"))
    builder.row(InlineKeyboardButton(text="📜 История поездок", callback_data="order_history"))
    builder.row(InlineKeyboardButton(text="⭐ Мой рейтинг", callback_data="my_rating"))
    builder.row(InlineKeyboardButton(text="ℹ️ Помощь", callback_data="help"))
    return builder.as_markup()

def get_driver_menu():
    """Main menu for drivers"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="👀 Смотреть заказы", callback_data="view_orders"))
    builder.row(InlineKeyboardButton(text="🚗 Изменить статус", callback_data="change_status"))
    builder.row(InlineKeyboardButton(text="📊 Моя статистика", callback_data="my_stats"))
    builder.row(InlineKeyboardButton(text="💰 Мой заработок", callback_data="my_earnings"))
    builder.row(InlineKeyboardButton(text="📜 История поездок", callback_data="order_history"))
    builder.row(InlineKeyboardButton(text="ℹ️ Помощь", callback_data="help"))
    return builder.as_markup()

def get_back_to_menu():
    """Back to menu button"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="◀️ Назад в меню", callback_data="back_to_menu"))
    return builder.as_markup()

# Order-related keyboards
def get_ride_class_keyboard():
    """Keyboard for selecting ride class"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🚗 Эконом", callback_data="class_economy"))
    builder.row(InlineKeyboardButton(text="🚙 Комфорт", callback_data="class_comfort"))
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu"))
    return builder.as_markup()

def get_confirm_order_keyboard():
    """Keyboard for confirming an order"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_order"))
    builder.row(InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_order"))
    return builder.as_markup()

def get_driver_order_actions(order_id):
    """Keyboard for driver actions on an order"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="✅ Принять заказ", 
        callback_data=f"accept_order_{order_id}"
    ))
    builder.row(InlineKeyboardButton(
        text="❌ Отклонить заказ", 
        callback_data=f"decline_order_{order_id}"
    ))
    builder.row(InlineKeyboardButton(
        text="◀️ Назад", 
        callback_data="back_to_menu"
    ))
    return builder.as_markup()

def get_active_order_keyboard(role, status):
    """Keyboard for active order actions"""
    builder = InlineKeyboardBuilder()
    
    if role == 'passenger':
        builder.row(InlineKeyboardButton(text="❌ Отменить заказ", callback_data="cancel_active_order"))
        if status == 'completed':
            builder.row(InlineKeyboardButton(text="⭐ Оценить поездку", callback_data="rate_driver"))
    
    elif role == 'driver':
        if status == 'accepted':
            builder.row(InlineKeyboardButton(text="🚗 Выехал", callback_data="driver_started"))
            builder.row(InlineKeyboardButton(text="🏁 Прибыл", callback_data="driver_arrived"))
        elif status == 'driver_started':
            builder.row(InlineKeyboardButton(text="🏁 Прибыл", callback_data="driver_arrived"))
        elif status == 'driver_arrived':
            builder.row(InlineKeyboardButton(text="🏁 Завершить поездку", callback_data="complete_order"))
        elif status == 'completed':
            builder.row(InlineKeyboardButton(text="⭐ Оценить пассажира", callback_data="rate_passenger"))
    
    builder.row(InlineKeyboardButton(text="◀️ Назад в меню", callback_data="back_to_menu"))
    return builder.as_markup()

def get_driver_status_keyboard(current_status):
    """Keyboard for changing driver status"""
    builder = InlineKeyboardBuilder()
    
    if current_status == 'available':
        builder.row(InlineKeyboardButton(text="🔴 Перейти в статус 'Занят'", callback_data="status_busy"))
    else:
        builder.row(InlineKeyboardButton(text="🟢 Перейти в статус 'Свободен'", callback_data="status_available"))
    
    builder.row(InlineKeyboardButton(text="◀️ Назад в меню", callback_data="back_to_menu"))
    return builder.as_markup()

def get_rating_keyboard():
    """Keyboard for rating"""
    builder = InlineKeyboardBuilder()
    for i in range(1, 6):
        builder.add(InlineKeyboardButton(text=f"{i} ⭐", callback_data=f"rate_{i}"))
    return builder.as_markup()

def get_earnings_period_keyboard():
    """Keyboard for selecting earnings period"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Сегодня", callback_data="earnings_today"))
    builder.row(InlineKeyboardButton(text="За неделю", callback_data="earnings_week"))
    builder.row(InlineKeyboardButton(text="За месяц", callback_data="earnings_month"))
    builder.row(InlineKeyboardButton(text="За все время", callback_data="earnings_all"))
    builder.row(InlineKeyboardButton(text="◀️ Назад в меню", callback_data="back_to_menu"))
    return builder.as_markup()

def get_history_keyboard():
    """Keyboard for order history"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="◀️ Назад в меню", callback_data="back_to_menu"))
    return builder.as_markup()