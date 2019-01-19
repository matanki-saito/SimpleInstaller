import locale
import os.path
import re
import sys
import tkinter
import urllib.request
import winreg
import zipfile
from tkinter import messagebox
import threading

# gettextなどを使うのが正解だろうが、面倒なので
def get_language_windows(system_lang=True):
    """Get language code based on current Windows settings.
    @return: list of languages.
    """
    try:
        import ctypes
    except ImportError:
        return [locale.getdefaultlocale()[0]]
    # get all locales using windows API
    lcid_user = ctypes.windll.kernel32.GetUserDefaultLCID()
    lcid_system = ctypes.windll.kernel32.GetSystemDefaultLCID()
    if system_lang and lcid_user != lcid_system:
        lcids = [lcid_user, lcid_system]
    else:
        lcids = [lcid_user]
    return list(filter(None, [locale.windows_locale.get(i) for i in lcids]))[0] or None


loc = get_language_windows()
loca_dic = {
    'EXIT': {
        'default': 'Exit',
        'ja_JP': '終了'
    },
    'ABOUT': {
        'default': 'About',
        'ja_JP': 'このソフトについて'
    },
    'INSTALL_CK2_MBDLL': {
        'default': 'Install CK2 Multibyte DLL',
        'ja_JP': 'CK2日本語化DLLをインストール'
    },
    'INSTALL_EU4_MBDLL': {
        'default': 'Install EU4 Multibyte DLL',
        'ja_JP': 'EU4日本語化DLLをインストール'
    },
    'TITLE': {
        'default': 'CK2/EU4 Multibyte Installer',
        'ja_JP': 'CK2/EU4 日本語化インストーラー'
    },
    'SUCCESS_BOX_MESSAGE': {
        'default': 'Install Success',
        'ja_JP': 'インストール成功！'
    },
    'SUCCESS_BOX_TITLE': {
        'default': 'success',
        'ja_JP': '成功！'
    },
    'ABOUT_BOX_MESSAGE': {
        'default': 'URL: https://github.com/matanki-saito/SimpleInstaller',
        'ja_JP': 'インストーラー最新版配布元: https://github.com/matanki-saito/SimpleInstaller'
    },
    'ABOUT_BOX_TITLE': {
        'default': 'About',
        'ja_JP': 'このソフトについて'
    },

    'ERROR_BOX_TITLE': {
        'default': 'failed: goto https://github.com/matanki-saito/SimpleInstaller',
        'ja_JP': '失敗：https://github.com/matanki-saito/SimpleInstallerを見てください'
    },
    'ERR_NOT_EXIST_FINAL_CHECK_FILE': {
        'default': 'not exist final check file',
        'ja_JP': '最終チェックファイルがありません'
    },
    'ERR_NOT_FIND_LIBRARYFOLDERS_VDF': {
        'default': 'Not find libraryfolders.vdf',
        'ja_JP': 'libraryfolders.vdfが見つかりませんでした'
    },
    'ERR_NOT_FIND_STEAM_REGKEY': {
        'default': 'Not find steam registry key',
        'ja_JP': 'Steamのレジストリキーが見つかりませんでした'
    },
    'ERR_NOT_FIND_INSTALLPATH_IN_STEAM_REGKEY': {
        'default': 'Not find installPath in steam registry key',
        'ja_JP': 'SteamのレジストリキーにinstallPathが見つかりませんでした'
    },
    'ERR_NOT_EXIST_DEFAULT_STEAMAPPS_DIR': {
        'default': 'Not exist default steamapps directory',
        'ja_JP': 'デフォルトのsteamappsディレクトリがありません'
    },
    'ERR_INVALID_ACF': {
        'default': 'Invalid acf file',
        'ja_JP': 'acf fileが正しくありません'
    },
    'ERR_NOT_EXIST_GAME_INSTALL_DIR': {
        'default': 'Not exist game install directory',
        'ja_JP': 'ゲームのインストールディレクトリがありません'
    },
    'ERR_NOT_FIND_TARGET_GAME_ON_YOUR_PC': {
        'default': 'Not find target game on your PC',
        'ja_JP': 'あなたのPCには該当のゲームはありません'
    },
}


