from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

import keyboards as kb
from db import Database
from geo import GeoService
from config import MESSAGES, RIDE_CLASSES
from common import format_order_info

# Initialize router, database, and geo service
router = Router()
db = Database()
geo_service = GeoService()

# States for passenger actions
class PassengerStates(StatesGroup):
    waiting_for_from_address = State()
    waiting_for_to_address = State()
    waiting_for_class = State()
    waiting_for_order_confirmation = State()
    waiting_for_rating = State()

@router.callback_query(F.data == "order_taxi")
async def order_taxi(callback: CallbackQuery, state: FSMContext):
    """Handler for ordering a taxi"""
    await callback.answer()
    
    # Check if user already has an active order
    active_order = await db.get_active_order(callback.from_user.id, 'passenger')
    
    if active_order:
        # User already has an active order
        await callback.message.answer(
            "У вас уже есть активный заказ. Пожалуйста, завершите или отмените его перед созданием нового.",
            reply_markup=kb.get_back_to_menu()
        )
        return
    
    # Ask for starting address
    await callback.message.answer(MESSAGES["order_from"])
    await state.set_state(PassengerStates.waiting_for_from_address)

@router.message(StateFilter(PassengerStates.waiting_for_from_address))
async def process_from_address(message: Message, state: FSMContext):
    """Process 'from' address"""
    # Save from address
    await state.update_data(from_address=message.text)
    
    # Ask for destination address
    await message.answer(MESSAGES["order_to"])
    await state.set_state(PassengerStates.waiting_for_to_address)

@router.message(StateFilter(PassengerStates.waiting_for_to_address))
async def process_to_address(message: Message, state: FSMContext):
    """Process 'to' address"""
    # Save to address
    await state.update_data(to_address=message.text)
    
    # Ask for ride class
    await message.answer(MESSAGES["select_class"], reply_markup=kb.get_ride_class_keyboard())
    await state.set_state(PassengerStates.waiting_for_class)

@router.callback_query(StateFilter(PassengerStates.waiting_for_class), F.data.startswith("class_"))
async def process_ride_class(callback: CallbackQuery, state: FSMContext):
    """Process ride class selection"""
    await callback.answer()
    
    # Extract class from callback data
    ride_class = callback.data.split("_")[1]  # economy or comfort
    await state.update_data(ride_class=ride_class)
    
    # Get addresses from state
    data = await state.get_data()
    from_address = data["from_address"]
    to_address = data["to_address"]
    
    # Calculate distance and estimated cost
    distance = await geo_service.calculate_distance(from_address, to_address)
    class_info = RIDE_CLASSES[ride_class]
    estimated_cost = class_info["base_fare"] + (distance * class_info["per_km"])
    estimated_cost = round(estimated_cost)
    
    # Calculate estimated arrival time
    estimated_arrival = class_info["wait_time"]
    
    # Save to state
    await state.update_data(
        distance=distance,
        estimated_cost=estimated_cost,
        estimated_arrival=estimated_arrival
    )
    
    # Show order confirmation
    human_class = "Комфорт" if ride_class == "comfort" else "Эконом"
    
    confirmation_text = (
        f"<b>Подтвердите заказ:</b>\n\n"
        f"<b>От:</b> {from_address}\n"
        f"<b>До:</b> {to_address}\n"
        f"<b>Класс:</b> {human_class}\n"
        f"<b>Расстояние:</b> {distance} км\n"
        f"<b>Примерная стоимость:</b> {estimated_cost} руб.\n"
        f"<b>Примерное время прибытия:</b> {estimated_arrival} мин."
    )
    
    await callback.message.answer(
        confirmation_text,
        reply_markup=kb.get_confirm_order_keyboard(),
        parse_mode="HTML"
    )
    
    await state.set_state(PassengerStates.waiting_for_order_confirmation)

@router.callback_query(StateFilter(PassengerStates.waiting_for_order_confirmation), F.data == "confirm_order")
async def confirm_order(callback: CallbackQuery, state: FSMContext):
    """Confirm taxi order"""
    await callback.answer()
    
    # Get order data from state
    data = await state.get_data()
    
    # Create order in database
    order_id = await db.create_order(
        passenger_id=callback.from_user.id,
        from_address=data["from_address"],
        to_address=data["to_address"],
        ride_class=data["ride_class"],
        distance=data["distance"],
        estimated_cost=data["estimated_cost"]
    )
    
    # Inform user
    await callback.message.answer(
        f"Заказ #{order_id} создан! Ожидайте подтверждения от водителя.",
        reply_markup=kb.get_back_to_menu()
    )
    
    # Clear state
    await state.clear()

