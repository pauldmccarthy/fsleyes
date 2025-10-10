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

    urlbase = f'{zenodo_url}/api/deposit/depositions'
    tknhdr  = {'Authorization' : f'Bearer {access_token}'}
    jhdr    = {'Content-Type'  : 'application/json'}


    # Create a new deposit
    url = f'{urlbase}/{dep_id}/actions/newversion'
    print(f'Creating new deposit: {url}')
    r   = requests.post(url, json={}, headers=tknhdr | jhdr)
    if r.status_code != 201:
        raise RuntimeError(f'POST {url} failed: {r.status_code}')

    r = r.json()

    dep_id     = r['id']
    bucket_url = r['links']['bucket']

    print(f"New deposition ID: {dep_id}")

    # Upload the file
    with open(upload_file, 'rb') as f:
        fname = op.basename(upload_file)
        url   = f'{bucket_url}/{fname}'
        print(f'Uploading file: {url}')
        r = requests.post(url, headers=tknhdr, data=f)

    if r.status_code != 201:
        raise RuntimeError(f'POST {url} failed: {r.status_code}')

    # Upload the metadata
    url = f'{urlbase}/{dep_id}'
    print(f'Uploading metadata: {url}')
    r = requests.put(url, data=json.dumps(meta), headers=tknhdr | jhdr)

    if r.status_code != 200:
        print(r.json())
        raise RuntimeError(f'PUT {url} failed: {r.status_code}')

    # Publish
    url = f'{urlbase}/{dep_id}/actions/publish'
    print(f'Publishing: {url}')
    r = requests.post(url, headers=tknhdr)

    if r.status_code != 202:
        raise RuntimeError(f'POST {url} failed: {r.status_code}')


def make_meta(templatefile, version, date):
    with open(templatefile, 'rt') as f:
        template = f.read()

    template = j2.Template(template)

    env = {
        'VERSION' : version,
        'DATE'    : date,
    }

    meta = template.render(**env)

    print('Filled out metadata:')
    print(meta)

    return json.loads(meta)


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
