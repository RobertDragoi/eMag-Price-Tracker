from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import sys
import platform
import sqlite3
import requests
import smtplib
import ssl
from bs4 import BeautifulSoup
import time
# import windows
from MainWindow import Ui_MainWindow
from TrackerWindow import Ui_TrackerWindow
from DialogWindow import Ui_DialogWindow
from Database import DatabaseManager
from SelectWindow import Ui_SelectWindow


class MainWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.window = Ui_MainWindow()
        self.window.setupUi(self)
        self.show()
        ####################################

        self.Tracker_Window = TrackerWindow()

        ####################################
        self.window.AccesButton.clicked.connect(self.show_tracker_window)
        self.window.helpButton.installEventFilter(self)

    def show_tracker_window(self):
        if len(self.window.emailText.text()) == 0:
            QMessageBox.about(self, "eMag Price Tracker",
                              "Please enter a valid email address!")
        else:
            self.hide()
            self.Tracker_Window.email = self.window.emailText.text()
            self.Tracker_Window.show()

    def eventFilter(self, object, event):
        if object == self.window.helpButton and event.type() == QtCore.QEvent.HoverEnter:
            QMessageBox.about(self, "eMag Price Tracker",
                              "Enter your valid email and start tracking. Add links for your products, create a preset, load it, and start tracking!")
        return False


