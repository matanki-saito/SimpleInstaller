import locale


def get_language_windows(system_lang=True):
    """
    gettextなどを使うのが正解だろうが、面倒なので
    Get language code based on current Windows settings.
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
    },
    'TAB_MBDLL': {
        'default': 'DLL'
    },
    'TAB_JPMOD': {
        'default': 'JPMOD',
        'ja_JP': '日本語化MOD'
    },
    'TAB_INFO': {
        'default': 'About',
        'ja_JP': 'このソフトについて',
        'zh_CN': '关于这个软件',
        'zh_TW': '關於這個軟件',
        'ko_KR': '이 소프트웨어에 대한',
        'de_DE': 'Über'
    },
    'INSTALL_EU4_JPMOD': {
        'default': 'Install EU4 JPMODs',
        'ja_JP': 'EU4日本語化Modをインストール'
    },

    'INSTALL_CK2_JPMOD': {
        'default': 'Install CK2 JPMODs',
        'ja_JP': 'CK2日本語化Modをインストール'
    },
}


def _(key):
    """
    keyから定義済みのロケーションテキストを返却する。
    定義がない場合はdefault、それもない場合はkeyそのものを返却する
    :param key:
    :return:
    """
    if loca_dic.get(key) is None:
        return key
    if loca_dic.get(key).get(loc) is None:
        return loca_dic.get(key).get('default')

    return loca_dic.get(key).get(loc)
