import os
import sqlite3
from datetime import datetime

from kivy.app import App
from kivy.metrics import dp
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup


# =========================================================
# DATABASE
# =========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "business_manager.db")


def get_db():
    conn = sqlite3.connect(DATABASE)
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
            sale_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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


# =========================================================
# HELPERS
# =========================================================

def money(value):
    try:
        return f"₦{float(value):,.2f}"
    except:
        return "₦0.00"


def make_label(text="", size=16, bold=False, height=45):
    return Label(
        text=str(text),
        font_size=dp(size),
        bold=bold,
        size_hint_y=None,
        height=dp(height),
        halign="left",
        valign="middle",
        text_size=(None, None)
    )


def make_input(hint="", height=48):
    return TextInput(
        hint_text=hint,
        multiline=False,
        size_hint_y=None,
        height=dp(height),
        padding=[dp(10), dp(10)]
    )


def show_message(title, message):
    content = BoxLayout(
        orientation="vertical",
        padding=dp(15),
        spacing=dp(10)
    )

    content.add_widget(
        Label(
            text=str(message),
            font_size=dp(16)
        )
    )

    close_button = Button(
        text="OK",
        size_hint_y=None,
        height=dp(45)
    )

    popup = Popup(
        title=title,
        content=content,
        size_hint=(0.9, 0.4)
    )

    close_button.bind(on_press=popup.dismiss)
    content.add_widget(close_button)

    popup.open()


# =========================================================
# BASE SCREEN
# =========================================================

class BaseScreen(Screen):

    def main_layout(self, title):
        root = BoxLayout(
            orientation="vertical",
            padding=dp(10),
            spacing=dp(8)
        )

        header = BoxLayout(
            size_hint_y=None,
            height=dp(55),
            spacing=dp(8)
        )

        menu = Button(
            text="☰",
            size_hint_x=None,
            width=dp(55)
        )

        menu.bind(on_press=lambda x: self.open_menu())

        header.add_widget(menu)

        header.add_widget(
            Label(
                text=title,
                font_size=dp(22),
                bold=True
            )
        )

        root.add_widget(header)

        return root

    def open_menu(self):
        content = BoxLayout(
            orientation="vertical",
            padding=dp(10),
            spacing=dp(8)
        )

        screens = [
            ("Dashboard", "dashboard"),
            ("Inventory", "inventory"),
            ("Sales", "sales"),
            ("Debtors", "debtors"),
            ("Creditors", "creditors"),
            ("Expenses", "expenses"),
            ("Profit & Loss", "profit")
        ]

        popup = Popup(
            title="Business Manager",
            content=content,
            size_hint=(0.8, 0.85)
        )

        for text, screen_name in screens:
            button = Button(
                text=text,
                size_hint_y=None,
                height=dp(50)
            )

            button.bind(
                on_press=lambda x, name=screen_name:
                self.go_to(name, popup)
            )

            content.add_widget(button)

        popup.open()

    def go_to(self, screen_name, popup=None):
        if popup:
            popup.dismiss()

        self.manager.current = screen_name


# =========================================================
# DASHBOARD
# =========================================================