def _(key):
    if loca_dic.get(key) is None:
        return key
    if loca_dic.get(key).get(loc) is None:
        return loca_dic.get(key).get('default')

    return loca_dic.get(key).get(loc)


def install(install_dir_path, target_zip_url, final_check_file):
    # 最終チェックファイルがあるかを確認する
    if os.path.exists(os.path.join(install_dir_path, final_check_file)) is False:
        raise Exception(_('ERR_NOT_EXIST_FINAL_CHECK_FILE'))

    path, headers = urllib.request.urlretrieve(target_zip_url)
    with zipfile.ZipFile(path) as existing_zip:
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
    steam_apps_path = os.path.join(steam_install_path, "steamapps")
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
    target_app_acf_path = os.path.join(dir_path, "appmanifest_{}.acf".format(target_app_id))

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
    game_install_dir_path = os.path.join(dir_path, "common", game_install_dir_name)

    if os.path.exists(game_install_dir_path) is False:
        raise Exception(_("ERR_NOT_EXIST_GAME_INSTALL_DIR"))

    return game_install_dir_path


def get_lib_folders_from_vdf(steam_apps_path):
    # vdfファイルを探す
    library_folders_vdf_path = os.path.join(steam_apps_path, "libraryfolders.vdf")
    if os.path.exists(library_folders_vdf_path) is False:
        raise Exception(_("ERR_NOT_FIND_LIBRARYFOLDERS_VDF"))

    # vdfファイルにある"[数字]" "xxxx"をさがす
    install_dir_pattern = re.compile(r'\s*"[0-9]+"\s+"(.*)')
    game_libs_paths = []
    with open(library_folders_vdf_path, 'r') as target_vdf_file:
        for line in target_vdf_file:
            result = install_dir_pattern.match(line)
            if result is not None:
                game_libs_paths.append(os.path.join(result.group(1).strip("\"").replace("\\\\", "\\"), "steamapps"))

    return game_libs_paths


def installer(app_id, target_zip, final_check_file):
    executor = ThreadPoolExecutor(max_workers=2)

    a = executor.submit(wait_on_b)
    b = executor.submit(wait_on_a)

    try:
        install_dir_path = get_game_install_dir_path(app_id)
        install(install_dir_path, target_zip, final_check_file)
        messagebox.showinfo(_('SUCCESS_BOX_TITLE'), _('SUCCESS_BOX_MESSAGE'))

    except Exception as exp:
        messagebox.showerror(_('ERROR_BOX_TITLE'), exp.args[0])


def about():
    messagebox.showinfo(_('ABOUT_BOX_TITLE'), _('ABOUT_BOX_MESSAGE'))


if __name__ == '__main__':
    root = tkinter.Tk()
    root.title(_('TITLE'))

    root.geometry("300x300")

    eu4installButton = tkinter.Button(root,
                                      activebackground='#A59564',
                                      background='#A0873C',
                                      text=_('INSTALL_EU4_MBDLL'),
                                      command=lambda x=236850,
                                                     y="https://github.com/matanki-saito/SimpleInstaller/files/2769846/eu4.zip",
                                                     z='eu4.exe'
                                      : installer(x, y, z),
                                      font=("Helvetica", 12))
    eu4installButton.pack(expand=True, fill='both')

    ck2InstallButton = tkinter.Button(root,
                                      activebackground='#80ABA9',
                                      background='#92B5A9',
                                      text=_('INSTALL_CK2_MBDLL'),
                                      command=lambda x=203770,
                                                     y="https://github.com/matanki-saito/SimpleInstaller/files/2769845/ck2.zip",
                                                     z='ck2game.exe'
                                      : installer(x, y, z),
                                      font=("Helvetica", 12))
    ck2InstallButton.pack(expand=True, fill='both')

    f = tkinter.Frame(root)
    f.pack(fill='x')

    aboutButton = tkinter.Button(f,
                                 background='#A3A3A2',
                                 text=_('ABOUT'),
                                 command=about,
                                 height='1',
                                 font=("Helvetica", 12))
    aboutButton.pack(expand=True, fill='x', side="left")

    exitButton = tkinter.Button(f,
                                background='#A3A3A2',
                                text=_('EXIT'),
                                command=sys.exit,
                                height='1',
                                font=("Helvetica", 12))
    exitButton.pack(expand=True, fill='x', side="left")

    root.mainloop()
