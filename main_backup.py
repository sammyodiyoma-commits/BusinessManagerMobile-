import sqlite3
from datetime import datetime

from kivy.app import App
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import ScreenManager, Screen


DB_NAME = "business_manager.db"


# =========================================================
# DATABASE
# =========================================================

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def setup_database():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            quantity INTEGER DEFAULT 0,
            buy_price REAL DEFAULT 0,
            sell_price REAL DEFAULT 0,
            reorder_level INTEGER DEFAULT 5
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer TEXT DEFAULT 'Walk-in Customer',
            product_id INTEGER,
            quantity INTEGER DEFAULT 0,
            total REAL DEFAULT 0,
            sale_date TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS debtors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer TEXT,
            phone TEXT,
            date TEXT,
            description TEXT,
            amount REAL DEFAULT 0,
            paid REAL DEFAULT 0,
            balance REAL DEFAULT 0,
            due_date TEXT,
            status TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS creditors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            supplier TEXT,
            phone TEXT,
            date TEXT,
            description TEXT,
            amount REAL DEFAULT 0,
            paid REAL DEFAULT 0,
            balance REAL DEFAULT 0,
            due_date TEXT,
            status TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            expense_date TEXT,
            description TEXT,
            category TEXT,
            amount REAL DEFAULT 0,
            payment_method TEXT,
            notes TEXT
        )
    """)

    conn.commit()
    conn.close()


def money(value):
    return f"₦{float(value or 0):,.2f}"


def show_message(title, message):
    content = BoxLayout(
        orientation="vertical",
        padding=dp(15),
        spacing=dp(10)
    )

    content.add_widget(
        Label(
            text=message,
            halign="center"
        )
    )

    close = Button(
        text="OK",
        size_hint_y=None,
        height=dp(50)
    )

    content.add_widget(close)

    popup = Popup(
        title=title,
        content=content,
        size_hint=(0.9, 0.4)
    )

    close.bind(on_press=popup.dismiss)

    popup.open()


# =========================================================
# BASE SCREEN
# =========================================================

class BaseScreen(Screen):

    def make_header(self, title):

        header = BoxLayout(
            size_hint_y=None,
            height=dp(60),
            spacing=dp(8)
        )

        back = Button(
            text="←",
            size_hint_x=None,
            width=dp(55)
        )

        back.bind(
            on_press=lambda x: self.go_menu()
        )

        header.add_widget(back)

        header.add_widget(
            Label(
                text=title,
                font_size=dp(22)
            )
        )

        return header

    def go_menu(self):
        self.manager.current = "menu"


# =========================================================
# DASHBOARD
# =========================================================

class DashboardScreen(BaseScreen):

    def on_enter(self):
        self.build()

    def build(self):

        self.clear_widgets()

        main = BoxLayout(
            orientation="vertical",
            padding=dp(12),
            spacing=dp(10)
        )

        main.add_widget(
            Label(
                text="BUSINESS MANAGER",
                font_size=dp(27),
                size_hint_y=None,
                height=dp(60)
            )
        )

        conn = get_db()

        sales = conn.execute("""
            SELECT COALESCE(SUM(total),0)
            FROM sales
        """).fetchone()[0]

        expenses = conn.execute("""
            SELECT COALESCE(SUM(amount),0)
            FROM expenses
        """).fetchone()[0]

        debtors = conn.execute("""
            SELECT COALESCE(SUM(balance),0)
            FROM debtors
        """).fetchone()[0]

        creditors = conn.execute("""
            SELECT COALESCE(SUM(balance),0)
            FROM creditors
        """).fetchone()[0]

        products = conn.execute("""
            SELECT COUNT(*)
            FROM products
        """).fetchone()[0]

        low_stock = conn.execute("""
            SELECT COUNT(*)
            FROM products
            WHERE quantity <= reorder_level
        """).fetchone()[0]

        conn.close()

        profit = sales - expenses

        scroll = ScrollView()

        grid = GridLayout(
            cols=1,
            spacing=dp(10),
            padding=dp(5),
            size_hint_y=None
        )

        grid.bind(minimum_height=grid.setter("height"))

        cards = [
            ("TOTAL SALES", money(sales)),
            ("TOTAL EXPENSES", money(expenses)),
            ("MONEY OWED TO YOU", money(debtors)),
            ("MONEY YOU OWE", money(creditors)),
            ("NET PROFIT", money(profit)),
            ("PRODUCTS", str(products)),
            ("LOW STOCK", str(low_stock))
        ]

        for title, value in cards:

            card = BoxLayout(
                orientation="vertical",
                size_hint_y=None,
                height=dp(85),
                padding=dp(8)
            )

            card.add_widget(
                Label(
                    text=title,
                    font_size=dp(14)
                )
            )

            card.add_widget(
                Label(
                    text=value,
                    font_size=dp(22)
                )
            )

            grid.add_widget(card)

        scroll.add_widget(grid)

        main.add_widget(scroll)

        menu = Button(
            text="OPEN MENU",
            size_hint_y=None,
            height=dp(55)
        )

        menu.bind(
            on_press=lambda x:
            setattr(self.manager, "current", "menu")
        )

        main.add_widget(menu)

        self.add_widget(main)


# =========================================================
# MENU
# =========================================================

class MenuScreen(BaseScreen):

    def on_enter(self):
        self.build()

    def build(self):

        self.clear_widgets()

        layout = BoxLayout(
            orientation="vertical",
            padding=dp(15),
            spacing=dp(10)
        )

        layout.add_widget(
            Label(
                text="BUSINESS MENU",
                font_size=dp(27),
                size_hint_y=None,
                height=dp(60)
            )
        )

        pages = [
            ("🏠 DASHBOARD", "dashboard"),
            ("📦 INVENTORY", "inventory"),
            ("🛒 SALES", "sales"),
            ("👥 DEBTORS", "debtors"),
            ("🏦 CREDITORS", "creditors"),
            ("💸 EXPENSES", "expenses"),
            ("📊 PROFIT & LOSS", "profit")
        ]

        for text, page in pages:

            button = Button(
                text=text,
                font_size=dp(18),
                size_hint_y=None,
                height=dp(55)
            )

            button.bind(
                on_press=lambda x, p=page:
                setattr(self.manager, "current", p)
            )

            layout.add_widget(button)

        self.add_widget(layout)


# =========================================================
# INVENTORY
# =========================================================

class InventoryScreen(BaseScreen):

    def on_enter(self):
        self.build()

    def build(self):

        self.clear_widgets()

        main = BoxLayout(
            orientation="vertical",
            padding=dp(10),
            spacing=dp(8)
        )

        main.add_widget(
            self.make_header("INVENTORY")
        )

        form = GridLayout(
            cols=2,
            spacing=dp(6),
            size_hint_y=None
        )

        form.bind(minimum_height=form.setter("height"))

        self.name = TextInput(
            hint_text="Product name",
            multiline=False
        )

        self.quantity = TextInput(
            hint_text="Quantity",
            multiline=False,
            input_filter="int"
        )

        self.buy_price = TextInput(
            hint_text="Buy price",
            multiline=False,
            input_filter="float"
        )

        self.sell_price = TextInput(
            hint_text="Sell price",
            multiline=False,
            input_filter="float"
        )

        self.reorder = TextInput(
            hint_text="Reorder level",
            multiline=False,
            input_filter="int"
        )

        fields = [
            ("Product", self.name),
            ("Quantity", self.quantity),
            ("Buy Price", self.buy_price),
            ("Sell Price", self.sell_price),
            ("Reorder Level", self.reorder)
        ]

        for label, widget in fields:
            form.add_widget(Label(text=label))
            form.add_widget(widget)

        add = Button(
            text="ADD PRODUCT",
            size_hint_y=None,
            height=dp(50)
        )

        add.bind(
            on_press=lambda x: self.add_product()
        )

        main.add_widget(form)
        main.add_widget(add)

        scroll = ScrollView()

        self.list_layout = GridLayout(
            cols=1,
            spacing=dp(6),
            size_hint_y=None
        )

        self.list_layout.bind(
            minimum_height=self.list_layout.setter("height")
        )

        scroll.add_widget(self.list_layout)

        main.add_widget(scroll)

        self.add_widget(main)

        self.load_products()

    def add_product(self):

        try:
            name = self.name.text.strip()
            quantity = int(self.quantity.text or 0)
            buy = float(self.buy_price.text or 0)
            sell = float(self.sell_price.text or 0)
            reorder = int(self.reorder.text or 5)

            if not name:
                show_message("Error", "Enter a product name.")
                return

            conn = get_db()

            conn.execute("""
                INSERT INTO products
                (name, quantity, buy_price, sell_price, reorder_level)
                VALUES (?, ?, ?, ?, ?)
            """, (
                name,
                quantity,
                buy,
                sell,
                reorder
            ))

            conn.commit()
            conn.close()

            self.name.text = ""
            self.quantity.text = ""
            self.buy_price.text = ""
            self.sell_price.text = ""
            self.reorder.text = ""

            self.load_products()

            show_message(
                "Success",
                "Product added successfully."
            )

        except ValueError:
            show_message(
                "Error",
                "Please enter valid numbers."
            )

    def load_products(self):

        self.list_layout.clear_widgets()

        conn = get_db()

        products = conn.execute("""
            SELECT *
            FROM products
            ORDER BY id DESC
        """).fetchall()

        conn.close()

        for p in products:

            row = BoxLayout(
                size_hint_y=None,
                height=dp(70),
                spacing=dp(5)
            )

            row.add_widget(
                Label(
                    text=(
                        f"{p['name']}\n"
                        f"Stock: {p['quantity']} | "
                        f"Sell: {money(p['sell_price'])}"
                    )
                )
            )

            delete = Button(
                text="DELETE",
                size_hint_x=None,
                width=dp(80)
            )

            delete.bind(
                on_press=lambda x, pid=p["id"]:
                self.delete_product(pid)
            )

            row.add_widget(delete)

            self.list_layout.add_widget(row)

    def delete_product(self, product_id):

        conn = get_db()

        conn.execute(
            "DELETE FROM products WHERE id=?",
            (product_id,)
        )

        conn.commit()
        conn.close()

        self.load_products()


# =========================================================
# SALES
# =========================================================

class SalesScreen(BaseScreen):

    def on_enter(self):
        self.build()

    def build(self):

        self.clear_widgets()

        main = BoxLayout(
            orientation="vertical",
            padding=dp(10),
            spacing=dp(8)
        )

        main.add_widget(
            self.make_header("SALES")
        )

        form = GridLayout(
            cols=2,
            spacing=dp(6),
            size_hint_y=None
        )

        form.bind(
            minimum_height=form.setter("height")
        )

        self.customer = TextInput(
            hint_text="Customer",
            multiline=False
        )

        self.product_id = TextInput(
            hint_text="Product ID",
            multiline=False,
            input_filter="int"
        )

        self.sale_quantity = TextInput(
            hint_text="Quantity",
            multiline=False,
            input_filter="int"
        )

        for label, field in [
            ("Customer", self.customer),
            ("Product ID", self.product_id),
            ("Quantity", self.sale_quantity)
        ]:
            form.add_widget(Label(text=label))
            form.add_widget(field)

        sell = Button(
            text="RECORD SALE",
            size_hint_y=None,
            height=dp(50)
        )

        sell.bind(
            on_press=lambda x: self.record_sale()
        )

        main.add_widget(form)
        main.add_widget(sell)

        main.add_widget(
            Label(
                text="Product ID can be found in Inventory.",
                size_hint_y=None,
                height=dp(35)
            )
        )

        scroll = ScrollView()

        self.sales_list = GridLayout(
            cols=1,
            spacing=dp(5),
            size_hint_y=None
        )

        self.sales_list.bind(
            minimum_height=self.sales_list.setter("height")
        )

        scroll.add_widget(self.sales_list)

        main.add_widget(scroll)

        self.add_widget(main)

        self.load_sales()

    def record_sale(self):

        try:

            customer = (
                self.customer.text.strip()
                or "Walk-in Customer"
            )

            product_id = int(self.product_id.text)
            quantity = int(self.sale_quantity.text)

            if quantity <= 0:
                show_message(
                    "Error",
                    "Quantity must be greater than zero."
                )
                return

            conn = get_db()

            product = conn.execute("""
                SELECT *
                FROM products
                WHERE id=?
            """, (product_id,)).fetchone()

            if product is None:
                conn.close()
                show_message(
                    "Error",
                    "Product not found."
                )
                return

            if quantity > product["quantity"]:
                conn.close()
                show_message(
                    "Error",
                    f"Only {product['quantity']} items in stock."
                )
                return

            total = quantity * product["sell_price"]

            conn.execute("""
                INSERT INTO sales
                (customer, product_id, quantity, total, sale_date)
                VALUES (?, ?, ?, ?, ?)
            """, (
                customer,
                product_id,
                quantity,
                total,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))

            conn.execute("""
                UPDATE products
                SET quantity = quantity - ?
                WHERE id=?
            """, (
                quantity,
                product_id
            ))

            conn.commit()
            conn.close()

            self.customer.text = ""
            self.product_id.text = ""
            self.sale_quantity.text = ""

            self.load_sales()

            show_message(
                "Sale Recorded",
                f"Sale total: {money(total)}"
            )

        except ValueError:
            show_message(
                "Error",
                "Enter valid numbers."
            )

    def load_sales(self):

        self.sales_list.clear_widgets()

        conn = get_db()

        rows = conn.execute("""
            SELECT
                sales.*,
                products.name AS product_name
            FROM sales
            LEFT JOIN products
            ON sales.product_id = products.id
            ORDER BY sales.id DESC
        """).fetchall()

        conn.close()

        for row in rows:

            self.sales_list.add_widget(
                Label(
                    text=(
                        f"{row['product_name'] or 'Deleted Product'} | "
                        f"{row['customer']} | "
                        f"Qty: {row['quantity']} | "
                        f"{money(row['total'])}"
                    ),
                    size_hint_y=None,
                    height=dp(55)
                )
            )


# =========================================================
# DEBTORS
# =========================================================

class DebtorsScreen(BaseScreen):

    def on_enter(self):
        self.build()

    def build(self):

        self.clear_widgets()

        main = BoxLayout(
            orientation="vertical",
            padding=dp(10),
            spacing=dp(7)
        )

        main.add_widget(
            self.make_header("DEBTORS")
        )

        form = GridLayout(
            cols=2,
            spacing=dp(5),
            size_hint_y=None
        )

        form.bind(
            minimum_height=form.setter("height")
        )

        self.debtor_customer = TextInput(
            hint_text="Customer",
            multiline=False
        )

        self.debtor_phone = TextInput(
            hint_text="Phone",
            multiline=False
        )

        self.debtor_description = TextInput(
            hint_text="Description",
            multiline=False
        )

        self.debtor_amount = TextInput(
            hint_text="Amount",
            multiline=False,
            input_filter="float"
        )

        self.debtor_paid = TextInput(
            hint_text="Paid",
            multiline=False,
            input_filter="float"
        )

        fields = [
            ("Customer", self.debtor_customer),
            ("Phone", self.debtor_phone),
            ("Description", self.debtor_description),
            ("Amount", self.debtor_amount),
            ("Paid", self.debtor_paid)
        ]

        for label, field in fields:
            form.add_widget(Label(text=label))
            form.add_widget(field)

        add = Button(
            text="ADD DEBT",
            size_hint_y=None,
            height=dp(50)
        )

        add.bind(
            on_press=lambda x: self.add_debt()
        )

        main.add_widget(form)
        main.add_widget(add)

        scroll = ScrollView()

        self.debt_list = GridLayout(
            cols=1,
            spacing=dp(5),
            size_hint_y=None
        )

        self.debt_list.bind(
            minimum_height=self.debt_list.setter("height")
        )

        scroll.add_widget(self.debt_list)

        main.add_widget(scroll)

        self.add_widget(main)

        self.load_debts()

    def add_debt(self):

        try:

            customer = self.debtor_customer.text.strip()
            phone = self.debtor_phone.text.strip()
            description = self.debtor_description.text.strip()

            amount = float(self.debtor_amount.text or 0)
            paid = float(self.debtor_paid.text or 0)

            if not customer:
                show_message(
                    "Error",
                    "Enter customer name."
                )
                return

            balance = amount - paid

            status = "Paid" if balance <= 0 else "Unpaid"

            conn = get_db()

            conn.execute("""
                INSERT INTO debtors
                (customer, phone, date, description,
                 amount, paid, balance, due_date, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                customer,
                phone,
                datetime.now().strftime("%Y-%m-%d"),
                description,
                amount,
                paid,
                balance,
                "",
                status
            ))

            conn.commit()
            conn.close()

            self.load_debts()

            show_message(
                "Success",
                "Debtor added."
            )

        except ValueError:
            show_message(
                "Error",
                "Enter a valid amount."
            )

    def load_debts(self):

        self.debt_list.clear_widgets()

        conn = get_db()

        rows = conn.execute("""
            SELECT *
            FROM debtors
            ORDER BY id DESC
        """).fetchall()

        conn.close()

        for row in rows:

            self.debt_list.add_widget(
                Label(
                    text=(
                        f"{row['customer']} | "
                        f"Total: {money(row['amount'])} | "
                        f"Paid: {money(row['paid'])} | "
                        f"Balance: {money(row['balance'])}"
                    ),
                    size_hint_y=None,
                    height=dp(55)
                )
            )


