import os.path
import re
import sys
import tkinter
import winreg

root = tkinter.Tk()
root.title("CK2/EU4 Installer")
root.geometry("400x300")


def install(target_app_id):
    # レジストリを見て、Steamのインストール先を探す
    # 32bitを見て、なければ64bitのキーを探しに行く。それでもなければそもそもインストールされていないと判断する
    try:
        steam_install_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, "SOFTWARE\\Valve\\Steam")
    except OSError:
        try:
            steam_install_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, "SOFTWARE\\WOW6432Node\\Valve\\Steam")
        except OSError:
            raise Exception("not found steam key.")

    try:
        steam_install_path, key_type = winreg.QueryValueEx(steam_install_key, "InstallPath")
    except FileNotFoundError:
        raise Exception("not include required value")

    steam_install_key.Close()

    if key_type != winreg.REG_SZ:
        raise Exception("invald value")

    # インストールディレクトリにあるsteamapps/appmanifest_[APPID].acfを探す
    steam_apps_path = os.path.join(steam_install_path, "steamapps")
    target_app_acf_path = os.path.join(steam_apps_path, "appmanifest_{}.acf".format(target_app_id))

    # なければ別処理をする必要あり
    if os.path.exists(target_app_acf_path) is False:
        raise Exception("sorry. not implemented")

    # acfファイルにある"installdir" "xxxx"をさがす
    install_dir_pattern = re.compile(r'\s*"installdir"\s+"(.*)')
    game_install_dir_name = None
    with open(target_app_acf_path, 'r') as target_app_acf_file:
        for line in target_app_acf_file:
            result = install_dir_pattern.match(line)
            if result is not None:
                game_install_dir_name = result.group(1).strip("\"")
                break

        if game_install_dir_name is None:
            raise Exception("invalid acf file")

    # パスを確認
    game_install_dir_path = os.path.join(steam_apps_path, "common", game_install_dir_name)

    if os.path.exists(game_install_dir_path) is False:
        raise Exception("not reached install directory")

    print(game_install_dir_path)


# EU4 multibyte dllのインストール
def eu4Func1():
    install(236850)


def ck2Func2():
    install(203770)


labelConfig = {
    'font': ("Helvetica", 16),
    'anchor': 'w',
    'justify': 'left',
    'text': "EU4/CK2 Multibyte DLL Installer",
    'width': 400
}
label = tkinter.Label(root, labelConfig)
label.pack()
eu4installButton = tkinter.Button(root,
                                  text='Install EU4 Multibyte DLL',
                                  command=eu4Func1,
                                  width=400,
                                  font=("Helvetica", 12))
eu4installButton.pack()

ck2InstallButton = tkinter.Button(root,
                                  text='Install CK2 Multibyte DLL',
                                  command=ck2Func2,
                                  width=400,
                                  font=("Helvetica", 12))
ck2InstallButton.pack()

log = tkinter.Message(root,
                      text='aaa',
                      width=400,
                      anchor='w',
                      justify='left')
log.pack()

exitButton = tkinter.Button(root,
                            text='Exit',
                            command=sys.exit,
                            width=400,
                            anchor='s',
                            font=("Helvetica", 12))
exitButton.pack()

root.mainloop()
