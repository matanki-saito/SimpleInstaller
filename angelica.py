import concurrent.futures
import ctypes
import json
import logging
import os.path
import queue
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
from tkinter.scrolledtext import ScrolledText

from github_tool import download_asset_from_github, download_asset_url_from_github
from loca import _

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QueueHandler(logging.Handler):
    """Class to send logger records to a queue

    It can be used from different threads
    """

    def __init__(self, _log_queue):
        super().__init__()
        self.log_queue = _log_queue

    def emit(self, record):
        self.log_queue.put(record)


def remove_util(path):
    """
    ファイルだろうがディレクトリだが存在すればお構いなしに削除する関数
    :param path: パス
    :return: 成否
    """

    logger.info('remove files, path=%s', path)

    if not os.path.exists(path):
        return False

    if os.path.isfile(path):
        os.remove(path)

    elif os.path.isdir(path):
        shutil.rmtree(path)

    return True


def install(install_dir_path, target_zip_url, final_check_file):
    logger.info('install')

    final_check_file_path = __(install_dir_path, final_check_file)
    logger.info('final_check_file_path=%s', final_check_file_path)

    # 最終チェックファイルがあるかを確認する
    if os.path.exists(final_check_file_path) is False:
        raise Exception(_('ERR_NOT_EXIST_FINAL_CHECK_FILE'))

    # 最終チェックファイルがある場所に対してファイルを展開する
    final_check_file_dir = os.path.dirname(final_check_file_path)
    logger.info('final_check_file_dir=%s', final_check_file_dir)

    path, headers = urllib.request.urlretrieve(target_zip_url)

    logger.info('path=%s,headers=%s', path, headers)

    with zipfile.ZipFile(path) as existing_zip:
        existing_zip.extractall(final_check_file_dir)

    logger.info('zip unpacked')


def install_downloader(target_repository, install_dir_path):
    logger.info('install downloader')

    with tempfile.TemporaryFile() as w:
        download_asset_from_github(
            repository_author=target_repository.get("author"),
            repository_name=target_repository.get("name"),
            out_file=w
        )

        logger.info('asset_file_path=%s', w)

        with zipfile.ZipFile(w) as existing_zip:
            existing_zip.extractall(install_dir_path)

    logger.info('zip unpacked')


def get_game_install_dir_path(target_app_id):
    logger.info('Get install dir path')
    # レジストリを見て、Steamのインストール先を探す
    # 32bitを見て、なければ64bitのキーを探しに行く。それでもなければそもそもインストールされていないと判断する
    try:
        steam_install_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, "SOFTWARE\\Valve\\Steam")
    except OSError:
        try:
            steam_install_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, "SOFTWARE\\WOW6432Node\\Valve\\Steam")
        except OSError:
            raise Exception(_("ERR_NOT_FIND_STEAM_REGKEY"))

    logger.info('Find steam_install_key in reg')

    try:
        steam_install_path, key_type = winreg.QueryValueEx(steam_install_key, "InstallPath")
    except FileNotFoundError:
        raise Exception(_("ERR_NOT_FIND_INSTALLPATH_IN_STEAM_REGKEY"))

    steam_install_key.Close()
    logger.info('steam_install_path=%s, key_type=%s', steam_install_path, key_type)

    # 基本問題ないと思うが念の為
    if key_type != winreg.REG_SZ:
        raise Exception("invald value")

    # デフォルトのsteamappsフォルダを探す
    steam_apps_path = __(steam_install_path, "steamapps")
    if os.path.exists(steam_apps_path) is False:
        raise Exception(_("ERR_NOT_EXIST_DEFAULT_STEAMAPPS_DIR"))

    logger.info('steam_apps_path=%s', steam_apps_path)

    # acfがあるフォルダを列挙
    acf_dir_paths = [steam_apps_path]
    acf_dir_paths.extend(get_lib_folders_from_vdf(steam_apps_path))

    logger.info('acf_dir_paths=%s', acf_dir_paths)

    # 各ディレクトリについて処理
    game_install_dir_path = None
    for dir_path in acf_dir_paths:
        game_install_dir_path = get_game_install_dir(dir_path, target_app_id)
        if game_install_dir_path is None:
            continue
        else:
            break

    logger.info('game_install_dir_path=%s', game_install_dir_path)

    if game_install_dir_path is None:
        raise Exception(_("ERR_NOT_FIND_TARGET_GAME_ON_YOUR_PC"))

    return game_install_dir_path


