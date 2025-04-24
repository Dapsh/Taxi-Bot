from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

import re
import keyboards as kb
from db import Database
from config import MESSAGES

# Initialize router and database
router = Router()
db = Database()

# States for registration
class RegistrationStates(StatesGroup):
    waiting_for_driver_name = State()
    waiting_for_driver_phone = State()
    waiting_for_car_model = State()
    waiting_for_car_number = State()
    
    waiting_for_passenger_name = State()
    waiting_for_passenger_phone = State()

# Phone number validation regex
PHONE_REGEX = r'^\+7\d{10}$'

@router.callback_query(F.data == "register_driver")
async def register_driver(callback: CallbackQuery, state: FSMContext):
    """Start driver registration process"""
    await callback.answer()
    await callback.message.answer(MESSAGES["register_driver"])
    await state.set_state(RegistrationStates.waiting_for_driver_name)

@router.callback_query(F.data == "register_passenger")
async def register_passenger(callback: CallbackQuery, state: FSMContext):
    """Start passenger registration process"""
    await callback.answer()
    await callback.message.answer(MESSAGES["register_passenger"])
    await state.set_state(RegistrationStates.waiting_for_passenger_name)

@router.message(StateFilter(RegistrationStates.waiting_for_driver_name))
async def process_driver_name(message: Message, state: FSMContext):
    """Process driver name"""
    # Save name
    await state.update_data(full_name=message.text)
    
    # Ask for phone number
    await message.answer(MESSAGES["phone_number"])
    await state.set_state(RegistrationStates.waiting_for_driver_phone)

@router.message(StateFilter(RegistrationStates.waiting_for_driver_phone))
async def process_driver_phone(message: Message, state: FSMContext):
    """Process driver phone number"""
    phone = message.text
    
    # Validate phone number
    if not re.match(PHONE_REGEX, phone):
        await message.answer(MESSAGES["invalid_phone"])
        return
    
    # Save phone
    await state.update_data(phone=phone)
    
    # Ask for car model
    await message.answer(MESSAGES["car_model"])
    await state.set_state(RegistrationStates.waiting_for_car_model)

@router.message(StateFilter(RegistrationStates.waiting_for_car_model))
async def process_car_model(message: Message, state: FSMContext):
    """Process car model"""
    # Save car model
    await state.update_data(car_model=message.text)
    
    # Ask for car number
    await message.answer(MESSAGES["car_number"])
    await state.set_state(RegistrationStates.waiting_for_car_number)

@router.message(StateFilter(RegistrationStates.waiting_for_car_number))
async def process_car_number(message: Message, state: FSMContext):
    """Process car number and complete driver registration"""
    # Get all data
    data = await state.get_data()
    data['car_number'] = message.text
    
    # Save driver to database
    user_id = message.from_user.id
    await db.register_user(user_id, 'driver', data['full_name'], data['phone'])
    await db.register_driver(user_id, data['car_model'], data['car_number'])
    
    # Complete registration
    await message.answer(
        f"Регистрация успешно завершена!\n\n"
        f"Имя: {data['full_name']}\n"
        f"Телефон: {data['phone']}\n"
        f"Автомобиль: {data['car_model']}\n"
        f"Номер: {data['car_number']}\n\n"
        f"Теперь вы можете принимать заказы!"
    )
    
    # Show driver menu
    await message.answer(MESSAGES["main_menu"], reply_markup=kb.get_driver_menu())
    
    # Clear state
    await state.clear()

@router.message(StateFilter(RegistrationStates.waiting_for_passenger_name))
async def process_passenger_name(message: Message, state: FSMContext):
    """Process passenger name"""
    # Save name
    await state.update_data(full_name=message.text)
    
    # Ask for phone number
    await message.answer(MESSAGES["phone_number"])
    await state.set_state(RegistrationStates.waiting_for_passenger_phone)

@router.message(StateFilter(RegistrationStates.waiting_for_passenger_phone))
async def process_passenger_phone(message: Message, state: FSMContext):
    """Process passenger phone number and complete registration"""
    phone = message.text
    
    # Validate phone number
    if not re.match(PHONE_REGEX, phone):
        await message.answer(MESSAGES["invalid_phone"])
        return
    
    # Get all data
    data = await state.get_data()
    data['phone'] = phone
    
    # Save passenger to database
    user_id = message.from_user.id
    await db.register_user(user_id, 'passenger', data['full_name'], data['phone'])
    
    # Complete registration
    await message.answer(
        f"Регистрация успешно завершена!\n\n"
        f"Имя: {data['full_name']}\n"
        f"Телефон: {data['phone']}\n\n"
        f"Теперь вы можете заказывать такси!"
    )
    
    # Show passenger menu
    await message.answer(MESSAGES["main_menu"], reply_markup=kb.get_passenger_menu())
    
    # Clear state
    await state.clear()