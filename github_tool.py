import json
import logging
import urllib.request


def download_asset_url_from_github(repository_author,
                                   repository_name,
                                   release_tag=None,
                                   file_name=None):
    """
    githubからアセットをダウンロード。未指定の場合は最新を取得
    :param repository_author:
    :param repository_name:
    :param release_tag:
    :param file_name:
    :return:
    """

    logging.info('download asset url from github')

    api_base_url = "https://api.github.com/repos/{}/{}".format(repository_author, repository_name)

    if release_tag is None:
        logging.info('release_tag=%s', release_tag)
        response = urllib.request.urlopen("{}/releases/latest".format(api_base_url))
        logging.info('finish urlopen')
        content = json.loads(response.read().decode('utf8'))
        logging.info('content=%s', content)
        release_tag = content["tag_name"]
        logging.info('release_tag=%s', release_tag)

    if file_name is None:
        logging.info('file_name=%s', file_name)
        response = urllib.request.urlopen("{}/releases/tags/{}".format(api_base_url, release_tag))
        logging.info('finish urlopen')
        content = json.loads(response.read().decode('utf8'))
        logging.info('content=%s', content)
        file_name = content["assets"][0]["name"]
        logging.info('file_name=%s', file_name)

    url = "{}/{}/{}/releases/download/{}/{}".format("https://github.com",
                                                    repository_author,
                                                    repository_name,
                                                    release_tag,
                                                    file_name)

    logging.info('url=%s', url)

    return url


def download_asset_from_github(repository_author,
                               repository_name,
                               out_file,
                               release_tag=None,
                               file_name=None):
    logging.info('download asset from github')

    request_url = download_asset_url_from_github(repository_author,
                                                 repository_name,
                                                 release_tag,
                                                 file_name)

    logging.info('request_url=%s', request_url)

    req = urllib.request.Request(request_url)

    logging.info('create request')

    out_file.write(urllib.request.urlopen(req).read())

    logging.info('finish urlopen')
