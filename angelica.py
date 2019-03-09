import os.path
import re
import subprocess as sb
import tempfile
import tkinter
import tkinter.ttk as ttk
import urllib.request
import winreg
import zipfile
from os.path import join as __
from tkinter import messagebox

from github_tool import download_asset_from_github
from loca import _


def install(install_dir_path, target_zip_url, final_check_file):
    # 最終チェックファイルがあるかを確認する
    if os.path.exists(__(install_dir_path, final_check_file)) is False:
        raise Exception(_('ERR_NOT_EXIST_FINAL_CHECK_FILE'))

    path, headers = urllib.request.urlretrieve(target_zip_url)
    with zipfile.ZipFile(path) as existing_zip:
        existing_zip.extractall(install_dir_path)


def install_downloader(target_repository, install_dir_path):
    asset_file_path = download_asset_from_github(
        repository_author=target_repository.get("author"),
        repository_name=target_repository.get("name"),
        out_file_path=__(tempfile.mkdtemp(), "a.zip")
    )
    with zipfile.ZipFile(asset_file_path) as existing_zip:
        existing_zip.extractall(install_dir_path)


def get_game_install_dir_path(target_app_id):
    # レジストリを見て、Steamのインストール先を探す
    # 32bitを見て、なければ64bitのキーを探しに行く。それでもなければそもそもインストールされていないと判断する
    try:
        steam_install_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, "SOFTWARE\\Valve\\Steam")
    except OSError:
        try:
            steam_install_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, "SOFTWARE\\WOW6432Node\\Valve\\Steam")
        except OSError:
            raise Exception(_("ERR_NOT_FIND_STEAM_REGKEY"))

    try:
        steam_install_path, key_type = winreg.QueryValueEx(steam_install_key, "InstallPath")
    except FileNotFoundError:
        raise Exception(_("ERR_NOT_FIND_INSTALLPATH_IN_STEAM_REGKEY"))

    steam_install_key.Close()

    # 基本問題ないと思うが念の為
    if key_type != winreg.REG_SZ:
        raise Exception("invald value")

    # デフォルトのsteamappsフォルダを探す
    steam_apps_path = __(steam_install_path, "steamapps")
    if os.path.exists(steam_apps_path) is False:
        raise Exception(_("ERR_NOT_EXIST_DEFAULT_STEAMAPPS_DIR"))

    # acfがあるフォルダを列挙
    acf_dir_paths = [steam_apps_path]
    acf_dir_paths.extend(get_lib_folders_from_vdf(steam_apps_path))

    # 各ディレクトリについて処理
    game_install_dir_path = None
    for dir_path in acf_dir_paths:
        game_install_dir_path = get_game_install_dir(dir_path, target_app_id)
        if game_install_dir_path is None:
            continue
        else:
            break

    if game_install_dir_path is None:
        raise Exception(_("ERR_NOT_FIND_TARGET_GAME_ON_YOUR_PC"))

    return game_install_dir_path


def get_game_install_dir(dir_path, target_app_id):
    # インストールディレクトリにあるsteamapps/appmanifest_[APPID].acfを探す
    target_app_acf_path = __(dir_path, "appmanifest_{}.acf".format(target_app_id))

    # なければ終了
    if os.path.exists(target_app_acf_path) is False:
        return None

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
            raise Exception(_("ERR_INVALID_ACF"))

    # パスを確認
    game_install_dir_path = __(dir_path, "common", game_install_dir_name)

    if os.path.exists(game_install_dir_path) is False:
        raise Exception(_("ERR_NOT_EXIST_GAME_INSTALL_DIR"))

    return game_install_dir_path


def get_lib_folders_from_vdf(steam_apps_path):
    # vdfファイルを探す
    library_folders_vdf_path = __(steam_apps_path, "libraryfolders.vdf")
    if os.path.exists(library_folders_vdf_path) is False:
        raise Exception(_("ERR_NOT_FIND_LIBRARYFOLDERS_VDF"))

    # vdfファイルにある"[数字]" "xxxx"をさがす
    install_dir_pattern = re.compile(r'\s*"[0-9]+"\s+"(.*)')
    game_libs_paths = []
    with open(library_folders_vdf_path, 'r') as target_vdf_file:
        for line in target_vdf_file:
            result = install_dir_pattern.match(line)
            if result is not None:
                game_libs_paths.append(__(result.group(1).strip("\"").replace("\\\\", "\\"), "steamapps"))

    return game_libs_paths


def install_key_file(save_file_path, mod_title, key_file_path):
    with open(save_file_path, encoding="utf-8", mode='w') as fw:
        fw.write("\n".join([
            mod_title,
            key_file_path
        ]))


def dll_installer(app_id, target_zip, final_check_file):
    try:
        install_dir_path = get_game_install_dir_path(app_id)

        install(install_dir_path, target_zip, final_check_file)

        messagebox.showinfo(_('SUCCESS_BOX_TITLE'), _('SUCCESS_BOX_MESSAGE'))

    except Exception as exp:
        messagebox.showerror(_('ERROR_BOX_TITLE'), _('ERROR_BOX_MESSAGE') + ":\n" + exp.args[0])