def get_game_install_dir(dir_path, target_app_id):
    logger.info('get game install dir')

    # インストールディレクトリにあるsteamapps/appmanifest_[APPID].acfを探す
    target_app_acf_path = __(dir_path, "appmanifest_{}.acf".format(target_app_id))

    logger.info('target_app_acf_path=%s', target_app_acf_path)

    # なければ終了
    if os.path.exists(target_app_acf_path) is False:
        return None

    # acfファイルにある"installdir" "xxxx"をさがす
    install_dir_pattern = re.compile(r'\s*"installdir"\s+"(.*)')
    game_install_dir_name = None
    with open(target_app_acf_path, mode='r', encoding="utf8", errors='ignore') as target_app_acf_file:
        logger.info('open %s', target_app_acf_path)
        for line in target_app_acf_file:
            result = install_dir_pattern.match(line)
            if result is not None:
                game_install_dir_name = result.group(1).strip("\"")
                break

        logger.info('game_install_dir_name=%s', game_install_dir_name)

        if game_install_dir_name is None:
            raise Exception(_("ERR_INVALID_ACF"))

    # パスを確認
    game_install_dir_path = __(dir_path, "common", game_install_dir_name)

    if os.path.exists(game_install_dir_path) is False:
        raise Exception(_("ERR_NOT_EXIST_GAME_INSTALL_DIR"))

    logger.info('game_install_dir_path=%s', game_install_dir_path)

    return game_install_dir_path


def get_lib_folders_from_vdf(steam_apps_path):
    logger.info('get lib folders from vdf')

    # vdfファイルを探す
    library_folders_vdf_path = __(steam_apps_path, "libraryfolders.vdf")
    if os.path.exists(library_folders_vdf_path) is False:
        raise Exception(_("ERR_NOT_FIND_LIBRARYFOLDERS_VDF"))

    logger.info('library_folders_vdf_path=%s', library_folders_vdf_path)

    # vdfファイルにある"[数字]" "xxxx"をさがす
    install_dir_pattern = re.compile(r'\s*"[0-9]+"\s+"(.*)')
    logger.info('install_dir_pattern=%s', install_dir_pattern)

    game_libs_paths = []
    with open(library_folders_vdf_path, mode='r', encoding="utf8", errors='ignore') as target_vdf_file:
        logger.info('open %s', library_folders_vdf_path)
        for line in target_vdf_file:
            result = install_dir_pattern.match(line)
            if result is not None:
                game_libs_paths.append(__(result.group(1).strip("\"").replace("\\\\", "\\"), "steamapps"))

    logger.info('game_libs_paths=%s', game_libs_paths)

    return game_libs_paths


def install_key_file(save_file_path, mod_title, key_file_path):
    logger.info('install key file')

    with open(save_file_path, encoding="utf-8", mode='w', errors='ignore') as fw:
        logger.info('open %s', save_file_path)
        fw.write("\n".join([
            mod_title,
            key_file_path
        ]))

    logger.info('finish')


def dll_installer(app_id, final_check_file, target_zip_url=None, target_repository=None):
    logger.info('Start dll installer')
    install_dir_path = get_game_install_dir_path(app_id)

    logger.info('install_dir_path=%s', install_dir_path)

    if target_zip_url is not None:
        src_url = target_zip_url
    else:
        src_url = download_asset_url_from_github(
            repository_author=target_repository.get("author"),
            repository_name=target_repository.get("name")
        )

    logger.info('src_url=%s', src_url)

    install(install_dir_path, src_url, final_check_file)

    logger.info('finish')


def uninstaller(uninstall_info_list):
    logger.info('uninstall')

    for info in uninstall_info_list:
        final_check_file = info['final_check_file']
        remove_target_paths = info['remove_target_paths']

        logger.info('remove_target_paths=%s', remove_target_paths)

        base_path = '.'

        if 'app_id' in info:
            base_path = get_game_install_dir_path(info['app_id'])
        elif 'game_dir_name' in info:
            base_path = __(get_my_documents_folder(),
                           "Paradox Interactive",
                           info['game_dir_name'])
            # Modダウンローダーをuninstallモードで起動
            if os.path.exists(__(base_path, "claes.exe")):
                logger.info('claes uninstall mode')
                sb.call(__(base_path, "claes.exe /uninstall-all"))

        logger.info('base_path=%s', base_path)

        # 最終チェックファイルがあるかを確認する。このファイルがあるかどうかで本当にインストールされているか判断する
        if os.path.exists(__(base_path, final_check_file)) is False:
            raise Exception(_('ERR_NOT_EXIST_FINAL_CHECK_FILE'))

        for path in remove_target_paths:
            remove_util(__(base_path, path))

    logger.info('finish')


