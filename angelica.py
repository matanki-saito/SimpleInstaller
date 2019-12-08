import concurrent.futures
import ctypes
import json
import os.path
import re
import shutil
import subprocess as sb
import tempfile
import time
import tkinter
import tkinter.ttk as ttk
import urllib.request
import winreg
import zipfile
from ctypes.wintypes import MAX_PATH
from os.path import join as __
from tkinter import messagebox

from github_tool import download_asset_from_github, download_asset_url_from_github
from loca import _


def remove_util(path):
    """
    ファイルだろうがディレクトリだが存在すればお構いなしに削除する関数
    :param path: パス
    :return: 成否
    """

    if not os.path.exists(path):
        return False

    if os.path.isfile(path):
        os.remove(path)

    elif os.path.isdir(path):
        shutil.rmtree(path)

    return True


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
    with open(target_app_acf_path, mode='r', encoding="utf8", errors='ignore') as target_app_acf_file:
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
    with open(library_folders_vdf_path, mode='r', encoding="utf8", errors='ignore') as target_vdf_file:
        for line in target_vdf_file:
            result = install_dir_pattern.match(line)
            if result is not None:
                game_libs_paths.append(__(result.group(1).strip("\"").replace("\\\\", "\\"), "steamapps"))

    return game_libs_paths


def install_key_file(save_file_path, mod_title, key_file_path):
    with open(save_file_path, encoding="utf-8", mode='w', errors='ignore') as fw:
        fw.write("\n".join([
            mod_title,
            key_file_path
        ]))


def dll_installer(app_id, final_check_file, target_zip_url=None, target_repository=None):
    install_dir_path = get_game_install_dir_path(app_id)
    if target_zip_url is not None:
        src_url = target_zip_url
    else:
        src_url = download_asset_url_from_github(
            repository_author=target_repository.get("author"),
            repository_name=target_repository.get("name")
        )
    install(install_dir_path, src_url, final_check_file)


def uninstaller(uninstall_info_list):
    for info in uninstall_info_list:
        final_check_file = info['final_check_file']
        remove_target_paths = info['remove_target_paths']

        base_path = '.'

        if 'app_id' in info:
            base_path = get_game_install_dir_path(info['app_id'])
        elif 'game_dir_name' in info:
            base_path = __(get_my_documents_folder(),
                           "Paradox Interactive",
                           info['game_dir_name'])
            # Modダウンローダーをuninstallモードで起動
            if os.path.exists(__(base_path, "claes.exe")):
                sb.call(__(base_path, "claes.exe /uninstall-all"))

        # 最終チェックファイルがあるかを確認する。このファイルがあるかどうかで本当にインストールされているか判断する
        if os.path.exists(__(base_path, final_check_file)) is False:
            raise Exception(_('ERR_NOT_EXIST_FINAL_CHECK_FILE'))

        for path in remove_target_paths:
            remove_util(__(base_path, path))


def get_my_documents_folder():
    # APIを使って探す
    buf = ctypes.create_unicode_buffer(MAX_PATH + 1)
    if ctypes.windll.shell32.SHGetSpecialFolderPathW(None, buf, 0x0005, False):
        return buf.value
    else:
        raise Exception(_("ERR_SHGetSpecialFolderPathW"))


def mod_installer(app_id, target_repository, key_file_name, game_dir_name, key_list_url):
    # My Documents をAPIから見つける
    install_game_dir_path = __(get_my_documents_folder(),
                               "Paradox Interactive",
                               game_dir_name)

    # exeを見つける
    install_dll_dir_path = get_game_install_dir_path(app_id)

    # Modダウンローダーを配置
    install_downloader(target_repository=target_repository,
                       install_dir_path=install_game_dir_path)

    # keyファイルを保存
    os.makedirs(__(install_game_dir_path, 'claes.key'), exist_ok=True)
    key_ids = json.loads(urllib.request.urlopen(key_list_url).read().decode('utf8'))
    for item in key_ids:
        install_key_file(save_file_path=__(install_game_dir_path, "claes.key", item.get("id") + ".key"),
                         mod_title=item.get("name"),
                         key_file_path=__(install_dll_dir_path, key_file_name))

    # Modダウンローダーを起動
    sb.call(__(install_game_dir_path, "claes.exe"))


