import re
from collections import UserDict
from datetime import datetime, timedelta, date
import pickle

class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)

class Name(Field):
    def __init__(self, value):
        if not value:
            raise ValueError("Please enter the name.")
        super().__init__(value)

class Phone(Field):
    def __init__(self, value):
        # Перевірка, чи номер телефону складається з 10 цифр
        if not re.match(r'^\d{10}$', value):
            raise ValueError("Phone number must be exactly 10 digits.")
        super().__init__(value)

class Birthday(Field):
    def __init__(self, value):
        try:
            datetime.strptime(value, "%d.%m.%Y")
        except ValueError:
            raise ValueError("birthday format must be DD.MM.YYYY")
        super().__init__(value)

class Record:
    def __init__(self, name, birthday=None):
        self.name = Name(name)
        self.phones = []
        self.birthday = Birthday(birthday) if birthday else None


    def add_phone(self, phone):
        self.phones.append(Phone(phone))
        
    def find_phone(self, phone):
        for p in self.phones:
            if p.value == phone:
                return p
        return None
    
    def remove_phone(self, phone):
        phone_obj = self.find_phone(phone)
        if phone_obj:
            self.phones.remove(phone_obj)
            return True
        return False

    def edit_phone(self, old_phone, new_phone):
        old_phone_obj = self.find_phone(old_phone)
        if not old_phone_obj:
            raise ValueError(f"Phone number {old_phone} not found.")
        self.add_phone(new_phone)
        self.remove_phone(old_phone)

    def add_birthday(self, birthday):
        self.birthday = Birthday(birthday)

    def __str__(self):
        return f"Contact name: {self.name.value}, phones: {'; '.join(p.value for p in self.phones)}"

class AddressBook(UserDict):
    def add_record(self, record):
        self.data[record.name.value] = record

    def delete(self, name):
        if name in self.data:
            del self.data[name]
            return True
        return False

    def find(self, name):
        return self.data.get(name, None)

    def __str__(self):
        return "\n".join(str(record) for record in self.data.values())
    
    def _adjust_for_weekend(self, birthday):
            if birthday.weekday() >= 5: 
                return self._find_next_weekday(birthday)
            return birthday
    
    def _find_next_weekday(self, start_date):
            days_ahead = 0
            if start_date.weekday() == 5:
                days_ahead = 2
            elif start_date.weekday() == 6:
                days_ahead = 1
            return start_date + timedelta(days=days_ahead)

    def get_upcoming_birthdays(self, days=7):
        upcoming_birthdays = []
        today = date.today()

        for record in self.data.values():
            if record.birthday:
                birth_day = datetime.strptime(record.birthday.value, "%d.%m.%Y").date()
                birthday_this_year = birth_day.replace(year=today.year)

                if birthday_this_year < today:
                    birthday_this_year = birth_day.replace(year=today.year + 1)

                if 0 <= (birthday_this_year - today).days <= days:
                    birthday_this_year = self._adjust_for_weekend(birthday_this_year)
                    upcoming_birthdays.append({
                        "name": record.name.value,
                        "birthday": birthday_this_year.strftime("%Y-%m-%d")
                    })
        return upcoming_birthdays
    
def save_data(book, filename="address_book.pkl"):
    with open(filename, "wb") as f:
        pickle.dump(book, f)

def load_data(filename="address_book.pkl"):
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return AddressBook()
    
def input_error(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError:
            return "Give me name and phone please."
        except KeyError:
            return "Contact doesn't exist."
        except IndexError:
            return "Enter the argument for the command"
        except AttributeError:
            return "Invalid contact."
        except Exception as e:
            return f"An unexpected error: {e}"
    return inner

@input_error
def add_contact(args, book: AddressBook):
    name, phone, *_ = args
    record = book.find(name)
    message = "Contact updated."
    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Contact added."
    if phone:
        record.add_phone(phone)
    return message

@input_error
def change_phone(args, book: AddressBook):
    name, old_phone, new_phone = args
    record = book.find(name)
    record.edit_phone(old_phone, new_phone)
    return f"Phone number for {name} changed from {old_phone} to {new_phone}"

@input_error
def show_phone(args, book: AddressBook):
    name = args[0]
    record = book.find(name)
    return f"{name}'s phones: {', '.join(p.value for p in record.phones)}"

@input_error
def all_contacts(args, book: AddressBook):
    if not book.data:
        return "No contacts available."
    return "\n".join(str(record) for record in book.data.values())

@input_error
def add_birthday(args, book):
    name, birthday = args
    record = book.find(name)
    if not record:
        return "Contact doesn't exist."
    record.add_birthday(birthday)
    return f"Birthday {birthday} added for {name}"

@input_error
def show_birthday(args, book):
    name = args[0]
    record = book.find(name)
    return f"{name}'s birthday is on {record.birthday.value}"

@input_error
def birthdays(args, book):
    upcoming = book.get_upcoming_birthdays(7)
    if not upcoming:
        return "No upcoming birthdays in the next week."
    return "\n".join([f"{entry['name']} has a birthday on {entry['birthday']}" for entry in upcoming])
    
def parse_input(user_input):
    parts = user_input.strip().split()
    if not parts:
        return None
    command = parts[0].lower()
    return command, parts[1:]

def main():
    book = load_data()
    print("Welcome to the assistant bot!")
    while True:
        user_input = input("Enter a command: ").strip()
        if not user_input:
            print("Please enter the command:")
            continue

        command, args = parse_input(user_input)

        if command in ["close", "exit"]:
            save_data(book)
            print("Good bye!")
            break

        elif command == "hello":
            print("How can I help you?")

        elif command == "add":
            result = add_contact(args, book)
            print(result)

        elif command == "change":
            result = change_phone(args, book)
            print(result)

        elif command == "phone":
            result = show_phone(args, book)
            print(result)

        elif command == "all":
            result = all_contacts(args, book)
            print(result)

        elif command == "add-birthday":
            result = add_birthday(args, book)
            print(result)

        elif command == "show-birthday":
            result = show_birthday(args, book)
            print(result)

        elif command == "birthdays":
            result = birthdays(args, book)
            print(result)
            
        else:
            print("Invalid command.")

if __name__ == "__main__":
    main()