def get_my_documents_folder():
    logger.info('get my documents folder')

    # APIを使って探す
    buf = ctypes.create_unicode_buffer(MAX_PATH + 1)
    if ctypes.windll.shell32.SHGetSpecialFolderPathW(None, buf, 0x0005, False):
        logger.info('search done. buf.value=%s', buf.value)
        return buf.value
    else:
        raise Exception(_("ERR_SHGetSpecialFolderPathW"))


def mod_installer(app_id, target_repository, key_file_name, game_dir_name, key_list_url):
    logger.info('mod install')

    # My Documents をAPIから見つける
    install_game_dir_path = __(get_my_documents_folder(),
                               "Paradox Interactive",
                               game_dir_name)

    logger.info('install_game_dir_path=%s', install_game_dir_path)

    # exeを見つける
    install_dll_dir_path = get_game_install_dir_path(app_id)

    logger.info('install_dll_dir_path=%s', install_dll_dir_path)

    logger.info('install downloader')

    # Modダウンローダーを配置
    install_downloader(target_repository=target_repository,
                       install_dir_path=install_game_dir_path)

    logger.info('done')

    # keyファイルを保存
    os.makedirs(__(install_game_dir_path, 'claes.key'), exist_ok=True)
    key_ids = json.loads(urllib.request.urlopen(key_list_url).read().decode('utf8'))

    logger.info('key_ids=%s', key_ids)

    for item in key_ids:
        install_key_file(save_file_path=__(install_game_dir_path, "claes.key", item.get("id") + ".key"),
                         mod_title=item.get("name"),
                         key_file_path=__(install_dll_dir_path, key_file_name))

    logger.info('call claes')

    # Modダウンローダーを起動
    sb.call(__(install_game_dir_path, "claes.exe"))

    logger.info('done')


def about():
    logger.info('open About dialog')
    messagebox.showinfo(_('ABOUT_BOX_TITLE'), _('ABOUT_BOX_MESSAGE'))


