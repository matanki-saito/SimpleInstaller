import locale
import os.path
import re
import sys
import tkinter
import urllib.request
import winreg
import zipfile
from tkinter import messagebox


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
        'ja_JP': '終了',
        'zh_CN': '终了',
        'zh_TW': '終了',
        'ko_KR': '종료',
        'de_DE': 'Ausfahrt'
    },
    'ABOUT': {
        'default': 'About',
        'ja_JP': 'このソフトについて',
        'zh_CN': '关于这个软件',
        'zh_TW': '關於這個軟件',
        'ko_KR': '이 소프트웨어에 대한',
        'de_DE': 'Über'
    },
    'INSTALL_CK2_MBDLL': {
        'default': 'Install CK2 Multibyte DLL',
        'ja_JP': 'CK2日本語化DLLをインストール',
        'zh_CN': '安装CK2 Multibyte DLL',
        'zh_TW': '安裝CK2 Multibyte DLL',
        'ko_KR': 'CK2 멀티 바이트 DLL 설치',
        'de_DE': 'Installieren Sie die CK2-Multibyte-DLL'
    },
    'INSTALL_EU4_MBDLL': {
        'default': 'Install EU4 Multibyte DLL',
        'ja_JP': 'EU4日本語化DLLをインストール',
        'zh_CN': '安装EU4 Multibyte DLL',
        'zh_TW': '安裝EU4 Multibyte DLL',
        'ko_KR': 'EU4 멀티 바이트 DLL 설치',
        'de_DE': 'Installieren Sie die EU4-Multibyte-DLL'
    },
    'TITLE': {
        'default': 'CK2/EU4 Multibyte DLL Installer',
        'ja_JP': 'CK2/EU4 日本語化DLLインストーラー',
        'zh_CN': 'CK2 / EU4多字节DLL安装程序',
        'zh_TW': 'CK2 / EU4多字節DLL安裝程序',
        'ko_KR': 'CK2 / EU4 멀티 바이트 DLL 설치 프로그램',
        'de_DE': 'CK2 / EU4 Multibyte DLL Installer'
    },
    'SUCCESS_BOX_MESSAGE': {
        'default': 'Install Succeeded.',
        'ja_JP': 'インストール成功！',
        'zh_CN': '安装成功',
        'zh_TW': '安裝成功',
        'ko_KR': '설치 성공',
        'de_DE': 'Installieren Sie erfolgreich'
    },
    'SUCCESS_BOX_TITLE': {
        'default': 'Success',
        'ja_JP': '成功！',
        'zh_CN': '成功',
        'zh_TW': '成功',
        'ko_KR': '성공한',
        'de_DE': 'Erfolg'
    },
    'ABOUT_BOX_MESSAGE': {
        'default': 'Distribution URL: https://github.com/matanki-saito/SimpleInstaller',
        'ja_JP': 'インストーラー最新版配布元: https://github.com/matanki-saito/SimpleInstaller',
        'zh_CN': '分发网址: https://github.com/matanki-saito/SimpleInstaller',
        'zh_TW': '分發網址: https://github.com/matanki-saito/SimpleInstaller',
        'ko_KR': '게재 URL: https://github.com/matanki-saito/SimpleInstaller',
        'de_DE': 'Verteilungs-URL: https://github.com/matanki-saito/SimpleInstaller'
    },
    'ABOUT_BOX_TITLE': {
        'default': 'About',
        'ja_JP': 'このソフトについて',
        'zh_CN': '关于这个软件',
        'zh_TW': '關於這個軟件',
        'ko_KR': '이 소프트웨어에 대한',
        'de_DE': 'Über'
    },
    'ERROR_BOX_MESSAGE': {
        'default': 'Failed: please see https://github.com/matanki-saito/SimpleInstaller',
        'ja_JP': '失敗：https://github.com/matanki-saito/SimpleInstallerをご覧ください',
        'zh_CN': '失败：请参阅https://github.com/matanki-saito/SimpleInstaller',
        'zh_TW': '失敗：請參閱https://github.com/matanki-saito/SimpleInstaller',
        'ko_KR': '실패 : https://github.com/matanki-saito/SimpleInstaller를 참조하십시오.',
        'de_DE': 'Fehlgeschlagen: siehe https://github.com/matanki-saito/SimpleInstaller'
    },
    'ERROR_BOX_TITLE': {
        'default': 'Failed',
        'ja_JP': '失敗',
        'zh_CN': '失败',
        'zh_TW': '失敗',
        'ko_KR': '실패',
        'de_DE': 'Fehlgeschlagen'
    },
    'ERR_NOT_EXIST_FINAL_CHECK_FILE': {
        'default': 'Selected game itself was not found.',
        'ja_JP': '選択したゲーム本体が見つかりませんでした'
    },
    'ERR_NOT_FIND_LIBRARYFOLDERS_VDF': {
        'default': 'File libraryfolders.vdf was not found.',
        'ja_JP': 'libraryfolders.vdfファイルが見つかりませんでした'
    },
    'ERR_NOT_FIND_STEAM_REGKEY': {
        'default': 'Steam registry key was not found.',
        'ja_JP': 'Steamのレジストリキーが見つかりませんでした'
    },
    'ERR_NOT_FIND_INSTALLPATH_IN_STEAM_REGKEY': {
        'default': 'InstallPath was not found in steam registry key.',
        'ja_JP': 'SteamのレジストリキーにinstallPathが見つかりませんでした'
    },
    'ERR_NOT_EXIST_DEFAULT_STEAMAPPS_DIR': {
        'default': 'Default steamapps folder was not found.',
        'ja_JP': 'デフォルトのsteamappsフォルダが見つかりませんでした'
    },
    'ERR_INVALID_ACF': {
        'default': 'Invalid acf file.',
        'ja_JP': 'acfファイルに問題が見つかりました'
    },
    'ERR_NOT_EXIST_GAME_INSTALL_DIR': {
        'default': "Selected game's install folder was not found.",
        'ja_JP': '選択したゲームのインストールフォルダが見つかりませんでした'
    },
    'ERR_NOT_FIND_TARGET_GAME_ON_YOUR_PC': {
        'default': 'Selected game was not found on your PC.',
        'ja_JP': '選択したゲームがパソコンの中に見つかりませんでした'
    }
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
    try:
        install_dir_path = get_game_install_dir_path(app_id)

        install(install_dir_path, target_zip, final_check_file)

        messagebox.showinfo(_('SUCCESS_BOX_TITLE'), _('SUCCESS_BOX_MESSAGE'))

    except Exception as exp:
        messagebox.showerror(_('ERROR_BOX_TITLE'), _('ERROR_BOX_MESSAGE') + ":\n" + exp.args[0])


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