# =========================================================
# CREDITORS
# =========================================================

class CreditorsScreen(BaseScreen):

    def on_enter(self):
        self.build()

    def build(self):

        self.clear_widgets()

        main = BoxLayout(
            orientation="vertical",
            padding=dp(10),
            spacing=dp(7)
        )

        main.add_widget(
            self.make_header("CREDITORS")
        )

        form = GridLayout(
            cols=2,
            spacing=dp(5),
            size_hint_y=None
        )

        form.bind(
            minimum_height=form.setter("height")
        )

        self.supplier = TextInput(
            hint_text="Supplier",
            multiline=False
        )

        self.supplier_phone = TextInput(
            hint_text="Phone",
            multiline=False
        )

        self.credit_description = TextInput(
            hint_text="Description",
            multiline=False
        )

        self.credit_amount = TextInput(
            hint_text="Amount",
            multiline=False,
            input_filter="float"
        )

        self.credit_paid = TextInput(
            hint_text="Paid",
            multiline=False,
            input_filter="float"
        )

        fields = [
            ("Supplier", self.supplier),
            ("Phone", self.supplier_phone),
            ("Description", self.credit_description),
            ("Amount", self.credit_amount),
            ("Paid", self.credit_paid)
        ]

        for label, field in fields:
            form.add_widget(Label(text=label))
            form.add_widget(field)

        add = Button(
            text="ADD CREDITOR",
            size_hint_y=None,
            height=dp(50)
        )

        add.bind(
            on_press=lambda x: self.add_creditor()
        )

        main.add_widget(form)
        main.add_widget(add)

        scroll = ScrollView()

        self.credit_list = GridLayout(
            cols=1,
            spacing=dp(5),
            size_hint_y=None
        )

        self.credit_list.bind(
            minimum_height=self.credit_list.setter("height")
        )

        scroll.add_widget(self.credit_list)

        main.add_widget(scroll)

        self.add_widget(main)

        self.load_creditors()

    def add_creditor(self):

        try:

            supplier = self.supplier.text.strip()
            phone = self.supplier_phone.text.strip()
            description = self.credit_description.text.strip()

            amount = float(self.credit_amount.text or 0)
            paid = float(self.credit_paid.text or 0)

            if not supplier:
                show_message(
                    "Error",
                    "Enter supplier name."
                )
                return

            balance = amount - paid

            status = "Paid" if balance <= 0 else "Unpaid"

            conn = get_db()

            conn.execute("""
                INSERT INTO creditors
                (supplier, phone, date, description,
                 amount, paid, balance, due_date, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                supplier,
                phone,
                datetime.now().strftime("%Y-%m-%d"),
                description,
                amount,
                paid,
                balance,
                "",
                status
            ))

            conn.commit()
            conn.close()

            self.load_creditors()

            show_message(
                "Success",
                "Creditor added."
            )

        except ValueError:
            show_message(
                "Error",
                "Enter a valid amount."
            )

    def load_creditors(self):

        self.credit_list.clear_widgets()

        conn = get_db()

        rows = conn.execute("""
            SELECT *
            FROM creditors
            ORDER BY id DESC
        """).fetchall()

        conn.close()

        for row in rows:

            self.credit_list.add_widget(
                Label(
                    text=(
                        f"{row['supplier']} | "
                        f"Total: {money(row['amount'])} | "
                        f"Paid: {money(row['paid'])} | "
                        f"Balance: {money(row['balance'])}"
                    ),
                    size_hint_y=None,
                    height=dp(55)
                )
            )


# =========================================================
# EXPENSES
# =========================================================

class ExpensesScreen(BaseScreen):

    def on_enter(self):
        self.build()

    def build(self):

        self.clear_widgets()

        main = BoxLayout(
            orientation="vertical",
            padding=dp(10),
            spacing=dp(7)
        )

        main.add_widget(
            self.make_header("EXPENSES")
        )

        form = GridLayout(
            cols=2,
            spacing=dp(5),
            size_hint_y=None
        )

        form.bind(
            minimum_height=form.setter("height")
        )

        self.expense_description = TextInput(
            hint_text="Description",
            multiline=False
        )

        self.expense_category = TextInput(
            hint_text="Category",
            multiline=False
        )

        self.expense_amount = TextInput(
            hint_text="Amount",
            multiline=False,
            input_filter="float"
        )

        fields = [
            ("Description", self.expense_description),
            ("Category", self.expense_category),
            ("Amount", self.expense_amount)
        ]

        for label, field in fields:
            form.add_widget(Label(text=label))
            form.add_widget(field)

        add = Button(
            text="ADD EXPENSE",
            size_hint_y=None,
            height=dp(50)
        )

        add.bind(
            on_press=lambda x: self.add_expense()
        )

        main.add_widget(form)
        main.add_widget(add)

        scroll = ScrollView()

        self.expense_list = GridLayout(
            cols=1,
            spacing=dp(5),
            size_hint_y=None
        )

        self.expense_list.bind(
            minimum_height=self.expense_list.setter("height")
        )

        scroll.add_widget(self.expense_list)

        main.add_widget(scroll)

        self.add_widget(main)

        self.load_expenses()

    def add_expense(self):

        try:

            description = self.expense_description.text.strip()
            category = self.expense_category.text.strip()
            amount = float(self.expense_amount.text or 0)

            if not description:
                show_message(
                    "Error",
                    "Enter an expense description."
                )
                return

            conn = get_db()

            conn.execute("""
                INSERT INTO expenses
                (expense_date, description, category,
                 amount, payment_method, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                datetime.now().strftime("%Y-%m-%d"),
                description,
                category,
                amount,
                "Cash",
                ""
            ))

            conn.commit()
            conn.close()

            self.expense_description.text = ""
            self.expense_category.text = ""
            self.expense_amount.text = ""

            self.load_expenses()

            show_message(
                "Success",
                "Expense added."
            )

        except ValueError:
            show_message(
                "Error",
                "Enter a valid amount."
            )

    def load_expenses(self):

        self.expense_list.clear_widgets()

        conn = get_db()

        rows = conn.execute("""
            SELECT *
            FROM expenses
            ORDER BY id DESC
        """).fetchall()

        conn.close()

        for row in rows:

            self.expense_list.add_widget(
                Label(
                    text=(
                        f"{row['description']} | "
                        f"{row['category']} | "
                        f"{money(row['amount'])}"
                    ),
                    size_hint_y=None,
                    height=dp(55)
                )
            )


