import pes2021_server_plugin

def register_user(username, password):
    pes2021_server_plugin.pes2021_server_plugin_register_user(username, password)

def login_user(username, password):
    pes2021_server_plugin.pes2021_server_plugin_login_user(username, password)

def get_users():
    return pes2021_server_plugin.pes2021_server_plugin_get_users()

def get_user_info(username):
    return pes2021_server_plugin.pes2021_server_plugin_get_user_info(username)

def main():
    print("Административен панел")
    print("1. Регистрация на администратор")
    print("2. Логин на администратор")
    print("3. Списък на всички регистрирани администратори")
    print("4. Профил на администратор")

    choice = input("Изберете опция: ")

    if choice == "1":
        username = input("Въведете потребителско име: ")
        password = input("Въведете парола: ")
        register_user(username, password)
    elif choice == "2":
        username = input("Въведете потребителско име: ")
        password = input("Въведете парола: ")
        login_user(username, password)
    elif choice == "3":
        users = get_users()
        for user in users:
            print(user)
    elif choice == "4":
        username = input("Въведете потребителско име: ")
        user_info = get_user_info(username)
        print(user_info)

if __name__ == "__main__":
    main()