def mod_installer(app_id, target_repository, key_file_name, game_dir_name, key_ids):
    try:
        # My Documents を環境変数から見つける
        install_game_dir_path = __(os.getenv("HOMEDRIVE"),
                                   os.getenv("HOMEPATH"),
                                   "Documents",
                                   "Paradox Interactive",
                                   game_dir_name)

        # exeを見つける
        install_dll_dir_path = get_game_install_dir_path(app_id)

        # Modダウンローダーを配置
        install_downloader(target_repository=target_repository,
                           install_dir_path=install_game_dir_path)

        # keyファイルを保存
        os.makedirs(__(install_game_dir_path, 'claes.key'), exist_ok=True)
        for tuple_data in key_ids:
            install_key_file(save_file_path=__(install_game_dir_path, "claes.key", tuple_data[1] + ".key"),
                             mod_title=tuple_data[0],
                             key_file_path=__(install_dll_dir_path, key_file_name))

        # Modダウンローダーを起動
        sb.call(__(install_game_dir_path, "claes.exe"))

        messagebox.showinfo(_('SUCCESS_BOX_TITLE'), _('SUCCESS_BOX_MESSAGE'))

    except Exception as exp:
        messagebox.showerror(_('ERROR_BOX_TITLE'), _('ERROR_BOX_MESSAGE') + ":\n" + exp.args[0])


def about():
    messagebox.showinfo(_('ABOUT_BOX_TITLE'), _('ABOUT_BOX_MESSAGE'))


if __name__ == '__main__':
    root = tkinter.Tk()
    root.title(_('TITLE'))

    root.geometry("300x300")

    # ノートブック
    style = ttk.Style()
    style.configure("BW.TLabel", foreground="black", background="white")
    nb = ttk.Notebook(width=300, height=200, style="BW.TLabel")

    # タブの作成
    tab1 = tkinter.Frame(nb, pady=0, relief='flat')
    tab2 = tkinter.Frame(nb, pady=0, relief='flat')
    tab3 = tkinter.Frame(nb, pady=0, relief='flat')

    nb.add(tab1, text=_('TAB_MBDLL'), padding=0)
    nb.add(tab2, text=_('TAB_JPMOD'), padding=0)
    nb.add(tab3, text=_('TAB_INFO'), padding=0)
    nb.pack(expand=True, fill='both')

    # Install DLL
    frame1_1 = tkinter.Frame(tab1, pady=0, relief='flat')
    frame1_1.pack(expand=True, fill='both')

    dl_url = "https://github.com/matanki-saito/SimpleInstaller/"

    # EU4
    eu4DllInstallButton = tkinter.Button(frame1_1,
                                         activebackground='#AF9F8E',
                                         background='#AF9F8E',
                                         relief='flat',
                                         text=_('INSTALL_EU4_MBDLL'),
                                         command=lambda
                                         : dll_installer(236850,
                                                         dl_url + "2769846/eu4.zip",
                                                         'eu4.exe'),
                                         font=("Helvetica", 12))
    eu4DllInstallButton.pack(expand=True, fill='both')

    # CK2
    ck2DllInstallButton = tkinter.Button(frame1_1,
                                         activebackground='#BFBD9F',
                                         background='#BFBD9F',
                                         relief='flat',
                                         text=_('INSTALL_CK2_MBDLL'),
                                         command=lambda
                                         : dll_installer(203770,
                                                         dl_url + "2769845/ck2.zip",
                                                         'ck2game.exe'),
                                         font=("Helvetica", 12))
    ck2DllInstallButton.pack(expand=True, fill='both')

    # Install downloader and jpmod
    frame1_2 = tkinter.Frame(tab2, pady=0)
    frame1_2.pack(expand=True, fill='both')

    # EU4
    eu4ModInstallButton = tkinter.Button(frame1_2,
                                         activebackground='#7A7069',
                                         background='#7A7069',
                                         relief='flat',
                                         text=_('INSTALL_EU4_JPMOD'),
                                         command=lambda
                                         : mod_installer(app_id=236850,
                                                         target_repository={
                                                             "author": "matanki-saito",
                                                             "name": "moddownloader"
                                                         },
                                                         key_file_name='eu4.exe',
                                                         game_dir_name="Europa Universalis IV",
                                                         key_ids=[]),
                                         font=("Helvetica", 12))
    eu4ModInstallButton.pack(expand=True, fill='both')

    # CK2
    ck2ModInstallButton = tkinter.Button(frame1_2,
                                         activebackground='#504D3E',
                                         background='#504D3E',
                                         relief='flat',
                                         text=_('INSTALL_CK2_JPMOD'),
                                         command=lambda
                                         : mod_installer(app_id=203770,
                                                         target_repository={
                                                             "author": "matanki-saito",
                                                             "name": "moddownloader"
                                                         },
                                                         key_file_name='ck2game.exe',
                                                         game_dir_name="Crusader Kings II",
                                                         key_list_url="ck2mods.json"),
                                         font=("Helvetica", 12))
    ck2ModInstallButton.pack(expand=True, fill='both')

    # Install MOD downloader and jpmod
    frame1_3 = tkinter.Frame(tab3, pady=0)
    frame1_3.pack(expand=True, fill='both')

    aboutButton = tkinter.Button(frame1_3,
                                 background='#443648',
                                 fg='white',
                                 text=_('ABOUT'),
                                 command=about,
                                 height='1',
                                 font=("Helvetica", 12))
    aboutButton.pack(expand=True, fill='both')
    root.mainloop()
