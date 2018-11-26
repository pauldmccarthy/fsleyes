#!/usr/bin/env python
#
# Deposit a new version of something on zenodo.
#
# It is assumed that a deposit already exists on zenodo - you must
# specify the deposit ID of that original deposit.
#
# http://developers.zenodo.org/#rest-api


import os.path as op
import sys
import json

import jinja2 as j2
import requests


def deposit(zenodo_url, access_token, dep_id, upload_file, meta):

    urlbase = '{}/api/deposit/depositions'.format(zenodo_url)
    headers = {'Content-Type': 'application/json'}
    params  = {'access_token' : access_token}

    # Create a new deposit
    url = '{}/{}/actions/newversion'.format(urlbase, dep_id)
    print('Creating new deposit: {}'.format(url))
    r   = requests.post(url, params=params)
    if r.status_code != 201:
        raise RuntimeError('POST {} failed: {}'.format(url, r.status_code))

    newurl = r.json()['links']['latest_draft']
    dep_id = newurl.split('/')[-1]

    print("New deposition ID: {}".format(dep_id))

    # Upload the file
    data   = {'filename': op.basename(upload_file)}
    files  = {'file': open(upload_file, 'rb')}
    url    = '{}/{}/files'.format(urlbase, dep_id)
    print('Uploading file: {}'.format(url))
    r   = requests.post(url, params=params, data=data, files=files)

    if r.status_code != 201:
        raise RuntimeError('POST {} failed: {}'.format(url, r.status_code))

    # Upload the metadata

    url  = '{}/{}?access_token={}'.format(urlbase, dep_id, access_token)
    print('Uploading metadata: {}'.format(url))
    r = requests.put(url, data=json.dumps(meta), headers=headers)

    if r.status_code != 200:
        print(r.json())
        raise RuntimeError('PUT {} failed: {}'.format(url, r.status_code))

    # Publish
    url = '{}/{}/actions/publish'.format(urlbase, dep_id)
    print('Publishing: {}'.format(url))
    r = requests.post(url, params=params)

    if r.status_code != 202:
        raise RuntimeError('POST {} failed: {}'.format(url, r.status_code))


def make_meta(templatefile, version, date):
    with open(templatefile, 'rt') as f:
        template = f.read()

    template = j2.Template(template)

    env = {
        'VERSION' : version,
        'DATE'    : date,
    }

    return json.loads(template.render(**env))


if __name__ == '__main__':

    zurl       = sys.argv[1]
    tkn        = sys.argv[2]
    depid      = sys.argv[3]
    upfile     = sys.argv[4]
    metafile   = sys.argv[5]
    version    = sys.argv[6]
    date       = sys.argv[7]

    meta = make_meta(metafile, version, date)

    deposit(zurl, tkn, depid, upfile, meta)
