from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

import keyboards as kb
from db import Database
from config import MESSAGES
from common import format_order_info

# Initialize router and database
router = Router()
db = Database()

# States for driver actions
class DriverStates(StatesGroup):
    waiting_for_rating = State()

@router.callback_query(F.data == "view_orders")
async def view_orders(callback: CallbackQuery):
    """Handler for viewing available orders"""
    await callback.answer()
    
    # Check if driver is available
    driver = await db.get_driver(callback.from_user.id)
    
    if not driver or driver['status'] != 'available':
        await callback.message.answer(
            "Вы должны быть в статусе 'Свободен', чтобы видеть доступные заказы.",
            reply_markup=kb.get_back_to_menu()
        )
        return
    
    # Get pending orders
    orders = await db.get_pending_orders()
    
    if not orders:
        await callback.message.answer(
            "В данный момент нет доступных заказов. Попробуйте позже.",
            reply_markup=kb.get_back_to_menu()
        )
        return
    
    # Show orders one by one
    for order in orders:
        # Format order message
        human_class = "Комфорт" if order['ride_class'] == 'comfort' else "Эконом"
        
        order_text = (
            f"<b>Заказ #{order['order_id']}</b>\n\n"
            f"<b>От:</b> {order['from_address']}\n"
            f"<b>До:</b> {order['to_address']}\n"
            f"<b>Класс:</b> {human_class}\n"
            f"<b>Расстояние:</b> {order['distance']} км\n"
            f"<b>Стоимость:</b> {order['estimated_cost']} руб.\n"
            f"<b>Пассажир:</b> {order['full_name']}\n"
            f"<b>Рейтинг пассажира:</b> {'⭐' * int(order['rating'])}\n"
        )
        
        # Create keyboard for this specific order
        markup = kb.get_driver_order_actions(order['order_id'])
        
        await callback.message.answer(
            order_text,
            reply_markup=markup,
            parse_mode="HTML"
        )
        
    # Add a back button at the end
    await callback.message.answer(
        "Выберите заказ или вернитесь в меню:",
        reply_markup=kb.get_back_to_menu()
    )

@router.callback_query(F.data.startswith("accept_order_"))
async def accept_order(callback: CallbackQuery):
    """Handler for accepting an order"""
    await callback.answer()
    
    # Extract order_id from callback data
    order_id = int(callback.data.split("_")[2])
    
    # Get order details
    order = await db.get_order(order_id)
    
    if not order:
        await callback.message.answer(
            "Заказ не найден или устарел.",
            reply_markup=kb.get_back_to_menu()
        )
        return
    
    # Check if order is still pending
    if order['status'] != 'pending':
        await callback.message.answer(
            MESSAGES["order_already_accepted"],
            reply_markup=kb.get_back_to_menu()
        )
        return
    
    # Accept the order
    await db.accept_order(order_id, callback.from_user.id)
    
    # Notify driver
    await callback.message.answer(
        f"Вы приняли заказ #{order_id}! Пожалуйста, направляйтесь к точке посадки:\n{order['from_address']}",
        reply_markup=kb.get_active_order_keyboard('driver', 'accepted')
    )

@router.callback_query(F.data.startswith("decline_order_"))
async def decline_order(callback: CallbackQuery):
    """Handler for declining an order"""
    await callback.answer()
    
    # Here we just ignore the order, not actually declining it in the database
    # In a real app, you might want to mark it as declined by this driver
    await callback.message.answer(
        "Вы отклонили заказ.",
        reply_markup=kb.get_back_to_menu()
    )

@router.callback_query(F.data == "change_status")
async def change_status_menu(callback: CallbackQuery):
    """Handler for showing status change menu"""
    await callback.answer()
    
    # Get current driver status
    driver = await db.get_driver(callback.from_user.id)
    
    if not driver:
        await callback.message.answer(
            "Ошибка: информация о водителе не найдена.",
            reply_markup=kb.get_back_to_menu()
        )
        return
    
    current_status = driver['status']
    status_text = "Свободен" if current_status == 'available' else "Занят"
    status_emoji = "🟢" if current_status == 'available' else "🔴"
    
    await callback.message.answer(
        f"Ваш текущий статус: {status_emoji} {status_text}\n\nВыберите действие:",
        reply_markup=kb.get_driver_status_keyboard(current_status)
    )

