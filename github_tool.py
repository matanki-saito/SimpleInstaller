import json
import urllib.request


def download_asset_from_github(repository_author,
                               repository_name,
                               out_file_path,
                               release_tag=None,
                               file_name=None):
    """
    githubからアセットをダウンロード。未指定の場合は最新を取得
    :param repository_author:
    :param repository_name:
    :param release_tag:
    :param file_name:
    :param out_file_path:
    :return:
    """
    api_base_url = "https://api.github.com/repos/{}/{}".format(repository_author, repository_name)

    if release_tag is None:
        response = urllib.request.urlopen("{}/releases/latest".format(api_base_url))
        content = json.loads(response.read().decode('utf8'))
        release_tag = content["tag_name"]

    if file_name is None:
        response = urllib.request.urlopen("{}/releases/tags/{}".format(api_base_url, release_tag))
        content = json.loads(response.read().decode('utf8'))
        file_name = content["assets"][0]["name"]

    request_url = "{}/{}/{}/releases/download/{}/{}".format("https://github.com",
                                                            repository_author,
                                                            repository_name,
                                                            release_tag,
                                                            file_name
                                                            )
    req = urllib.request.Request(request_url)

    with open(out_file_path, "wb") as my_file:
        my_file.write(urllib.request.urlopen(req).read())

    return out_file_path
