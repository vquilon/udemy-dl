# pylint: disable=R,C,W,E
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""

Author  : Nasir Khan (r0ot h3x49)
Github  : https://github.com/r0oth3x49
License : MIT


Copyright (c) 2018-2025 Nasir Khan (r0ot h3x49)

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the
Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, 
and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR
ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH 
THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""

import re
import io
import os
import sys
import time
import json
import m3u8
import codecs
import requests
import cloudscraper
from html.parser import HTMLParser as compat_HTMLParser
from http.cookies import SimpleCookie as ParseCookie
from requests.exceptions import ConnectionError as conn_error

encoding = str

NO_DEFAULT = object()
LOGIN_URL = "https://www.udemy.com/join/login-popup/?ref=&display_type=popup&loc"
LOGOUT_URL = "https://www.udemy.com/user/logout"

WISHLIST_URL = "https://{portal_name}.udemy.com/api-2.0/users/me/wishlisted-courses?fields[course]=id,url,published_title&ordering=-access_time&page=1&page_size=1000"
COLLECTION_URL = "https://{portal_name}.udemy.com/api-2.0/users/me/subscribed-courses-collections/?collection_has_courses=True&course_limit=20&fields[course]=last_accessed_time,title,published_title&fields[user_has_subscribed_courses_collection]=@all&page=1&page_size=1000"
MY_COURSES_URL = "https://{portal_name}.udemy.com/api-2.0/users/me/subscribed-courses?fields[course]=id,url,title,published_title&ordering=-last_accessed,-access_time&page=1&page_size=10000"
COURSE_SEARCH = "https://{portal_name}.udemy.com/api-2.0/users/me/subscribed-courses?fields[course]=id,url,title,published_title&page=1&page_size=1000&ordering=-last_accessed,-access_time&search={course_name}"
COURSE_URL = "https://{portal_name}.udemy.com/api-2.0/courses/{course_id}/cached-subscriber-curriculum-items?fields[asset]=results,title,external_url,time_estimation,download_urls,slide_urls,filename,asset_type,captions,stream_urls,body&fields[chapter]=object_index,title,sort_order&fields[lecture]=id,title,object_index,asset,supplementary_assets,view_html&fields[quiz]=title,object_index,is_published,sort_order,type,version&fields[practice]=title,object_index,is_published,sort_order&page_size=10000"
# PLUGIN: QUIZ
# &fields[quiz]=title,object_index,is_published,sort_order,type&fields[practice]=title,object_index,is_published,sort_order&
SUBSCRIBED_COURSES = "https://www.udemy.com/api-2.0/users/me/subscribed-courses/?ordering=-last_accessed&fields[course]=id,title,url&page=1&page_size=12"
QUIZ_URL = "https://{portal_name}.udemy.com/api-2.0/quizzes/{quiz_id}/assessments/?version={last_version}&page_size=250&fields[assessment]=id,assessment_type,prompt,correct_response,section,question_plain,related_lectures"
REFERER_QUIZ_URL = "https://{portal_name}.udemy.com/course/{course_name}/learn/quiz/{quiz_id}#content"
LECTURE_URL = "https://{portal_name}.udemy.com/api-2.0/users/me/subscribed-courses/{course_id}/lectures/{lecture_id}/?fields[lecture]=asset,description,download_url,is_free,last_watched_second,version&fields[asset]=asset_type,length,media_license_token,course_is_drmed,media_sources,captions,thumbnail_sprite,slides,slide_urls,download_urls" # &q=0.6148300542269443"

WIDEVINE_KEY_ENCRYPT="https://indra.udemy.com/api-2.0/media-license-server/validate-auth-token?drm_type=widevine&auth_token={media_license_token}"

# https://indra.udemy.com/assets/25195092/encrypted-files/out/v1/cd1acb8084ab4788a03d3354050a5767/06c8dc12da2745f1b0b4e7c2c032dfef/842d4b8e2e014fbbb87c640ddc89d036/index.mpd?token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJwYXRoIjoib3V0L3YxL2NkMWFjYjgwODRhYjQ3ODhhMDNkMzM1NDA1MGE1NzY3LzA2YzhkYzEyZGEyNzQ1ZjFiMGI0ZTdjMmMwMzJkZmVmLzg0MmQ0YjhlMmUwMTRmYmJiODdjNjQwZGRjODlkMDM2LyIsImV4cCI6MTYzMjI0MTMzNn0.0RZPIu2wdhZG5WMGPDAJ7pKc_laEvGyVSMWZZczQexA&provider=cloudfront&v=1
#vdata1632225133276: 143
#https://bitmovin.com/demos/drm
# .requestMediaKeySystemAccess("com.widevine.alpha", {
#     "audioCapabilities": [
#         {
#             "contentType": "audio/mp4; codecs=\"mp4a.40.5\"",
#             "robustness": "SW_SECURE_CRYPTO"
#         }
#     ],
#     "videoCapabilities": [
#         {
#             "contentType": "video/mp4; codecs=\"avc1.4D401E\"",
#             "robustness": "SW_SECURE_CRYPTO"
#         }
#     ]
# })

# .requestMediaKeySystemAccess("com.microssoft.playready", {
#     "audioCapabilities": [
#         {
#             "contentType": "audio/mp4; codecs=\"mp4a.40.5\"",
#             "robustness": "SW_SECURE_CRYPTO"
#         }
#     ],
#     "videoCapabilities": [
#         {
#             "contentType": "video/mp4; codecs=\"avc1.4D401E\"",
#             "robustness": "SW_SECURE_CRYPTO"
#         }
#     ]
# })
# "com.apple.fps.1_0"


HEADERS = {
    "Origin": "www.udemy.com",
    "User-Agent": "Mozilla/5.0 (Windows NT 6.3; Win64; x64; rv:85.0) Gecko/20100101 Firefox/85.0",
    # "Referer": "https://www.udemy.com/join/login-popup/",
    "Accept": "*/*",
    # "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": None,
    # "Connection": "keep-alive",
}


__ALL__ = [
    "re",
    "io",
    "os",
    "sys",
    "time",
    "json",
    "pyver",
    "codecs",
    "encoding",
    "requests",
    "conn_error",
    "cloudscraper",
    "compat_HTMLParser",
    "ParseCookie",
    "HEADERS",
    "LOGIN_URL",
    "NO_DEFAULT",
    "COURSE_URL",
    "LOGOUT_URL",
    "WISHLIST_URL",
    "COLLECTION_URL",
    "MY_COURSES_URL",
    "COURSE_SEARCH",
    "SUBSCRIBED_COURSES",
]