@router.callback_query(F.data.startswith("status_"))
async def update_status(callback: CallbackQuery):
    """Handler for updating driver status"""
    await callback.answer()
    
    # Extract status from callback data
    new_status = callback.data.split("_")[1]  # available or busy
    
    # Check if driver has active orders
    if new_status == 'available':
        active_order = await db.get_active_order(callback.from_user.id, 'driver')
        if active_order and active_order['status'] not in ['completed', 'cancelled']:
            await callback.message.answer(
                "Невозможно изменить статус на 'Свободен', пока у вас есть активный заказ.",
                reply_markup=kb.get_back_to_menu()
            )
            return
    
    # Update status
    await db.update_driver_status(callback.from_user.id, new_status)
    
    # Notify driver
    status_text = "Свободен" if new_status == 'available' else "Занят"
    await callback.message.answer(
        MESSAGES["status_changed"].format(status=status_text),
        reply_markup=kb.get_back_to_menu()
    )

@router.callback_query(F.data == "driver_started")
async def driver_started(callback: CallbackQuery):
    """Handler for when driver starts moving to pickup point"""
    await callback.answer()
    
    # Get active order
    active_order = await db.get_active_order(callback.from_user.id, 'driver')
    
    if not active_order or active_order['status'] != 'accepted':
        await callback.message.answer(
            "Нет активного заказа в подходящем статусе.",
            reply_markup=kb.get_back_to_menu()
        )
        return
    
    # Update order status
    await db.execute(
        "UPDATE orders SET status = 'driver_started' WHERE order_id = ?",
        (active_order['order_id'],)
    )
    
    await callback.message.answer(
        "Статус обновлен: Вы выехали к клиенту.",
        reply_markup=kb.get_active_order_keyboard('driver', 'driver_started')
    )

@router.callback_query(F.data == "driver_arrived")
async def driver_arrived(callback: CallbackQuery):
    """Handler for when driver arrives at pickup point"""
    await callback.answer()
    
    # Get active order
    active_order = await db.get_active_order(callback.from_user.id, 'driver')
    
    if not active_order or active_order['status'] not in ['accepted', 'driver_started']:
        await callback.message.answer(
            "Нет активного заказа в подходящем статусе.",
            reply_markup=kb.get_back_to_menu()
        )
        return
    
    # Update order status
    await db.execute(
        "UPDATE orders SET status = 'driver_arrived' WHERE order_id = ?",
        (active_order['order_id'],)
    )
    
    await callback.message.answer(
        "Статус обновлен: Вы прибыли на место посадки.",
        reply_markup=kb.get_active_order_keyboard('driver', 'driver_arrived')
    )

@router.callback_query(F.data == "complete_order")
async def complete_ride(callback: CallbackQuery):
    """Handler for completing a ride"""
    await callback.answer()
    
    # Get active order
    active_order = await db.get_active_order(callback.from_user.id, 'driver')
    
    if not active_order or active_order['status'] != 'driver_arrived':
        await callback.message.answer(
            "Нет активного заказа в подходящем статусе.",
            reply_markup=kb.get_back_to_menu()
        )
        return
    
    # Complete the order
    success = await db.complete_order(active_order['order_id'])
    
    if success:
        await callback.message.answer(
            "Поездка успешно завершена! Теперь вы можете оценить пассажира.",
            reply_markup=kb.get_active_order_keyboard('driver', 'completed')
        )
    else:
        await callback.message.answer(
            "Произошла ошибка при завершении поездки. Попробуйте снова.",
            reply_markup=kb.get_back_to_menu()
        )

@router.callback_query(F.data == "rate_passenger")
async def show_passenger_rating(callback: CallbackQuery, state: FSMContext):
    """Show rating interface for passenger"""
    await callback.answer()
    
    # Get completed order
    active_order = await db.get_active_order(callback.from_user.id, 'driver')
    
    if not active_order or active_order['status'] != 'completed':
        await callback.message.answer(
            "Нет завершенных поездок для оценки.",
            reply_markup=kb.get_back_to_menu()
        )
        return
    
    # Save order_id and passenger_id to state
    await state.update_data(
        order_id=active_order['order_id'],
        passenger_id=active_order['passenger_id']
    )
    
    # Show rating keyboard
    await callback.message.answer(
        MESSAGES["rate_passenger"],
        reply_markup=kb.get_rating_keyboard()
    )
    
    await state.set_state(DriverStates.waiting_for_rating)