@router.callback_query(StateFilter(PassengerStates.waiting_for_order_confirmation), F.data == "cancel_order")
async def cancel_order_creation(callback: CallbackQuery, state: FSMContext):
    """Cancel order creation process"""
    await callback.answer()
    await callback.message.answer(
        "Заказ отменен.",
        reply_markup=kb.get_passenger_menu()
    )
    await state.clear()

@router.callback_query(F.data == "active_order")
async def show_active_order(callback: CallbackQuery):
    """Show active order for passenger"""
    await callback.answer()
    
    # Get active order
    active_order = await db.get_active_order(callback.from_user.id, 'passenger')
    
    if not active_order:
        await callback.message.answer(
            MESSAGES["no_active_orders"],
            reply_markup=kb.get_back_to_menu()
        )
        return
    
    # Format and show order
    order_info = await format_order_info(active_order)
    await callback.message.answer(
        order_info,
        reply_markup=kb.get_active_order_keyboard('passenger', active_order['status']),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "cancel_active_order")
async def cancel_active_order(callback: CallbackQuery):
    """Cancel active order"""
    await callback.answer()
    
    # Get active order
    active_order = await db.get_active_order(callback.from_user.id, 'passenger')
    
    if not active_order:
        await callback.message.answer(
            MESSAGES["no_active_orders"],
            reply_markup=kb.get_back_to_menu()
        )
        return
    
    # Only allow cancellation for pending or accepted orders
    if active_order['status'] in ['pending', 'accepted', 'driver_started']:
        # Cancel order
        await db.cancel_order(active_order['order_id'])
        await callback.message.answer(
            "Заказ успешно отменен.",
            reply_markup=kb.get_back_to_menu()
        )
    else:
        await callback.message.answer(
            "Невозможно отменить заказ в текущем статусе.",
            reply_markup=kb.get_back_to_menu()
        )

@router.callback_query(F.data == "rate_driver")
async def show_driver_rating(callback: CallbackQuery, state: FSMContext):
    """Show rating interface for driver"""
    await callback.answer()
    
    # Get completed order
    active_order = await db.get_active_order(callback.from_user.id, 'passenger')
    
    if not active_order or active_order['status'] != 'completed':
        await callback.message.answer(
            "Нет завершенных поездок для оценки.",
            reply_markup=kb.get_back_to_menu()
        )
        return
    
    # Save order_id to state
    await state.update_data(order_id=active_order['order_id'], driver_id=active_order['driver_id'])
    
    # Show rating keyboard
    await callback.message.answer(
        MESSAGES["rate_driver"],
        reply_markup=kb.get_rating_keyboard()
    )
    
    await state.set_state(PassengerStates.waiting_for_rating)

@router.callback_query(StateFilter(PassengerStates.waiting_for_rating), F.data.startswith("rate_"))
async def process_driver_rating(callback: CallbackQuery, state: FSMContext):
    """Process driver rating"""
    await callback.answer()
    
    # Extract rating from callback data (format: rate_X)
    rating = int(callback.data.split("_")[1])
    
    # Get order info from state
    data = await state.get_data()
    order_id = data['order_id']
    driver_id = data['driver_id']
    
    # Save rating
    await db.add_rating(
        order_id=order_id,
        from_user_id=callback.from_user.id,
        to_user_id=driver_id,
        rating=rating
    )
    
    # Thank user
    await callback.message.answer(
        f"Спасибо за вашу оценку! Вы поставили водителю {rating} {'звезд' if rating > 1 else 'звезду'}.",
        reply_markup=kb.get_back_to_menu()
    )
    
    # Clear state
    await state.clear()

@router.callback_query(F.data == "order_history")
async def show_order_history(callback: CallbackQuery):
    """Show order history for passenger"""
    await callback.answer()
    
    # Get order history
    orders = await db.get_order_history(callback.from_user.id, 'passenger')
    
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