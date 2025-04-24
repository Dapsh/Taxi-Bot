import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Bot token from BotFather
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Database settings
DB_NAME = "fifty_drive.db"

# Ride classes and pricing
RIDE_CLASSES = {
    "economy": {"base_fare": 100, "per_km": 15, "wait_time": 5},
    "comfort": {"base_fare": 150, "per_km": 20, "wait_time": 3}
}

# Rating thresholds
MIN_RATING = 1
MAX_RATING = 5
DEFAULT_RATING = 5

# Timeout for order acceptance (seconds)
ORDER_ACCEPTANCE_TIMEOUT = 60

# Message templates
MESSAGES = {
    "welcome": "Добро пожаловать в Fifty Drive! Выберите роль:",
    "register_driver": "Регистрация водителя. Введите ваше ФИО:",
    "register_passenger": "Регистрация пассажира. Введите ваше ФИО:",
    "phone_number": "Введите ваш номер телефона (формат +79XXXXXXXXX):",
    "car_model": "Введите марку и модель вашего автомобиля:",
    "car_number": "Введите государственный номер вашего автомобиля:",
    "registration_complete": "Регистрация успешно завершена!",
    "main_menu": "Главное меню. Выберите действие:",
    "order_from": "Введите адрес отправления:",
    "order_to": "Введите адрес назначения:",
    "select_class": "Выберите класс поездки:",
    "order_confirmation": "Подтвердите заказ:\nОт: {from_address}\nДо: {to_address}\nКласс: {ride_class}\nПримерная стоимость: {estimated_cost} руб.\nПримерное время прибытия: {estimated_arrival} мин.",
    "order_created": "Заказ создан! Ожидайте подтверждения от водителя.",
    "order_accepted": "Водитель принял ваш заказ и скоро прибудет!",
    "order_declined": "Водитель отклонил заказ. Ищем другого водителя...",
    "order_cancelled": "Заказ отменен.",
    "order_completed": "Поездка завершена. Спасибо, что воспользовались Fifty Drive!",
    "driver_started": "Водитель выехал и скоро будет на месте!",
    "driver_arrived": "Водитель прибыл на место посадки!",
    "rate_driver": "Оцените водителя от 1 до 5:",
    "rate_passenger": "Оцените пассажира от 1 до 5:",
    "no_active_orders": "На данный момент нет активных заказов.",
    "order_already_accepted": "Этот заказ уже принят другим водителем.",
    "invalid_phone": "Неверный формат номера телефона. Пожалуйста, используйте формат +79XXXXXXXXX",
    "invalid_input": "Некорректный ввод. Пожалуйста, попробуйте снова.",
    "no_history": "История поездок пуста.",
    "status_changed": "Ваш статус изменен на: {status}",
    "new_order": "Новый заказ!\nОт: {from_address}\nДо: {to_address}\nКласс: {ride_class}\nПримерная стоимость: {estimated_cost} руб.\nРасстояние: {distance} км",
    "earnings_today": "Ваш заработок за сегодня: {amount} руб.",
    "earnings_total": "Ваш общий заработок: {amount} руб."
}