@router.callback_query(StateFilter(DriverStates.waiting_for_rating), F.data.startswith("rate_"))
async def process_passenger_rating(callback: CallbackQuery, state: FSMContext):
    """Process passenger rating"""
    await callback.answer()
    
    # Extract rating from callback data (format: rate_X)
    rating = int(callback.data.split("_")[1])
    
    # Get order info from state
    data = await state.get_data()
    order_id = data['order_id']
    passenger_id = data['passenger_id']
    
    # Save rating
    await db.add_rating(
        order_id=order_id,
        from_user_id=callback.from_user.id,
        to_user_id=passenger_id,
        rating=rating
    )
    
    # Thank driver
    await callback.message.answer(
        f"Спасибо за вашу оценку! Вы поставили пассажиру {rating} {'звезд' if rating > 1 else 'звезду'}.",
        reply_markup=kb.get_back_to_menu()
    )
    
    # Clear state
    await state.clear()

@router.callback_query(F.data == "my_stats")
async def show_stats(callback: CallbackQuery):
    """Show driver statistics"""
    await callback.answer()
    
    # Get driver data
    driver = await db.get_driver(callback.from_user.id)
    user = await db.get_user(callback.from_user.id)
    
    if not driver or not user:
        await callback.message.answer(
            "Ошибка: информация о водителе не найдена.",
            reply_markup=kb.get_back_to_menu()
        )
        return
    
    # Get stats
    completed_orders = await db.get_completed_orders_count(callback.from_user.id, 'driver')
    total_earnings = driver['total_earnings']
    rating = user['rating']
    
    # Format stats
    stats_text = (
        f"<b>Ваша статистика:</b>\n\n"
        f"<b>Выполнено заказов:</b> {completed_orders}\n"
        f"<b>Общий заработок:</b> {total_earnings} руб.\n"
        f"<b>Рейтинг:</b> {rating:.1f} {'⭐' * int(rating)}\n"
        f"<b>Статус:</b> {'🟢 Свободен' if driver['status'] == 'available' else '🔴 Занят'}\n"
    )
    
    await callback.message.answer(
        stats_text,
        reply_markup=kb.get_back_to_menu(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "my_earnings")
async def show_earnings_menu(callback: CallbackQuery):
    """Show earnings menu"""
    await callback.answer()
    
    await callback.message.answer(
        "Выберите период для просмотра заработка:",
        reply_markup=kb.get_earnings_period_keyboard()
    )

@router.callback_query(F.data.startswith("earnings_"))
async def show_earnings(callback: CallbackQuery):
    """Show earnings for selected period"""
    await callback.answer()
    
    # Extract period from callback data
    period = callback.data.split("_")[1]  # today, week, month, all
    
    # Get earnings for period
    if period == 'all':
        driver = await db.get_driver(callback.from_user.id)
        earnings = driver['total_earnings'] if driver else 0
    else:
        earnings = await db.get_driver_earnings(callback.from_user.id, period)
    
    # Format period text
    period_text = {
        'today': 'сегодня',
        'week': 'за неделю',
        'month': 'за месяц',
        'all': 'за все время'
    }.get(period, period)
    
    await callback.message.answer(
        f"Ваш заработок {period_text}: {earnings} руб.",
        reply_markup=kb.get_back_to_menu()
    )

@router.callback_query(F.data == "order_history")
async def show_order_history(callback: CallbackQuery):
    """Show order history for driver"""
    await callback.answer()
    
    # Get order history
    orders = await db.get_order_history(callback.from_user.id, 'driver')
    
    if not orders:
        await callback.message.answer(
            MESSAGES["no_history"],
            reply_markup=kb.get_back_to_menu()
        )
        return
    
    # Format and show orders
    response = "<b>История ваших поездок:</b>\n\n"
    
    for i, order in enumerate(orders, 1):
        status_emoji = {
            'completed': '✅',
            'cancelled': '❌',
            'pending': '⏳',
            'accepted': '🚗',
            'in_progress': '🚕'
        }.get(order['status'], '')
        
        response += (
            f"{i}. {status_emoji} <b>Заказ #{order['order_id']}</b>\n"
            f"   {order['from_address']} → {order['to_address']}\n"
            f"   Класс: {'Комфорт' if order['ride_class'] == 'comfort' else 'Эконом'}\n"
            f"   Стоимость: {order['actual_cost'] or order['estimated_cost']} руб.\n"
            f"   Дата: {order['created_at'][:10]}\n\n"
        )
    
    await callback.message.answer(
        response,
        reply_markup=kb.get_history_keyboard(),
        parse_mode="HTML"
    )