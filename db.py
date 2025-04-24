import aiosqlite
import datetime
from config import DB_NAME, DEFAULT_RATING


class Database:
    def __init__(self):
        self.db_name = DB_NAME

    async def init(self):
        """Initialize database and create tables if they don't exist"""
        async with aiosqlite.connect(self.db_name) as db:
            # Users table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    role TEXT NOT NULL,
                    full_name TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    rating REAL DEFAULT 5.0,
                    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Drivers table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS drivers (
                    user_id INTEGER PRIMARY KEY,
                    car_model TEXT NOT NULL,
                    car_number TEXT NOT NULL,
                    status TEXT DEFAULT 'available',
                    total_earnings REAL DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')

            # Orders table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS orders (
                    order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    passenger_id INTEGER NOT NULL,
                    driver_id INTEGER,
                    from_address TEXT NOT NULL,
                    to_address TEXT NOT NULL,
                    ride_class TEXT NOT NULL,
                    distance REAL,
                    estimated_cost REAL,
                    actual_cost REAL,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    passenger_rating INTEGER,
                    driver_rating INTEGER,
                    FOREIGN KEY (passenger_id) REFERENCES users (user_id),
                    FOREIGN KEY (driver_id) REFERENCES users (user_id)
                )
            ''')

            # Ratings table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS ratings (
                    rating_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id INTEGER NOT NULL,
                    from_user_id INTEGER NOT NULL,
                    to_user_id INTEGER NOT NULL,
                    rating INTEGER NOT NULL,
                    comment TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (order_id) REFERENCES orders (order_id),
                    FOREIGN KEY (from_user_id) REFERENCES users (user_id),
                    FOREIGN KEY (to_user_id) REFERENCES users (user_id)
                )
            ''')

            await db.commit()

    # User management
    async def register_user(self, user_id, role, full_name, phone):
        """Register a new user"""
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute(
                "INSERT OR REPLACE INTO users (user_id, role, full_name, phone) VALUES (?, ?, ?, ?)",
                (user_id, role, full_name, phone)
            )
            await db.commit()

    async def register_driver(self, user_id, car_model, car_number):
        """Register driver details"""
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute(
                "INSERT OR REPLACE INTO drivers (user_id, car_model, car_number) VALUES (?, ?, ?)",
                (user_id, car_model, car_number)
            )
            await db.commit()

    async def get_user(self, user_id):
        """Get user data by ID"""
        async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
                return await cursor.fetchone()

    async def get_driver(self, user_id):
        """Get driver data by ID"""
        async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM drivers WHERE user_id = ?", (user_id,)) as cursor:
                return await cursor.fetchone()

    async def get_available_drivers(self):
        """Get all available drivers"""
        async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute('''
                SELECT u.*, d.* FROM users u
                JOIN drivers d ON u.user_id = d.user_id
                WHERE d.status = 'available'
            ''') as cursor:
                return await cursor.fetchall()

    async def update_driver_status(self, user_id, status):
        """Update driver status"""
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute(
                "UPDATE drivers SET status = ? WHERE user_id = ?",
                (status, user_id)
            )
            await db.commit()

    async def update_user_rating(self, user_id, new_rating):
        """Update user rating"""
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute(
                "UPDATE users SET rating = ? WHERE user_id = ?",
                (new_rating, user_id)
            )
            await db.commit()

    # Order management
    async def create_order(self, passenger_id, from_address, to_address, ride_class, distance, estimated_cost):
        """Create a new order"""
        async with aiosqlite.connect(self.db_name) as db:
            cursor = await db.execute(
                '''INSERT INTO orders 
                   (passenger_id, from_address, to_address, ride_class, distance, estimated_cost, status) 
                   VALUES (?, ?, ?, ?, ?, ?, ?)''',
                (passenger_id, from_address, to_address, ride_class, distance, estimated_cost, 'pending')
            )
            order_id = cursor.lastrowid
            await db.commit()
            return order_id

    async def get_order(self, order_id):
        """Get order by ID"""
        async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM orders WHERE order_id = ?", (order_id,)) as cursor:
                return await cursor.fetchone()

    async def get_active_order(self, user_id, role='passenger'):
        """Get active order for a user"""
        field = 'passenger_id' if role == 'passenger' else 'driver_id'
        async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            query = f"SELECT * FROM orders WHERE {field} = ? AND status != 'completed' AND status != 'cancelled' ORDER BY created_at DESC LIMIT 1"
            async with db.execute(query, (user_id,)) as cursor:
                return await cursor.fetchone()

    async def get_pending_orders(self):
        """Get all pending orders"""
        async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute('''
                SELECT o.*, u.full_name, u.phone, u.rating FROM orders o
                JOIN users u ON o.passenger_id = u.user_id
                WHERE o.status = 'pending'
                ORDER BY o.created_at
            ''') as cursor:
                return await cursor.fetchall()

    async def accept_order(self, order_id, driver_id):
        """Driver accepts an order"""
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute(
                "UPDATE orders SET driver_id = ?, status = 'accepted' WHERE order_id = ? AND status = 'pending'",
                (driver_id, order_id)
            )
            await db.commit()
            # Update driver status
            await db.execute(
                "UPDATE drivers SET status = 'busy' WHERE user_id = ?",
                (driver_id,)
            )
            await db.commit()

    async def start_ride(self, order_id):
        """Start a ride"""
        now = datetime.datetime.now().isoformat()
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute(
                "UPDATE orders SET status = 'in_progress', started_at = ? WHERE order_id = ?",
                (now, order_id)
            )
            await db.commit()

    async def complete_order(self, order_id, actual_cost=None):
        """Complete an order"""
        now = datetime.datetime.now().isoformat()
        async with aiosqlite.connect(self.db_name) as db:
            # Get order details
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM orders WHERE order_id = ?", (order_id,)) as cursor:
                order = await cursor.fetchone()

            if not order:
                return False

            # Use estimated cost if actual cost is not provided
            if actual_cost is None:
                actual_cost = order['estimated_cost']

            # Update order
            await db.execute(
                "UPDATE orders SET status = 'completed', completed_at = ?, actual_cost = ? WHERE order_id = ?",
                (now, actual_cost, order_id)
            )

            # Update driver status and earnings
            await db.execute(
                "UPDATE drivers SET status = 'available', total_earnings = total_earnings + ? WHERE user_id = ?",
                (actual_cost, order['driver_id'])
            )

            await db.commit()
            return True

    async def cancel_order(self, order_id, driver_id=None):
        """Cancel an order"""
        async with aiosqlite.connect(self.db_name) as db:
            # Get order details
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM orders WHERE order_id = ?", (order_id,)) as cursor:
                order = await cursor.fetchone()

            if not order:
                return False

            # Update order
            await db.execute(
                "UPDATE orders SET status = 'cancelled' WHERE order_id = ?",
                (order_id,)
            )

            # Update driver status if driver_id is provided or order has a driver
            if driver_id or order['driver_id']:
                driver_to_update = driver_id if driver_id else order['driver_id']
                await db.execute(
                    "UPDATE drivers SET status = 'available' WHERE user_id = ?",
                    (driver_to_update,)
                )

            await db.commit()
            return True

    async def get_order_history(self, user_id, role='passenger', limit=10):
        """Get order history for a user"""
        field = 'passenger_id' if role == 'passenger' else 'driver_id'
        async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            query = f"SELECT * FROM orders WHERE {field} = ? ORDER BY created_at DESC LIMIT ?"
            async with db.execute(query, (user_id, limit)) as cursor:
                return await cursor.fetchall()

    # Rating management
    async def add_rating(self, order_id, from_user_id, to_user_id, rating, comment=None):
        """Add a rating for a user"""
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute(
                "INSERT INTO ratings (order_id, from_user_id, to_user_id, rating, comment) VALUES (?, ?, ?, ?, ?)",
                (order_id, from_user_id, to_user_id, rating, comment)
            )

            # Update the order with rating
            field = 'passenger_rating' if to_user_id == (await self.get_order(order_id))[
                'passenger_id'] else 'driver_rating'
            await db.execute(f"UPDATE orders SET {field} = ? WHERE order_id = ?", (rating, order_id))

            # Update user's average rating
            db.row_factory = aiosqlite.Row
            async with db.execute(
                    "SELECT AVG(rating) as avg_rating FROM ratings WHERE to_user_id = ?",
                    (to_user_id,)
            ) as cursor:
                result = await cursor.fetchone()
                avg_rating = result['avg_rating']

            await db.execute(
                "UPDATE users SET rating = ? WHERE user_id = ?",
                (avg_rating, to_user_id)
            )

            await db.commit()

    # Statistics
    async def get_driver_earnings(self, driver_id, period=None):
        """Get driver earnings"""
        async with aiosqlite.connect(self.db_name) as db:
            query = """
                SELECT SUM(actual_cost) as total_earnings 
                FROM orders 
                WHERE driver_id = ? AND status = 'completed'
            """
            params = [driver_id]

            if period == 'today':
                query += " AND date(completed_at) = date('now')"
            elif period == 'week':
                query += " AND date(completed_at) >= date('now', '-7 days')"
            elif period == 'month':
                query += " AND date(completed_at) >= date('now', '-30 days')"

            db.row_factory = aiosqlite.Row
            async with db.execute(query, params) as cursor:
                result = await cursor.fetchone()
                return result['total_earnings'] if result['total_earnings'] else 0

    async def get_completed_orders_count(self, user_id, role='driver'):
        """Get count of completed orders"""
        field = 'driver_id' if role == 'driver' else 'passenger_id'
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute(
                    f"SELECT COUNT(*) as count FROM orders WHERE {field} = ? AND status = 'completed'",
                    (user_id,)
            ) as cursor:
                result = await cursor.fetchone()
                return result[0]