class DashboardScreen(BaseScreen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.root_layout = self.main_layout("Dashboard")

        scroll = ScrollView()

        self.content = BoxLayout(
            orientation="vertical",
            spacing=dp(10),
            padding=dp(5),
            size_hint_y=None
        )

        self.content.bind(
            minimum_height=self.content.setter("height")
        )

        scroll.add_widget(self.content)

        self.root_layout.add_widget(scroll)

        self.add_widget(self.root_layout)

    def on_pre_enter(self):
        self.refresh()

    def refresh(self):

        self.content.clear_widgets()

        conn = get_db()

        sales = conn.execute("""
            SELECT COALESCE(SUM(total), 0)
            FROM sales
        """).fetchone()[0]

        expenses = conn.execute("""
            SELECT COALESCE(SUM(amount), 0)
            FROM expenses
        """).fetchone()[0]

        debtors = conn.execute("""
            SELECT COALESCE(SUM(balance), 0)
            FROM debtors
        """).fetchone()[0]

        creditors = conn.execute("""
            SELECT COALESCE(SUM(balance), 0)
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

        net = sales - expenses

        self.content.add_widget(
            make_label(
                "Welcome to Business Manager",
                21,
                True,
                55
            )
        )

        stats = [
            ("Total Sales", money(sales)),
            ("Total Expenses", money(expenses)),
            ("Money Owed To You", money(debtors)),
            ("Money You Owe", money(creditors)),
            ("Net Profit", money(net)),
            ("Products", products),
            ("Low Stock", low_stock)
        ]

        for title, value in stats:

            card = BoxLayout(
                orientation="vertical",
                padding=dp(12),
                size_hint_y=None,
                height=dp(90)
            )

            card.add_widget(
                make_label(title, 15, False, 35)
            )

            card.add_widget(
                make_label(str(value), 23, True, 45)
            )

            self.content.add_widget(card)


# =========================================================
# INVENTORY
# =========================================================

class InventoryScreen(BaseScreen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.root_layout = self.main_layout("Inventory")

        add_button = Button(
            text="+ ADD PRODUCT",
            size_hint_y=None,
            height=dp(50)
        )

        add_button.bind(on_press=self.add_product_popup)

        self.root_layout.add_widget(add_button)

        scroll = ScrollView()

        self.content = BoxLayout(
            orientation="vertical",
            spacing=dp(8),
            size_hint_y=None
        )

        self.content.bind(
            minimum_height=self.content.setter("height")
        )

        scroll.add_widget(self.content)

        self.root_layout.add_widget(scroll)

        self.add_widget(self.root_layout)

    def on_pre_enter(self):
        self.refresh()

    def refresh(self):

        self.content.clear_widgets()

        conn = get_db()

        products = conn.execute("""
            SELECT *
            FROM products
            ORDER BY name
        """).fetchall()

        conn.close()

        if not products:
            self.content.add_widget(
                make_label(
                    "No products in inventory.",
                    17,
                    False,
                    60
                )
            )
            return

        for product in products:

            box = BoxLayout(
                orientation="vertical",
                padding=dp(10),
                size_hint_y=None,
                height=dp(145)
            )

            box.add_widget(
                make_label(
                    product["name"],
                    18,
                    True,
                    35
                )
            )

            box.add_widget(
                make_label(
                    f"Stock: {product['quantity']}    "
                    f"Buy: {money(product['buy_price'])}    "
                    f"Sell: {money(product['sell_price'])}",
                    14,
                    False,
                    35
                )
            )

            box.add_widget(
                make_label(
                    f"Reorder level: {product['reorder_level']}",
                    14,
                    False,
                    30
                )
            )

            buttons = BoxLayout(
                spacing=dp(5),
                size_hint_y=None,
                height=dp(40)
            )

            edit = Button(text="EDIT")
            delete = Button(text="DELETE")

            edit.bind(
                on_press=lambda x, p=dict(product):
                self.edit_product(p)
            )

            delete.bind(
                on_press=lambda x, pid=product["id"]:
                self.delete_product(pid)
            )

            buttons.add_widget(edit)
            buttons.add_widget(delete)

            box.add_widget(buttons)

            self.content.add_widget(box)

    def add_product_popup(self, instance):

        content = BoxLayout(
            orientation="vertical",
            spacing=dp(8),
            padding=dp(10)
        )

        name = make_input("Product name")
        quantity = make_input("Quantity")
        buy = make_input("Buying price")
        sell = make_input("Selling price")
        reorder = make_input("Reorder level")

        for field in [name, quantity, buy, sell, reorder]:
            content.add_widget(field)

        save = Button(
            text="SAVE PRODUCT",
            size_hint_y=None,
            height=dp(48)
        )

        content.add_widget(save)

        popup = Popup(
            title="Add Product",
            content=content,
            size_hint=(0.92, 0.85)
        )

        def save_product(instance):

            try:
                q = int(quantity.text)
                b = float(buy.text)
                s = float(sell.text)
                r = int(reorder.text or 5)

                if not name.text.strip():
                    raise ValueError()

                conn = get_db()

                conn.execute("""
                    INSERT INTO products
                    (name, quantity, buy_price, sell_price, reorder_level)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    name.text.strip(),
                    q,
                    b,
                    s,
                    r
                ))

                conn.commit()
                conn.close()

                popup.dismiss()
                self.refresh()

            except:
                show_message(
                    "Error",
                    "Please enter valid product information."
                )

        save.bind(on_press=save_product)

        popup.open()

    def edit_product(self, product):

        content = BoxLayout(
            orientation="vertical",
            spacing=dp(8),
            padding=dp(10)
        )

        name = make_input("Product name")
        quantity = make_input("Quantity")
        buy = make_input("Buying price")
        sell = make_input("Selling price")
        reorder = make_input("Reorder level")

        name.text = product["name"]
        quantity.text = str(product["quantity"])
        buy.text = str(product["buy_price"])
        sell.text = str(product["sell_price"])
        reorder.text = str(product["reorder_level"])

        for field in [name, quantity, buy, sell, reorder]:
            content.add_widget(field)

        save = Button(
            text="UPDATE PRODUCT",
            size_hint_y=None,
            height=dp(48)
        )

        content.add_widget(save)

        popup = Popup(
            title="Edit Product",
            content=content,
            size_hint=(0.92, 0.85)
        )

        def update(instance):

            try:
                conn = get_db()

                conn.execute("""
                    UPDATE products
                    SET name=?,
                        quantity=?,
                        buy_price=?,
                        sell_price=?,
                        reorder_level=?
                    WHERE id=?
                """, (
                    name.text.strip(),
                    int(quantity.text),
                    float(buy.text),
                    float(sell.text),
                    int(reorder.text),
                    product["id"]
                ))

                conn.commit()
                conn.close()

                popup.dismiss()
                self.refresh()

            except:
                show_message(
                    "Error",
                    "Please enter valid information."
                )

        save.bind(on_press=update)

        popup.open()

    def delete_product(self, product_id):

        content = BoxLayout(
            orientation="vertical",
            spacing=dp(10),
            padding=dp(10)
        )

        content.add_widget(
            Label(
                text="Delete this product?"
            )
        )

        buttons = BoxLayout(
            spacing=dp(8),
            size_hint_y=None,
            height=dp(45)
        )

        yes = Button(text="YES")
        no = Button(text="NO")

        buttons.add_widget(yes)
        buttons.add_widget(no)

        content.add_widget(buttons)

        popup = Popup(
            title="Confirm Delete",
            content=content,
            size_hint=(0.8, 0.35)
        )

        no.bind(on_press=popup.dismiss)

        def confirm(instance):

            conn = get_db()

            conn.execute(
                "DELETE FROM products WHERE id=?",
                (product_id,)
            )

            conn.commit()
            conn.close()

            popup.dismiss()
            self.refresh()

        yes.bind(on_press=confirm)

        popup.open()


