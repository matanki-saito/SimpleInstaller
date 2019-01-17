import os.path
import re
import sys
import tkinter
import urllib.request
import winreg
import zipfile
from tkinter import messagebox

root = tkinter.Tk()
root.title("CK2/EU4 Multibyte Installer")
root.geometry("400x300")


def install(install_dir_path, target_zip_url):
    urllib.request.urlretrieve(target_zip_url, 'tmp__multibytedllset.zip')

    print("download success")

    with zipfile.ZipFile("tmp__multibytedllset.zip") as existing_zip:
        existing_zip.extractall(install_dir_path)

    os.remove("tmp__multibytedllset.zip")


def get_game_install_dir_path(target_app_id):
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

    # デフォルトのsteamappsフォルダを探す
    steam_apps_path = os.path.join(steam_install_path, "steamapps")
    if os.path.exists(steam_apps_path) is False:
        raise Exception("not find steamapps folder")

    # acfがあるフォルダを列挙
    acf_dir_paths = [steam_apps_path]
    acf_dir_paths.extend(get_lib_folders_from_vdf(steam_apps_path))

    # 各ディレクトリについて処理
    game_install_dir_path = None
    for dir_path in acf_dir_paths:
        game_install_dir_path = get_game_install_dir(dir_path, target_app_id)
        if game_install_dir_path is None:
            print("not find target acf...")
            continue
        else:
            print("find target acf")
            break

    if game_install_dir_path is None:
        raise Exception("not find game install dir")

    return game_install_dir_path


def get_game_install_dir(dir_path, target_app_id):
    # インストールディレクトリにあるsteamapps/appmanifest_[APPID].acfを探す
    target_app_acf_path = os.path.join(dir_path, "appmanifest_{}.acf".format(target_app_id))

    # なければ終了
    if os.path.exists(target_app_acf_path) is False:
        return None

    # acfファイルにある"installdir" "xxxx"をさがす
    install_dir_pattern = re.compile(r'\s*"installdir"\s+"(.*)')
    game_install_dir_name = None
    with open(target_app_acf_path, 'r') as target_app_acf_file:
        print("open file:" + target_app_acf_file.name)
        for line in target_app_acf_file:
            result = install_dir_pattern.match(line)
            if result is not None:
                game_install_dir_name = result.group(1).strip("\"")
                break

        if game_install_dir_name is None:
            raise Exception("invalid acf file")

    # パスを確認
    game_install_dir_path = os.path.join(dir_path, "common", game_install_dir_name)

    if os.path.exists(game_install_dir_path) is False:
        raise Exception("not reached install directory")

    return game_install_dir_path


def get_lib_folders_from_vdf(steam_apps_path):
    # vdfファイルを探す
    library_folders_vdf_path = os.path.join(steam_apps_path, "libraryfolders.vdf")
    if os.path.exists(library_folders_vdf_path) is False:
        raise Exception("not find libraryfolders.vdf")

    # vdfファイルにある"[数字]" "xxxx"をさがす
    install_dir_pattern = re.compile(r'\s*"[0-9]+"\s+"(.*)')
    game_libs_paths = []
    with open(library_folders_vdf_path, 'r') as target_vdf_file:
        print("open file:" + target_vdf_file.name)
        for line in target_vdf_file:
            result = install_dir_pattern.match(line)
            if result is not None:
                game_libs_paths.append(os.path.join(result.group(1).strip("\"").replace("\\\\", "\\"), "steamapps"))

    return game_libs_paths


def installer(app_id, target_zip):
    try:
        install_dir_path = get_game_install_dir_path(app_id)
        print(install_dir_path)

        install(install_dir_path, target_zip)
        print("success")

        messagebox.showinfo("Success", "Install success!")

    except Exception as exp:
        messagebox.showerror("Error", exp.args[0])


label = tkinter.Label(root,
                      font=("Helvetica", 16),
                      anchor='w',
                      justify='left',
                      text="EU4/CK2 Multibyte DLL Installer",
                      width=400)
label.pack()

eu4installButton = tkinter.Button(root,
                                  text='Install EU4 Multibyte DLL',
                                  command=lambda x=236850,
                                                 y="https://github.com/matanki-saito/SimpleInstaller/files/2769846/eu4.zip"
                                  : installer(x, y),
                                  width=400,
                                  font=("Helvetica", 12))
eu4installButton.pack()

ck2InstallButton = tkinter.Button(root,
                                  text='Install CK2 Multibyte DLL',
                                  command=lambda x=203770,
                                                 y="https://github.com/matanki-saito/SimpleInstaller/files/2769845/ck2.zip"
                                  : installer(x, y),
                                  width=400,
                                  font=("Helvetica", 12))
ck2InstallButton.pack()

exitButton = tkinter.Button(root,
                            text='Exit',
                            command=sys.exit,
                            width=400,
                            anchor='s',
                            font=("Helvetica", 12))
exitButton.pack()

root.mainloop()