def about():
    messagebox.showinfo(_('ABOUT_BOX_TITLE'), _('ABOUT_BOX_MESSAGE'))


if __name__ == '__main__':
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)

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

    dl_url = "https://github.com/matanki-saito/SimpleInstaller/files/"


    def on_enter(e, bg_color, font_color):
        e.widget['background'] = bg_color
        e.widget['fg'] = font_color


    def on_leave(e, bg_color, font_color):
        e.widget['background'] = bg_color
        e.widget['fg'] = font_color


    def threader(r, func):
        original_text = r['text']
        r['text'] = _('TASK_DO')

        feature = executor.submit(func)

        def done(self):
            try:
                self.result()
                r['text'] = _('TASK_FINISH')
                time.sleep(1)
            except Exception as exp:
                messagebox.showerror(_('ERROR_BOX_TITLE'), _('ERROR_BOX_MESSAGE') + ":\n" + str(exp))
            finally:
                r['text'] = original_text

        feature.add_done_callback(done)


    # EU4
    eu4DllInstallButton = tkinter.Button(frame1_1,
                                         activebackground='#d3a243',
                                         background='#d3a243',
                                         fg="#8f2e14",
                                         relief='flat',
                                         text=_('INSTALL_EU4_MBDLL'),
                                         command=lambda: threader(eu4DllInstallButton, lambda: dll_installer(
                                             app_id=236850,
                                             final_check_file='eu4.exe',
                                             target_repository={
                                                 "author": "matanki-saito",
                                                 "name": "eu4dll"
                                             },
                                         )),
                                         font=("sans-selif", 16, "bold"))
    eu4DllInstallButton.pack(expand=True, fill='both')
    eu4DllInstallButton.bind("<Enter>", lambda e: on_enter(e, "#e6b422", "#9a493f"))
    eu4DllInstallButton.bind("<Leave>", lambda e: on_leave(e, "#d3a243", "#8f2e14"))

    # CK2
    ck2DllInstallButton = tkinter.Button(frame1_1,
                                         activebackground='#2c4f54',
                                         background='#2c4f54',
                                         fg='#c1e4e9',
                                         relief='flat',
                                         text=_('INSTALL_CK2_MBDLL'),
                                         command=lambda: threader(ck2DllInstallButton, lambda: dll_installer(
                                             app_id=203770,
                                             final_check_file='ck2game.exe',
                                             target_repository={
                                                 "author": "matanki-saito",
                                                 "name": "ck2dll"
                                             },
                                         )),
                                         font=("sans-selif", 16, "bold"))
    ck2DllInstallButton.pack(expand=True, fill='both')
    ck2DllInstallButton.bind("<Enter>", lambda e: on_enter(e, "#478384", "#1f3134"))
    ck2DllInstallButton.bind("<Leave>", lambda e: on_leave(e, "#2c4f54", "#c1e4e9"))

    # Install downloader and jpmod
    frame1_2 = tkinter.Frame(tab2, pady=0)
    frame1_2.pack(expand=True, fill='both')
    repo_url = "https://raw.githubusercontent.com/matanki-saito/SimpleInstaller/master/"

    # EU4
    eu4ModInstallButton = tkinter.Button(frame1_2,
                                         activebackground='#d3a243',
                                         background='#d3a243',
                                         relief='flat',
                                         fg="#8f2e14",
                                         text=_('INSTALL_EU4_JPMOD'),
                                         command=lambda: threader(eu4ModInstallButton, lambda: mod_installer(
                                             app_id=236850,
                                             target_repository={
                                                 "author": "matanki-saito",
                                                 "name": "moddownloader"
                                             },
                                             key_file_name='eu4.exe',
                                             game_dir_name="Europa Universalis IV",
                                             key_list_url=repo_url + "eu4mods.json")),
                                         font=("sans-selif", 16, "bold"))
    eu4ModInstallButton.pack(expand=True, fill='both')
    eu4ModInstallButton.bind("<Enter>", lambda e: on_enter(e, "#e6b422", "#9a493f"))
    eu4ModInstallButton.bind("<Leave>", lambda e: on_leave(e, "#d3a243", "#8f2e14"))

    # CK2
    ck2ModInstallButton = tkinter.Button(frame1_2,
                                         activebackground='#2c4f54',
                                         background='#2c4f54',
                                         relief='flat',
                                         fg='#c1e4e9',
                                         text=_('INSTALL_CK2_JPMOD'),
                                         command=lambda: threader(ck2ModInstallButton, lambda: mod_installer(
                                             app_id=203770,
                                             target_repository={
                                                 "author": "matanki-saito",
                                                 "name": "moddownloader"
                                             },
                                             key_file_name='ck2game.exe',
                                             game_dir_name="Crusader Kings II",
                                             key_list_url=repo_url + "ck2mods.json")),
                                         font=("sans-selif", 16, "bold"))
    ck2ModInstallButton.pack(expand=True, fill='both')
    ck2ModInstallButton.bind("<Enter>", lambda e: on_enter(e, "#478384", "#1f3134"))
    ck2ModInstallButton.bind("<Leave>", lambda e: on_leave(e, "#2c4f54", "#c1e4e9"))

    # その他
    frame1_3 = tkinter.Frame(tab3, pady=0)
    frame1_3.pack(expand=True, fill='both')

    about_button = tkinter.Button(frame1_3,
                                  background='#443648',
                                  fg='white',
                                  text=_('ABOUT'),
                                  command=about,
                                  height='1',
                                  font=("Helvetica", 12))
    about_button.pack(expand=True, fill='both')

    uninstall_button_eu4 = tkinter.Button(frame1_3,
                                          background='#FFFFFF',
                                          fg='black',
                                          text=_('UNINSTALL_EU4'),
                                          command=lambda: threader(uninstall_button_eu4, lambda: uninstaller(
                                              [
                                                  {
                                                      # EU4 DLL
                                                      'app_id': 236850,
                                                      'final_check_file': 'eu4.exe',
                                                      'remove_target_paths': [
                                                          'd3d9.dll',
                                                          'version.dll',
                                                          'plugins',
                                                          'pattern_eu4jps.log',
                                                          'README.md'
                                                          'pattern_eu4_jps_2.log',
                                                          'README.md',
                                                          '.dist.v1.json'
                                                      ]
                                                  },
                                                  {
                                                      # EU4 MOD
                                                      'game_dir_name': 'Europa Universalis IV',
                                                      'final_check_file': 'settings.txt',
                                                      'remove_target_paths': [
                                                          'claes.exe',
                                                          'claes.key',
                                                          'claes.cache'
                                                      ]
                                                  }
                                              ])),
                                          height='1',
                                          font=("Helvetica", 12))
    uninstall_button_eu4.pack(expand=True, fill='both')

    uninstall_button_ck2 = tkinter.Button(frame1_3,
                                          background='#FFFFFF',
                                          fg='black',
                                          text=_('UNINSTALL_CK2'),
                                          command=lambda: threader(uninstall_button_ck2, lambda: uninstaller(
                                              [
                                                  {
                                                      # CK2 DLL
                                                      'app_id': 203770,
                                                      'final_check_file': 'ck2game.exe',
                                                      'remove_target_paths': [
                                                          'd3d9.dll',
                                                          'version.dll',
                                                          'plugins',
                                                          'pattern_ck2jps.log',
                                                          'pattern_ck2_jps_2.log',
                                                          'README.md',
                                                          '.dist.v1.json'
                                                      ]
                                                  },
                                                  {
                                                      # CK2 MOD
                                                      'game_dir_name': 'Crusader Kings II',
                                                      'final_check_file': 'settings.txt',
                                                      'remove_target_paths': [
                                                          'claes.exe',
                                                          'claes.key',
                                                          'claes.cache'
                                                      ]
                                                  }
                                              ])),
                                          height='1',
                                          font=("Helvetica", 12))
    uninstall_button_ck2.pack(expand=True, fill='both')

    # main
    root.mainloop()
