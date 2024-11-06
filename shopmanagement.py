import mysql.connector
from datetime import datetime
from getpass import getpass
import csv

PRODUCTS_FILE = 'products_backup.csv'  # File name for product backup
SALES_FILE = 'sales_backup.csv'        # File name for sales backup
USER_FILE = 'users.csv'                # File name for user backup

class DatabaseConnection:
    def __init__(self):
        try:
            self.connection = mysql.connector.connect(
                host='localhost',
                user='',   #username  
                password='',    #password
                database='shop_management'  # MySQL database name
            )
            self.cursor = self.connection.cursor()
            self.create_tables()
        except Exception as e:
            print(f"Error: {e}")

    def create_tables(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS users
                                ( user_id INT AUTO_INCREMENT PRIMARY KEY,
                                username VARCHAR(100) NOT NULL UNIQUE,
                                password VARCHAR(100) NOT NULL,
                                role VARCHAR(50) NOT NULL)''')

        self.cursor.execute('''CREATE TABLE IF NOT EXISTS products
                                ( product_id INT AUTO_INCREMENT PRIMARY KEY,
                                name VARCHAR(100) NOT NULL UNIQUE,
                                category VARCHAR(100),
                                price DECIMAL(10, 2),
                                stock_quantity INT
                                )''')

        self.cursor.execute('''CREATE TABLE IF NOT EXISTS sales
                                ( sale_id INT AUTO_INCREMENT PRIMARY KEY,
                                product_id INT,
                                quantity INT,
                                total_amount DECIMAL(10, 2),
                                sale_date DATETIME,
                                FOREIGN KEY (product_id) REFERENCES products(product_id)
                                )''')

        self.connection.commit()

    def execute_query(self, query, params=None):
        self.cursor.execute(query, params)
        self.connection.commit()

    def fetch_all(self, query, params=None):
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def close(self):
        self.cursor.close()
        self.connection.close()


class CSV_files:
    @staticmethod
    def append_to_csv(filename, row):
        with open(filename, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(row)

    @staticmethod
    def write_to_csv(filename, headers, rows):
        with open(filename, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(headers)
            writer.writerows(rows)

class User:
    def __init__(self, username, password, role):
        self.username = username
        self.password = password
        self.role = role

class Admin(User):
    def __init__(self, username, password):
        super().__init__(username, password, role='admin')

    def add_user(self, db, username, password, role):
        query = "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)"
        db.execute_query(query, (username, password, role))
        print(f"User '{username}' added as '{role}'.")

        csv_handler = CSV_files()
        csv_handler.append_to_csv(USER_FILE, [username, password, role])

    @staticmethod
    def verify_admin(db, username, password):
        query = "SELECT * FROM users WHERE username = %s AND password = %s AND role = 'admin'"
        result = db.fetch_all(query, (username, password))
        if result:
            print("Admin verified successfully.")
            return True
        else:
            print("Admin verification failed. Access denied.")
            return False

class Shopkeeper(User):
    def __init__(self, username, password):
        super().__init__(username, password, role='shopkeeper')

class Client(User):
    def __init__(self, username, password):
        super().__init__(username, password, role='client')

class Authentication:
    def register(self, db, username, password, role):
        query = "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)"
        db.execute_query(query, (username, password, role))
        print(f"User '{username}' registered successfully.")

        csv_handler = CSV_files()
        csv_handler.append_to_csv(USER_FILE, [username, password, role])

    def login(self, db, username, password):
        query = "SELECT username, password, role FROM users WHERE username = %s AND password = %s"
        result = db.fetch_all(query, (username, password))
        if result:
            user = result[0]
            if len(user) == 3:
                print(f"Login successful! Welcome {username}.")
                return result  # return user details
        else:
            print("Login failed! Invalid credentials.")
            return None


class Product:
    def __init__(self, product_id, name, category, price, stock_quantity):
        self.product_id = product_id
        self.name = name
        self.category = category
        self.price = price
        self.stock_quantity = stock_quantity

class ProductManager:
    def add_product(self, db, name, category, price, stock_quantity):
        existing_product = db.fetch_all("SELECT * FROM products WHERE name = %s", (name,))
        if existing_product:
            print(f"Product '{name}' already exists.")
        else:
            query = "INSERT INTO products (name, category, price, stock_quantity) VALUES (%s, %s, %s, %s)"
            db.execute_query(query, (name, category, price, stock_quantity))
            print(f"Product '{name}' added successfully.")

            csv_handler = CSV_files()
            csv_handler.append_to_csv(PRODUCTS_FILE, [name, category, price, stock_quantity])

    def view_products(self, db):
        products = db.fetch_all("SELECT * FROM products")
        if not products:
            print("No products available.")
        for product in products:
            print(f"ID: {product[0]}, Name: {product[1]}, Category: {product[2]}, Price: {product[3]}, Stock: {product[4]}")

    def delete_product(self, db, product_id):
        query = "DELETE FROM products WHERE product_id = %s"
        db.execute_query(query, (product_id,))
        print(f"Product with ID '{product_id}' deleted successfully.")
        self.backup_products_to_csv(db)

    def update_stock(self, db, product_id, new_quantity):
        query = "UPDATE products SET stock_quantity = %s WHERE product_id = %s"
        db.execute_query(query, (new_quantity, product_id))
        print(f"Stock updated for product ID '{product_id}'. New quantity: {new_quantity}")
        self.backup_products_to_csv(db)

    def backup_products_to_csv(self, db):
        products = db.fetch_all("SELECT * FROM products")
        csv_handler = CSV_files()
        csv_handler.write_to_csv(PRODUCTS_FILE, ['Product ID', 'Name', 'Category', 'Price', 'Stock'], products)


class Billing:
    def generate_bill(self, db, product_id, quantity):
        product = db.fetch_all("SELECT * FROM products WHERE product_id = %s", (product_id,))
        if not product:
            print("Product not found.")
            return
        product = product[0]  
        if quantity > product[4]: 
            print("Not enough stock available.")
            return

        total_amount = quantity * product[3] 
        query = "INSERT INTO sales (product_id, quantity, total_amount, sale_date) VALUES (%s, %s, %s, %s)"
        sale_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S") 
        db.execute_query(query, (product_id, quantity, total_amount, sale_date))
        # Update stock after sale
        new_stock = product[4] - quantity
        ProductManager().update_stock(db, product_id, new_stock)

        csv_handler = CSV_files()
        csv_handler.append_to_csv(SALES_FILE, [product_id, quantity, total_amount,sale_date])
        print(f"Bill generated for {quantity} unit(s) of '{product[1]}'. Total: ${total_amount:.2f} > {sale_date}")

    def generate_sales_report(self, db):
        query = "SELECT * FROM sales"
        sales = db.fetch_all(query)
        print("Sales Report:")
        for sale in sales:
            print(sale)
        print()

    def backup_sales_to_csv(self, db):
        sales = db.fetch_all("SELECT * FROM sales")
        csv_handler = CSV_files()
        csv_handler.write_to_csv(SALES_FILE, ['Sale ID', 'Product ID', 'Quantity', 'Total Amount', 'Sale Date'], sales)


db = DatabaseConnection()
csv_handler = CSV_files()
while True:
    print("\n=== Shop Management System ===")
    print("1. Admin Registration")
    print("2. Login")
    print("3. Exit")
    choice = input("Enter your choice: ")
    if choice == '1':
        username = input("Enter admin username: ")
        password = getpass("Enter admin password: ")
        if Admin.verify_admin(db, username, password):
            admin = Admin(username, password)
            while True:
                print("\n1. Add a New Admin")
                print("2. Login for Other Purposes")
                print("3. Exit Admin Registration")
                admin_choice = input("Enter your choice: ")

                if admin_choice == '1':
                    new_admin_name = input("Enter new admin username: ")
                    new_admin_password = getpass("Enter new admin password: ")
                    admin.add_user(db, new_admin_name, new_admin_password, 'admin')
                    print(f"New admin '{new_admin_name}' registered successfully.")

                elif admin_choice == '2':
                    username = input("Enter username: ")
                    password = getpass("Enter password: ")
                    auth = Authentication()
                    user = auth.login(db, username, password)
                    if user:
                        (username, password, role) = user[0]
                        if role == 'admin':
                            print(f"\nWelcome Admin {username}!")
                            while True:
                                print("\n1. Add Shopkeeper")
                                print("2. Add Client")
                                print("3. View Products")
                                print("4. Add Product")
                                print("5. Delete Product")
                                print("6. Stock Update")
                                print("7. Generate Sales Report")
                                print("8. Logout")
                                admin_choice = input("Enter your choice: ")

                                if admin_choice == '1':
                                    shopkeeper_name = input("Enter shopkeeper username: ")
                                    shopkeeper_password = getpass("Enter password: ")
                                    admin = Admin(username, password)
                                    admin.add_user(db, shopkeeper_name, shopkeeper_password, 'shopkeeper')

                                elif admin_choice == '2':
                                    client_name = input("Enter client username: ")
                                    client_password = getpass("Enter password: ")
                                    admin = Admin(username, password)
                                    admin.add_user(db, client_name, client_password, 'client')

                                elif admin_choice == '3':
                                    ProductManager().view_products(db)

                                elif admin_choice == '4':
                                    product_name = input("Enter product name: ")
                                    category = input("Enter category: ")
                                    price = float(input("Enter price: "))
                                    stock = int(input("Enter stock quantity: "))
                                    ProductManager().add_product(db, product_name, category, price, stock)

                                elif admin_choice == '5':
                                    product_id = int(input("Enter product ID to delete: "))
                                    ProductManager().delete_product(db, product_id)

                                elif admin_choice == '6':
                                    product_id = int(input("Enter product ID to be updated: "))
                                    new_quantity=int(input("Enter quantity to be updated: "))
                                    ProductManager().update_stock(db,product_id,new_quantity)

                                elif admin_choice == '7':
                                    Billing().generate_sales_report(db)

                                elif admin_choice == '8':
                                    break

                elif admin_choice == '3':
                    break
                else:
                    print("Invalid choice. Please try again.")

    elif choice == '2':
        # Normal login process
        username = input("Enter username: ")
        password = getpass("Enter password: ")
        auth = Authentication()
        user = auth.login(db, username, password)
        if user:
                (username, password, role) = user[0]
                if role == 'shopkeeper':
                    print(f"\nWelcome Shopkeeper {username}!")
                    while True:
                        print("\n1. Generate Bill")
                        print("2. View Products")
                        print("3. Logout")
                        shopkeeper_choice = input("Enter your choice: ")
                        if shopkeeper_choice == '1':
                            product_id = int(input("Enter product ID: "))
                            quantity = int(input("Enter quantity: "))
                            Billing().generate_bill(db, product_id, quantity)
                        elif shopkeeper_choice == '2':
                            ProductManager().view_products(db)
                        elif shopkeeper_choice == '3':
                            break

                elif role == 'client':
                    print(f"\nWelcome Client {username}!")
                    while True:
                        print("\n1. View Products")
                        print("2. Logout")
                        client_choice = input("Enter your choice: ")
                        if client_choice == '1':
                            ProductManager().view_products(db)
                        elif client_choice == '2':
                            break       

    elif choice == '3':
        print("Exiting system...")
        db.close()
        break                                    