if __name__ == '__main__':
    # ログ設定
    # https://beenje.github.io/blog/posts/logging-to-a-tkinter-scrolledtext-widget/
    log_queue = queue.Queue()
    queue_handler = QueueHandler(log_queue)
    logger.addHandler(queue_handler)
    formatter = logging.Formatter('%(asctime)s: %(message)s')
    queue_handler.setFormatter(formatter)

    logger.info('GUI setup')

    repo_url = "https://raw.githubusercontent.com/matanki-saito/SimpleInstaller/master/"

    executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)

    root = tkinter.Tk()
    root.title(_('TITLE'))

    root.geometry("300x300")

    # ノートブック
    style = ttk.Style()
    style.configure("BW.TLabel", foreground="black", background="white")
    nb = ttk.Notebook(width=300, height=200, style="BW.TLabel")

    # タブの作成
    tab2 = tkinter.Frame(nb, pady=0, relief='flat')
    tab3 = tkinter.Frame(nb, pady=0, relief='flat')
    tab4 = tkinter.Frame(nb, pady=0, relief='flat')

    nb.add(tab2, text=_('TAB_JPMOD'), padding=0)
    nb.add(tab3, text=_('TAB_INFO'), padding=0)
    nb.add(tab4, text=_('TAB_LOG'), padding=0)
    nb.pack(expand=True, fill='both')


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


    # Install dll , downloader and jpmod
    frame1_2 = tkinter.Frame(tab2, pady=0)
    frame1_2.pack(expand=True, fill='both')


    def eu4_button_function():
        logger.info('Push a button to install eu4')
        dll_installer(
            app_id=236850,
            final_check_file='eu4.exe',
            target_repository={
                "author": "matanki-saito",
                "name": "eu4dll"
            },
        )

        mod_installer(
            app_id=236850,
            target_repository={
                "author": "matanki-saito",
                "name": "moddownloader"
            },
            key_file_name='eu4.exe',
            game_dir_name="Europa Universalis IV",
            key_list_url=repo_url + "eu4mods.json")


    def ck2_button_function():
        logger.info('Push a button to install ck2')
        dll_installer(
            app_id=203770,
            final_check_file='ck2game.exe',
            target_repository={
                "author": "matanki-saito",
                "name": "ck2dll"
            },
        )

        mod_installer(
            app_id=203770,
            target_repository={
                "author": "matanki-saito",
                "name": "moddownloader"
            },
            key_file_name='ck2game.exe',
            game_dir_name="Crusader Kings II",
            key_list_url=repo_url + "ck2mods.json")


    def ir_button_function():
        logger.info('Push a button to install I:R')
        dll_installer(
            app_id=859580,
            final_check_file='binaries/imperator.exe',
            target_repository={
                "author": "matanki-saito",
                "name": "irdll"
            },
        )

        mod_installer(
            app_id=859580,
            target_repository={
                "author": "matanki-saito",
                "name": "moddownloader"
            },
            key_file_name='binaries/imperator.exe',
            game_dir_name="Imperator",
            key_list_url=repo_url + "irmods.json")


    # EU4
    eu4InstallButton = tkinter.Button(frame1_2,
                                      activebackground='#d3a243',
                                      background='#d3a243',
                                      relief='flat',
                                      fg="#8f2e14",
                                      text=_('INSTALL_EU4'),
                                      command=lambda: threader(eu4InstallButton, eu4_button_function),
                                      font=("sans-selif", 16, "bold"))
    eu4InstallButton.pack(expand=True, fill='both')
    eu4InstallButton.bind("<Enter>", lambda e: on_enter(e, "#e6b422", "#000000"))
    eu4InstallButton.bind("<Leave>", lambda e: on_leave(e, "#d3a243", "#8f2e14"))

    # CK2
    ck2InstallButton = tkinter.Button(frame1_2,
                                      activebackground='#478384',
                                      background='#478384',
                                      relief='flat',
                                      fg='#1f3134',
                                      text=_('INSTALL_CK2'),
                                      command=lambda: threader(ck2InstallButton, ck2_button_function),
                                      font=("sans-selif", 16, "bold"))
    ck2InstallButton.pack(expand=True, fill='both')
    ck2InstallButton.bind("<Enter>", lambda e: on_enter(e, "#2c4f54", "#c1e4e9"))
    ck2InstallButton.bind("<Leave>", lambda e: on_leave(e, "#478384", "#1f3134"))

    # I:R
    irInstallButton = tkinter.Button(frame1_2,
                                     activebackground='#cca6bf',
                                     background='#cca6bf',
                                     relief='flat',
                                     fg='#8f2e14',
                                     text=_('INSTALL_IR'),
                                     command=lambda: threader(irInstallButton, ir_button_function),
                                     font=("sans-selif", 16, "bold"))
    irInstallButton.pack(expand=True, fill='both')
    irInstallButton.bind("<Enter>", lambda e: on_enter(e, "#bc64a4", "#c1e4e9"))
    irInstallButton.bind("<Leave>", lambda e: on_leave(e, "#cca6bf", "#8f2e14"))

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

    logger.info('mainloop')

    # ログエリア
    frame1_4 = tkinter.Frame(tab4, pady=0)
    frame1_4.pack(expand=True, fill='both')
    log_area = ScrolledText(frame1_4, state='disabled', height=12)
    log_area.configure(font='TkFixedFont')
    log_area.tag_config('INFO', foreground='black')
    log_area.tag_config('DEBUG', foreground='gray')
    log_area.tag_config('WARNING', foreground='orange')
    log_area.tag_config('ERROR', foreground='red')
    log_area.tag_config('CRITICAL', foreground='red', underline=1)
    log_area.pack(expand=True, fill='both')


    def display_log(record):
        msg = queue_handler.format(record)

        log_area.configure(state='normal')
        log_area.insert(tkinter.END, msg + '\n', record.levelname)
        log_area.configure(state='disabled')
        # Autoscroll to the bottom
        log_area.yview(tkinter.END)


    def poll_log_queue():
        # Check every 100ms if there is a new message in the queue to display
        while True:
            try:
                record = log_queue.get(block=False)
            except queue.Empty:
                break
            else:
                display_log(record)
        frame1_4.after(100, poll_log_queue)


    frame1_4.after(100, poll_log_queue)

    # main
    root.mainloop()