# =========================================================
# PROFIT & LOSS
# =========================================================

class ProfitScreen(BaseScreen):

    def on_enter(self):
        self.build()

    def build(self):

        self.clear_widgets()

        main = BoxLayout(
            orientation="vertical",
            padding=dp(20),
            spacing=dp(15)
        )

        main.add_widget(
            self.make_header("PROFIT & LOSS")
        )

        conn = get_db()

        sales = conn.execute("""
            SELECT COALESCE(SUM(total),0)
            FROM sales
        """).fetchone()[0]

        expenses = conn.execute("""
            SELECT COALESCE(SUM(amount),0)
            FROM expenses
        """).fetchone()[0]

        conn.close()

        profit = sales - expenses

        main.add_widget(
            Label(
                text=f"TOTAL SALES\n{money(sales)}",
                font_size=dp(23)
            )
        )

        main.add_widget(
            Label(
                text=f"TOTAL EXPENSES\n{money(expenses)}",
                font_size=dp(23)
            )
        )

        main.add_widget(
            Label(
                text=f"NET PROFIT\n{money(profit)}",
                font_size=dp(28)
            )
        )

        refresh = Button(
            text="REFRESH",
            size_hint_y=None,
            height=dp(55)
        )

        refresh.bind(
            on_press=lambda x: self.build()
        )

        main.add_widget(refresh)

        self.add_widget(main)


# =========================================================
# APPLICATION
# =========================================================

class BusinessManager(App):

    def build(self):

        setup_database()

        manager = ScreenManager()

        manager.add_widget(
            DashboardScreen(name="dashboard")
        )

        manager.add_widget(
            MenuScreen(name="menu")
        )

        manager.add_widget(
            InventoryScreen(name="inventory")
        )

        manager.add_widget(
            SalesScreen(name="sales")
        )

        manager.add_widget(
            DebtorsScreen(name="debtors")
        )

        manager.add_widget(
            CreditorsScreen(name="creditors")
        )

        manager.add_widget(
            ExpensesScreen(name="expenses")
        )

        manager.add_widget(
            ProfitScreen(name="profit")
        )

        manager.current = "dashboard"

        return manager


if __name__ == "__main__":
    BusinessManager().run()
