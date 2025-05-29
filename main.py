# Import necessary libraries
import os
import sys
import json

from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtCore import QObject, Slot, Signal

# Check if the "users.json" file exists, if not, create an empty one
if not os.path.exists("users.json"):
    with open("users.json", "w") as file:
        json.dump({}, file)


class Backend(QObject):
    # Signals to communicate with the frontend
    signalEmail = Signal(str)           # Signal emitted with the user's email
    signalPassword = Signal(str)        # Signal emitted with the user's password
    signalLogin = Signal(bool)          # Signal emitted to indicate successful login or failed login attempt
    signalBookings = Signal(dict)       # Signal emitted with the user's reservation data

    # Attributes to store user information and reservations
    email = None
    password = None
    bookings = {}

    def __init__(self):
        QObject.__init__(self)

    @Slot(str, str)
    def authenticate(self, email, password):
        """
        Authenticates the user with the provided email and password.

        If the email exists in the database and the password matches,
        signals for successful login and emits the user's email, password,
        and reservations. Otherwise, signals for failed login.

        Args:
            email (str): User's email.
            password (str): User's password.
        """
        with open("users.json", "r") as data:
            database = json.load(data)

        if database.get(email):
            if database[email]["password"] == password:
                # Emit signals for successful login
                self.signalEmail.emit(email)
                self.signalPassword.emit(password)
                self.signalLogin.emit(True)
                self.signalBookings.emit(database[email]["reservations"])

                # Store the user's email, password, and reservations
                self.email = email
                self.password = password
                self.bookings = database[email]["reservations"]

            else:
                # Signal for failed login
                self.signalLogin.emit(False)

    @Slot(str, int, str, str)
    def createAccount(self, name, abn, email, password):
        """
        Creates a new user account with the provided details.

        Adds the user's account information to the database and signals
        for successful login.

        Args:
            name (str): User's name.
            abn (int): User's ABN number.
            email (str): User's email.
            password (str): User's password.
        """
        with open("users.json", "r+") as data:
            database = json.load(data)

            # Validate that all fields are filled
            if not name or not abn or not email or not password:
                # Signal an error message for missing fields
                self.signalLogin.emit(False)
                return

            if len(email) > 30:
                # Signal an error message for exceeding email limit
                self.signalLogin.emit(False)
                return

            if len(password) > 20:
                # Signal an error message for exceeding password limit
                self.signalLogin.emit(False)
                return

            database.update(
                {
                    email: {
                        "password": password,
                        "name": name,
                        "abn": abn,
                        "reservations": {},
                    }
                }
            )

        with open("users.json", "w") as data:
            json.dump(database, data)

        # Signal for successful login
        self.signalLogin.emit(True)

    @Slot(str, str, str, int)
    def book(self, name, startTime, endTime, floor):
        """
        Books a reservation with the provided details.

        Adds the reservation information to the user's reservations,
        signals for updated bookings, and updates the bookings attribute.

        Args:
            name (str): Reservation name.
            startTime (str): Start time of the reservation.
            endTime (str): End time of the reservation.
            floor (int): Floor number for the reservation.
        """
        with open("users.json", "r+") as data:
            database = json.load(data)
            user = database[self.email]
            reservations = user["reservations"]
            reservations.update(
                {
                    name: {
                        "startTime": startTime,
                        "endTime": endTime,
                        "floor": floor,
                    },
                }
            )
            user["reservations"] = reservations
            database[self.email] = user

            # Signal for updated bookings
            self.signalBookings.emit(reservations)
            self.bookings = reservations

        with open("users.json", "w") as data:
            json.dump(database, data)

    @Slot(str)
    def cancel(self, name):
        """
        Cancels a reservation.

        Removes the specified reservation from the user's reservations,
        signals for updated bookings, and updates the bookings attribute.

        Args:
            name (str): Name of the reservation to be canceled.
        """
        with open("users.json", "r+") as data:
            database = json.load(data)
            user = database[self.email]
            del user["reservations"][name]
            database[self.email] = user

            # Signal for updated bookings
            self.signalBookings.emit(user["reservations"])
            self.bookings = user["reservations"]

        with open("users.json", "w") as data:
            json.dump(database, data)


app = QGuiApplication(sys.argv)
backend = Backend()

engine = QQmlApplicationEngine()
engine.quit.connect(app.quit)
engine.rootContext().setContextProperty("backend", backend)
engine.load("interface/pages/Main.qml")

sys.exit(app.exec())