# =========================================================
# SALES
# =========================================================

class SalesScreen(BaseScreen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.root_layout = self.main_layout("Sales")

        add = Button(
            text="+ ADD SALE",
            size_hint_y=None,
            height=dp(50)
        )

        add.bind(on_press=self.add_sale_popup)

        self.root_layout.add_widget(add)

        scroll = ScrollView()

        self.content = BoxLayout(
            orientation="vertical",
            spacing=dp(8),
            size_hint_y=None
        )

        self.content.bind(
            minimum_height=self.content.setter("height")
        )

        scroll.add_widget(self.content)

        self.root_layout.add_widget(scroll)

        self.add_widget(self.root_layout)

    def on_pre_enter(self):
        self.refresh()

    def refresh(self):

        self.content.clear_widgets()

        conn = get_db()

        rows = conn.execute("""
            SELECT sales.*,
                   products.name AS product_name
            FROM sales
            LEFT JOIN products
            ON sales.product_id = products.id
            ORDER BY sales.id DESC
        """).fetchall()

        conn.close()

        if not rows:
            self.content.add_widget(
                make_label("No sales recorded.", 17, False, 60)
            )
            return

        for row in rows:

            self.content.add_widget(
                make_label(
                    f"{row['product_name'] or 'Unknown'}\n"
                    f"Customer: {row['customer']}\n"
                    f"Quantity: {row['quantity']}    "
                    f"Total: {money(row['total'])}\n"
                    f"Date: {row['sale_date']}",
                    14,
                    False,
                    100
                )
            )

    def add_sale_popup(self, instance):

        conn = get_db()

        products = conn.execute("""
            SELECT *
            FROM products
            WHERE quantity > 0
            ORDER BY name
        """).fetchall()

        conn.close()

        if not products:
            show_message(
                "No Stock",
                "There are no products with available stock."
            )
            return

        content = BoxLayout(
            orientation="vertical",
            spacing=dp(8),
            padding=dp(10)
        )

        customer = make_input("Customer name")

        product_input = make_input(
            "Enter product ID"
        )

        quantity = make_input("Quantity")

        content.add_widget(customer)
        content.add_widget(product_input)
        content.add_widget(quantity)

        content.add_widget(
            make_label(
                "Available products:",
                15,
                True,
                35
            )
        )

        for p in products:
            content.add_widget(
                make_label(
                    f"ID {p['id']} - {p['name']} "
                    f"(Stock: {p['quantity']})",
                    13,
                    False,
                    30
                )
            )

        save = Button(
            text="SAVE SALE",
            size_hint_y=None,
            height=dp(48)
        )

        content.add_widget(save)

        popup = Popup(
            title="Add Sale",
            content=content,
            size_hint=(0.94, 0.9)
        )

        def save_sale(instance):

            try:
                product_id = int(product_input.text)
                qty = int(quantity.text)

                if qty <= 0:
                    raise ValueError()

                conn = get_db()

                product = conn.execute("""
                    SELECT *
                    FROM products
                    WHERE id=?
                """, (product_id,)).fetchone()

                if not product:
                    conn.close()
                    show_message(
                        "Error",
                        "Product not found."
                    )
                    return

                if qty > product["quantity"]:
                    conn.close()
                    show_message(
                        "Error",
                        f"Only {product['quantity']} available."
                    )
                    return

                total = qty * product["sell_price"]

                conn.execute("""
                    INSERT INTO sales
                    (customer, product_id, quantity, total)
                    VALUES (?, ?, ?, ?)
                """, (
                    customer.text.strip() or "Walk-in Customer",
                    product_id,
                    qty,
                    total
                ))

                conn.execute("""
                    UPDATE products
                    SET quantity = quantity - ?
                    WHERE id=?
                """, (
                    qty,
                    product_id
                ))

                conn.commit()
                conn.close()

                popup.dismiss()
                self.refresh()

            except:
                show_message(
                    "Error",
                    "Enter a valid product ID and quantity."
                )

        save.bind(on_press=save_sale)

        popup.open()


# =========================================================
# DEBTORS
# =========================================================

class DebtorsScreen(BaseScreen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.root_layout = self.main_layout("Debtors")

        add = Button(
            text="+ ADD DEBTOR",
            size_hint_y=None,
            height=dp(50)
        )

        add.bind(on_press=self.add_debtor)

        self.root_layout.add_widget(add)

        scroll = ScrollView()

        self.content = BoxLayout(
            orientation="vertical",
            spacing=dp(8),
            size_hint_y=None
        )

        self.content.bind(
            minimum_height=self.content.setter("height")
        )

        scroll.add_widget(self.content)
        self.root_layout.add_widget(scroll)

        self.add_widget(self.root_layout)

    def on_pre_enter(self):
        self.refresh()

    def refresh(self):

        self.content.clear_widgets()

        conn = get_db()

        rows = conn.execute("""
            SELECT *
            FROM debtors
            ORDER BY id DESC
        """).fetchall()

        conn.close()

        for row in rows:

            self.content.add_widget(
                make_label(
                    f"{row['customer']}\n"
                    f"Phone: {row['phone']}\n"
                    f"Amount: {money(row['amount'])}\n"
                    f"Paid: {money(row['paid'])}\n"
                    f"Balance: {money(row['balance'])}\n"
                    f"Status: {row['status']}",
                    14,
                    False,
                    130
                )
            )

    def add_debtor(self, instance):

        fields = self.form_popup(
            "Add Debtor",
            [
                "Customer",
                "Phone",
                "Description",
                "Amount",
                "Paid",
                "Due date"
            ]
        )

        popup, inputs = fields

        def save(instance):

            try:
                amount = float(inputs[3].text)
                paid = float(inputs[4].text or 0)
                balance = amount - paid

                status = "Paid" if balance <= 0 else "Unpaid"

                conn = get_db()

                conn.execute("""
                    INSERT INTO debtors
                    (customer, phone, date, description,
                     amount, paid, balance, due_date, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    inputs[0].text,
                    inputs[1].text,
                    datetime.now().strftime("%Y-%m-%d"),
                    inputs[2].text,
                    amount,
                    paid,
                    balance,
                    inputs[5].text,
                    status
                ))

                conn.commit()
                conn.close()

                popup.dismiss()
                self.refresh()

            except:
                show_message(
                    "Error",
                    "Please enter valid amounts."
                )

        inputs[-1].bind(on_press=save)

    def form_popup(self, title, names):

        content = BoxLayout(
            orientation="vertical",
            spacing=dp(8),
            padding=dp(10)
        )

        inputs = []

        for name in names:
            field = make_input(name)
            inputs.append(field)
            content.add_widget(field)

        button = Button(
            text="SAVE",
            size_hint_y=None,
            height=dp(48)
        )

        content.add_widget(button)

        popup = Popup(
            title=title,
            content=content,
            size_hint=(0.92, 0.85)
        )

        popup.open()

        return popup, inputs


# =========================================================
# CREDITORS
# =========================================================

class CreditorsScreen(BaseScreen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.root_layout = self.main_layout("Creditors")

        add = Button(
            text="+ ADD CREDITOR",
            size_hint_y=None,
            height=dp(50)
        )

        add.bind(on_press=self.add_creditor)

        self.root_layout.add_widget(add)

        scroll = ScrollView()

        self.content = BoxLayout(
            orientation="vertical",
            spacing=dp(8),
            size_hint_y=None
        )

        self.content.bind(
            minimum_height=self.content.setter("height")
        )

        scroll.add_widget(self.content)

        self.root_layout.add_widget(scroll)

        self.add_widget(self.root_layout)

    def on_pre_enter(self):
        self.refresh()

    def refresh(self):

        self.content.clear_widgets()

        conn = get_db()

        rows = conn.execute("""
            SELECT *
            FROM creditors
            ORDER BY id DESC
        """).fetchall()

        conn.close()

        for row in rows:

            self.content.add_widget(
                make_label(
                    f"{row['supplier']}\n"
                    f"Phone: {row['phone']}\n"
                    f"Amount: {money(row['amount'])}\n"
                    f"Paid: {money(row['paid'])}\n"
                    f"Balance: {money(row['balance'])}\n"
                    f"Status: {row['status']}",
                    14,
                    False,
                    130
                )
            )

    def add_creditor(self, instance):

        content = BoxLayout(
            orientation="vertical",
            spacing=dp(8),
            padding=dp(10)
        )

        fields = []

        for hint in [
            "Supplier",
            "Phone",
            "Description",
            "Amount",
            "Paid",
            "Due date"
        ]:
            field = make_input(hint)
            fields.append(field)
            content.add_widget(field)

        save = Button(
            text="SAVE",
            size_hint_y=None,
            height=dp(48)
        )

        content.add_widget(save)

        popup = Popup(
            title="Add Creditor",
            content=content,
            size_hint=(0.92, 0.85)
        )

        def save_creditor(instance):

            try:
                amount = float(fields[3].text)
                paid = float(fields[4].text or 0)
                balance = amount - paid

                status = "Paid" if balance <= 0 else "Unpaid"

                conn = get_db()

                conn.execute("""
                    INSERT INTO creditors
                    (supplier, phone, date, description,
                     amount, paid, balance, due_date, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    fields[0].text,
                    fields[1].text,
                    datetime.now().strftime("%Y-%m-%d"),
                    fields[2].text,
                    amount,
                    paid,
                    balance,
                    fields[5].text,
                    status
                ))

                conn.commit()
                conn.close()

                popup.dismiss()
                self.refresh()

            except:
                show_message(
                    "Error",
                    "Please enter valid amounts."
                )

        save.bind(on_press=save_creditor)

        popup.open()


# =========================================================
# EXPENSES
# =========================================================

class ExpensesScreen(BaseScreen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.root_layout = self.main_layout("Expenses")

        add = Button(
            text="+ ADD EXPENSE",
            size_hint_y=None,
            height=dp(50)
        )

        add.bind(on_press=self.add_expense)

        self.root_layout.add_widget(add)

        self.total_label = make_label(
            "Total Expenses: ₦0.00",
            18,
            True,
            50
        )

        self.root_layout.add_widget(self.total_label)

        scroll = ScrollView()

        self.content = BoxLayout(
            orientation="vertical",
            spacing=dp(8),
            size_hint_y=None
        )

        self.content.bind(
            minimum_height=self.content.setter("height")
        )

        scroll.add_widget(self.content)

        self.root_layout.add_widget(scroll)

        self.add_widget(self.root_layout)

    def on_pre_enter(self):
        self.refresh()

    def refresh(self):

        self.content.clear_widgets()

        conn = get_db()

        rows = conn.execute("""
            SELECT *
            FROM expenses
            ORDER BY id DESC
        """).fetchall()

        total = conn.execute("""
            SELECT COALESCE(SUM(amount), 0)
            FROM expenses
        """).fetchone()[0]

        conn.close()

        self.total_label.text = (
            f"Total Expenses: {money(total)}"
        )

        for row in rows:

            self.content.add_widget(
                make_label(
                    f"{row['description']}\n"
                    f"Category: {row['category']}\n"
                    f"Amount: {money(row['amount'])}\n"
                    f"Date: {row['expense_date']}\n"
                    f"Payment: {row['payment_method']}",
                    14,
                    False,
                    115
                )
            )

    def add_expense(self, instance):

        content = BoxLayout(
            orientation="vertical",
            spacing=dp(8),
            padding=dp(10)
        )

        fields = []

        for hint in [
            "Date (YYYY-MM-DD)",
            "Expense name",
            "Category",
            "Amount",
            "Notes"
        ]:
            field = make_input(hint)
            fields.append(field)
            content.add_widget(field)

        fields[0].text = datetime.now().strftime("%Y-%m-%d")

        save = Button(
            text="SAVE EXPENSE",
            size_hint_y=None,
            height=dp(48)
        )

        content.add_widget(save)

        popup = Popup(
            title="Add Expense",
            content=content,
            size_hint=(0.92, 0.75)
        )

        def save_expense(instance):

            try:
                amount = float(fields[3].text)

                conn = get_db()

                conn.execute("""
                    INSERT INTO expenses
                    (expense_date, description, category,
                     amount, payment_method, notes)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    fields[0].text,
                    fields[1].text,
                    fields[2].text,
                    amount,
                    "Cash",
                    fields[4].text
                ))

                conn.commit()
                conn.close()

                popup.dismiss()
                self.refresh()

            except:
                show_message(
                    "Error",
                    "Please enter a valid amount."
                )

        save.bind(on_press=save_expense)

        popup.open()


# =========================================================
# PROFIT & LOSS
# =========================================================

class ProfitScreen(BaseScreen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.root_layout = self.main_layout(
            "Profit & Loss"
        )

        scroll = ScrollView()

        self.content = BoxLayout(
            orientation="vertical",
            spacing=dp(15),
            padding=dp(15),
            size_hint_y=None
        )

        self.content.bind(
            minimum_height=self.content.setter("height")
        )

        scroll.add_widget(self.content)

        self.root_layout.add_widget(scroll)

        self.add_widget(self.root_layout)

    def on_pre_enter(self):
        self.refresh()

    def refresh(self):

        self.content.clear_widgets()

        conn = get_db()

        sales = conn.execute("""
            SELECT COALESCE(SUM(total), 0)
            FROM sales
        """).fetchone()[0]

        expenses = conn.execute("""
            SELECT COALESCE(SUM(amount), 0)
            FROM expenses
        """).fetchone()[0]

        conn.close()

        profit = sales - expenses

        self.content.add_widget(
            make_label(
                "FINANCIAL SUMMARY",
                22,
                True,
                60
            )
        )

        self.content.add_widget(
            make_label(
                f"Total Sales\n{money(sales)}",
                19,
                True,
                90
            )
        )

        self.content.add_widget(
            make_label(
                f"Total Expenses\n{money(expenses)}",
                19,
                True,
                90
            )
        )

        self.content.add_widget(
            make_label(
                f"Net Profit / Loss\n{money(profit)}",
                23,
                True,
                110
            )
        )


# =========================================================
# APP
# =========================================================

class BusinessManager(App):

    def build(self):

        setup_database()

        manager = ScreenManager()

        manager.add_widget(
            DashboardScreen(name="dashboard")
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
