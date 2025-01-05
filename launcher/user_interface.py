import pes2021_server_plugin

def get_server_status():
    return pes2021_server_plugin.pes2021_server_plugin_get_server_status()

def get_active_players():
    return pes2021_server_plugin.pes2021_server_plugin_get_active_players()

def get_user_info(username):
    return pes2021_server_plugin.pes2021_server_plugin_get_user_info(username)

def main():
    print("Потребителски интерфейс")
    print("1. Информация за състоянието на сървъра")
    print("2. Списък на активните играчи")
    print("3. Профил на потребителя")

    choice = input("Изберете опция: ")

    if choice == "1":
        server_status = get_server_status()
        print(server_status)
    elif choice == "2":
        active_players = get_active_players()
        for player in active_players:
            print(player)
    elif choice == "3":
        username = input("Въведете потребителско име: ")
        user_info = get_user_info(username)
        print(user_info)

if __name__ == "__main__":
    main()