class SelectWindow(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        self.window = Ui_SelectWindow()
        self.window.setupUi(self)


class DialogWindow(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        self.window = Ui_DialogWindow()
        self.window.setupUi(self)


class pricetracker_thread(QThread):
    def __init__(self, products, Notif_List, email):
        super(pricetracker_thread, self).__init__()
        self.threadactive = True
        self.products = products
        self.Notif_List = Notif_List
        self.email = email

    @pyqtSlot()
    def run(self):
        self.check_price(self.products, self.Notif_List, self.email)

    def number(self, string):
        number = 0
        for letter in string:
            if letter.isalnum() == True:
                number = number*10+int(letter, 10)
        return number

    def send_mail(self, message, email):
        context = ssl.create_default_context()
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.ehlo()
        server.starttls(context=context)
        server.ehlo()
        server.login("emagpricetracker@gmail.com", "YAMAsiro12")
        server.sendmail("emagpricetracker@gmail.com", email, message)

    def initialize_prices(self, products):
        # initialize the prices
        previous_prices = [x[1] for x in products]
        links = [x[0] for x in products]
        header = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36"}
        for i in range(0, len(links)):
            page = requests.get(str(links[i]), headers=header)
            main = BeautifulSoup(page.content, 'html.parser')
            price = main.find(class_="product-new-price").get_text()
            price = price.strip()
            price = self.number(price[0:len(price)-6])
            previous_prices[i] = price
        db_manager = DatabaseManager('Database.db')
        db_manager.check_database()
        cursor = db_manager.conn.cursor()
        for i in range(0, len(previous_prices)):
            cursor.execute(
                "UPDATE Products SET previous_price =? WHERE link=?", (previous_prices[i], links[i]))
        db_manager.conn.commit()
        db_manager.close_connection()

    def check_price(self, products, Notif_List, email):

        header = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36"}
        # initialize the prices
        previous_prices = [x[1] for x in products]
        links = [x[0] for x in products]
        if 0 in previous_prices:
            self.initialize_prices(products)
        # checking the prices every 900sec
        db_manager = DatabaseManager('Database.db')
        db_manager.check_database()
        cursor = db_manager.conn.cursor()
        while True:
            for i in range(0, len(links)):
                page = requests.get(links[i], headers=header)
                main = BeautifulSoup(page.content, 'html.parser')
                price = main.find(class_="product-new-price").get_text()
                name = main.find(class_="page-title").get_text()
                name = name.strip()
                price = price.strip()
                price = self.number(price[0:len(price)-6])
                if price < previous_prices[i]:
                    aux = previous_prices[i]-price
                    print_message = "Price has been dropped by {0} lei for product {1}".format(
                        aux, name)
                    previous_prices[i] = price
                    subject = "Price was decreased by {0} lei for product {1}".format(
                        aux, name)
                    body = "Check the link {}".format(links[i])
                    message = f"Subject: {subject}\n\n{body}"
                    self.send_mail(message, email)
                    ########################################
                    cursor.execute(
                        "UPDATE Products SET previous_price =? WHERE link=?", (previous_prices[i], links[i]))
                    Notif_List.addItem(QListWidgetItem(print_message))
                    db_manager.conn.commit()
                else:
                    if price < previous_prices[i]:
                        print_message = "Price was increased by {0} lei for product {1}".format(price-previous_prices[i],
                                                                                                name)
                        Notif_List.addItem(QListWidgetItem(print_message))
                    else:
                        print_message = "Price it's the same for product {0}".format(
                            name)
                        Notif_List.addItem(QListWidgetItem(print_message))
                print(print_message)
            time.sleep(300)

    def stop(self):
        self.threadactive = False
        self.terminate()


class TrackerWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.window = Ui_TrackerWindow()
        self.window.setupUi(self)
        ####################################
        self.Dialog_Window = DialogWindow()
        self.Select_Window = SelectWindow()
        self.Select_Window2 = SelectWindow()
        ####################################
        self.window.AddButton.clicked.connect(self.add_Item)
        self.window.SaveButton.clicked.connect(self.show_popup)
        self.window.LoadButton.clicked.connect(self.show_Presets)
        self.window.DeleteButton.clicked.connect(self.show_Presets2)
        self.Dialog_Window.window.SaveButton.clicked.connect(
            self.save_Preset)
        self.Select_Window.window.Button.clicked.connect(self.load_Preset)
        self.Select_Window2.window.Button.clicked.connect(self.delete_Preset)
        self.preset_is_loaded = False
        ####################################

    def add_Item(self):
        text = self.window.Link_Input.text()
        if len(text) == 0:
            QMessageBox.about(self, "eMag Price Tracker",
                              "You must add the products URL!")
        else:
            item = QListWidgetItem(text)
            self.window.Tracker_List.addItem(item)
            widget = QtWidgets.QWidget(self.window.Tracker_List)
            button = QtWidgets.QPushButton(widget)
            button.setText("X")
            button.setFixedSize(25, 25)
            button.clicked.connect(lambda: self.remove_Item(item))
            layout = QtWidgets.QHBoxLayout(widget)
            layout.setContentsMargins(0, 1, 1, 0)
            layout.addStretch()
            layout.addWidget(button)
            self.window.Tracker_List.setItemWidget(item, widget)
            self.window.Link_Input.clear()

    def remove_Item(self, item):
        self.window.Tracker_List.takeItem(self.window.Tracker_List.row(item))

    def show_popup(self):
        if self.window.Tracker_List.count() == 0:
            QMessageBox.about(self, "eMag Price Tracker",
                              "You must add at least one product!")
        else:
            self.Dialog_Window.show()

    def get_Presets(self):
        db_manager = DatabaseManager('Database.db')
        db_manager.check_database()
        cursor = db_manager.conn.cursor()
        cursor.execute("SELECT DISTINCT(preset) FROM Products")
        list = cursor.fetchall()
        list = [x[0] for x in list]
        return list

    def show_Presets(self):
        self.Select_Window.window.List.clear()
        if self.preset_is_loaded == True:
            self.thread.stop()

        self.Select_Window.window.Button.setText("Load Preset")
        self.Select_Window.show()
        list = self.get_Presets()
        for i in range(0, len(list)):
            item = QListWidgetItem(str(list[i]))
            self.Select_Window.window.List.addItem(item)

    def show_Presets2(self):
        self.Select_Window2.window.List.clear()
        if self.preset_is_loaded == True:
            QMessageBox.about(self, "eMag Price Tracker",
                              "Preset is already loaded")
        else:
            self.Select_Window2.window.Button.setText("Delete Preset")
            self.Select_Window2.show()
            list = self.get_Presets()
            for i in range(0, len(list)):
                item = QListWidgetItem(str(list[i]))
                self.Select_Window2.window.List.addItem(item)

    def save_Preset(self):
        if len(self.Dialog_Window.window.Name_Input.text()) == 0:
            QMessageBox.about(self, "eMag Price Tracker",
                              "You must choose a name for the preset!")
        list = self.get_Presets()
        if str(self.Dialog_Window.window.Name_Input.text()) in list:
            QMessageBox.about(self, "eMag Price Tracker",
                              "The preset already exists!")
        else:
            db_manager = DatabaseManager('Database.db')
            if db_manager.check_database():
                cursor = db_manager.conn.cursor()
            cursor.execute("""create table if not exists Products(
                link text,
                preset text,
                previous_price integer
            )""")

            for i in range(self.window.Tracker_List.count()):
                cursor.execute("""INSERT INTO Products VALUES(?,?,?)""", (str(
                    self.window.Tracker_List.item(i).text()), str(self.Dialog_Window.window.Name_Input.text()), 0))
            cursor.execute("SELECT * FROM Products")

            print(cursor.fetchall())
            db_manager.conn.commit()
            db_manager.close_connection()
            self.window.Tracker_List.clear()
            self.Dialog_Window.hide()

    def load_Preset(self):
        self.window.Notif_List.clear()
        preset_name = self.Select_Window.window.List.currentItem().text()
        db_manager = DatabaseManager('Database.db')
        db_manager.check_database()
        cursor = db_manager.conn.cursor()
        cursor.execute(
            "SELECT link,previous_price FROM Products WHERE preset=?", (preset_name,))
        self.Select_Window.hide()
        if str(preset_name) is not None:
            self.window.Status_Label.setText(str(preset_name)+" loaded!")
        #########################################
        self.start_thread(cursor.fetchall(),
                          self.window.Notif_List, self.email)
        self.preset_is_loaded = True

    def start_thread(self, products, notif_list, email):
        print(email)
        self.thread = pricetracker_thread(products, notif_list, email)
        self.thread.setTerminationEnabled(True)
        self.thread.start()

    def stop_thread(self):
        self.thread.stop()

    def delete_Preset(self):
        preset_name = self.Select_Window2.window.List.currentItem().text()
        db_manager = DatabaseManager('Database.db')
        db_manager.check_database()
        cursor = db_manager.conn.cursor()
        cursor.execute("DELETE FROM Products WHERE preset=?", (preset_name,))
        cursor.execute("SELECT * FROM Products")
        print(cursor.fetchall())
        db_manager.conn.commit()
        db_manager.close_connection()
        self.Select_Window2.hide()
    ####################################################


app = QApplication(sys.argv)
Main_Window = MainWindow()
sys.exit(app.exec_())
