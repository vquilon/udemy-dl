# pylint: disable=R,C,W
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
from typing import List

from udemy.auxiliar.decrypt_all_sources import clean_title
from udemy.compat import time, sys
from udemy.extract import Udemy
from udemy.logger import logger
from udemy.shared import (
    UdemyCourse,
    UdemyCourses,
    UdemyChapters,
    UdemyLectures,
    UdemyLectureStream,
    UdemyLectureAssets,
    UdemyLectureSubtitles, UdemyQuizzes, UdemyQuizQuestion, UdemyLectureEncryptStreams,
)


class InternUdemyCourses(UdemyCourses, Udemy):
    def __init__(self, *args, **kwargs):
        super(InternUdemyCourses, self).__init__(*args, **kwargs)

    def _fetch_course(self):
        auth = {}
        if not self._cookies:
            auth = self._login(username=self._username, password=self._password)
        if not auth and self._cookies:
            auth = self._login(cookies=self._cookies)
        if auth.get("login") == "successful":
            logger.info(msg="Logged in successfully.", new_line=True)
            logger.info(msg="Fetching all enrolled course(s) url(s)..")
            self._courses = self._extract_subscribed_courses()
            time.sleep(1)
            logger.success(msg="Fetching all enrolled course(s) url(s).. ")
            self._logout()
        if auth.get("login") == "failed":
            logger.error(msg="Failed to login ..\n")
            sys.exit(0)


class InternUdemyCourse(UdemyCourse, Udemy):
    def __init__(self, *args, **kwargs):
        self._info = ""
        super(InternUdemyCourse, self).__init__(*args, **kwargs)

    def _fetch_course(self):
        if self._have_basic:
            return
        auth = {}
        if not self._cookies:
            auth = self._login(
                username=self._username,
                password=self._password,
                cache_session=self._cache_session,
            )
        if not auth and self._cookies:
            auth = self._login(cookies=self._cookies, cache_session=self._cache_session)
        if auth.get("login") == "successful":
            logger.info(msg="Logged in successfully.", new_line=True)
            logger.info(msg="Downloading course information ..")
            self._info = self._real_extract(
                self._url, skip_hls_stream=self._skip_hls_stream, chapter_start=self._chapter_start
            )
            time.sleep(1)
            logger.success(msg="Downloaded course information .. ")
            access_token = self._info["access_token"]
            self._id = self._info["course_id"]
            self._title = self._info["course_title"]
            self._chapters_count = self._info["total_chapters"]
            self._total_lectures = self._info["total_lectures"]
            self._total_quizzes = self._info["total_quizzes"]
            self._chapters = [
                InternUdemyChapter(z, access_token=access_token)
                for z in self._info["chapters"]
            ]
            logger.info(
                msg="Trying to logout now...",
                new_line=True,
            )
            if not self._cookies:
                self._logout()
            logger.info(
                msg="Logged out successfully.",
                new_line=True,
            )
            self._have_basic = True
        if auth.get("login") == "failed":
            logger.error(msg="Failed to login ..\n")
            sys.exit(0)


class InternUdemyChapter(UdemyChapters):
    def __init__(self, chapter, access_token=None):
        super(InternUdemyChapter, self).__init__()

        self._chapter_id = chapter["chapter_id"]
        self._chapter_title = clean_title(chapter["chapter_title"])

        self._chapter_index = chapter["chapter_index"]
        self._lectures_count = chapter.get("lectures_count", 0)
        self._question_count = chapter.get("quizzes_count", 0)
        self._lectures = (
            [
                InternUdemyLecture(z, access_token=access_token)
                for z in chapter["lectures"]
            ]
            if self._lectures_count > 0
            else []
        )

        self._quizzes = (
            [
                InternUdemyQuiz(z, access_token=access_token)
                for z in chapter["quizzes"]
            ]
            if self._question_count > 0
            else []
        )


class InternUdemyLecture(UdemyLectures):
    def __init__(self, lectures, access_token=None):
        super(InternUdemyLecture, self).__init__()
        self._access_token = access_token
        self._info = lectures

        self._lecture_id = self._info["lectures_id"]
        self._lecture_title = clean_title(self._info["lecture_title"])
        self._lecture_index = self._info["lecture_index"]

        self._subtitles_count = self._info.get("subtitle_count", 0)
        self._sources_count = self._info.get("sources_count", 0)
        self._assets_count = self._info.get("assets_count", 0)
        self._extension = self._info.get("extension")
        self._html_content = self._info.get("html_content")
        self._duration = self._info.get("duration")
        if self._duration:
            duration = int(self._duration)
            (mins, secs) = divmod(duration, 60)
            (hours, mins) = divmod(mins, 60)
            if hours == 0:
                self._duration = "%02d:%02d" % (mins, secs)
            else:
                self._duration = "%02d:%02d:%02d" % (hours, mins, secs)

        self._is_encrypted = self._info.get("is_encrypted", False)
        self._asset_id = self._info.get("asset_id", None)

    def _process_encrypted_sources(self):
        _sources = self._info.get("video_sources", [])
        encrypt_streams = (
            [InternUdemyLectureEncryptStreams(z, self) for z in _sources]
            if len(_sources) > 0
            else []
        )
        self._encrypt_streams = encrypt_streams
        # self._streams = sorted(streams, key=lambda k: k.quality)
        # self._streams = sorted(self._streams, key=lambda k: k.mediatype)

    def _process_streams(self):
        streams = (
            [InternUdemyLectureStream(z, self) for z in self._info["sources"]]
            if self._sources_count > 0
            else []
        )
        self._streams = sorted(streams, key=lambda k: k.quality)
        self._streams = sorted(self._streams, key=lambda k: k.mediatype)

    def _process_assets(self):
        assets = (
            [InternUdemyLectureAssets(z, self) for z in self._info["assets"]]
            if self._assets_count > 0
            else []
        )
        self._assets = assets

    def _process_subtitles(self):
        subtitles = (
            [InternUdemyLectureSubtitles(z, self) for z in self._info["subtitles"]]
            if self._subtitles_count > 0
            else []
        )
        self._subtitles = subtitles


class InternUdemyLectureEncryptStreams(UdemyLectureEncryptStreams):
    def __init__(self, sources, parent):
        super(InternUdemyLectureEncryptStreams, self).__init__(parent)
        self._mediatype = sources.get("type")
        self._extension = sources.get("extension")
        self._format_id = sources.get("format_id")
        self._token = parent._access_token
        height = sources.get("height", "0")
        width = sources.get("width", "0")
        self._resolution = "%sx%s" % (width, height)
        self._dimension = width, height
        self._quality = int(height)
        self._is_hls = "hls" in self._mediatype
        self._url = sources.get("download_url")


class InternUdemyLectureStream(UdemyLectureStream):
    def __init__(self, sources, parent):
        super(InternUdemyLectureStream, self).__init__(parent)

        self._mediatype = sources.get("type")
        self._extension = sources.get("extension")
        self._token = parent._access_token
        height = sources.get("height", "0")
        width = sources.get("width", "0")
        self._resolution = "%sx%s" % (width, height)
        self._dimension = width, height
        self._quality = int(height)
        self._is_hls = "hls" in self._mediatype
        self._url = sources.get("download_url")


class InternUdemyLectureAssets(UdemyLectureAssets):
    def __init__(self, assets, parent):
        super(InternUdemyLectureAssets, self).__init__(parent)

        self._mediatype = assets.get("type")
        self._extension = assets.get("extension")
        title = clean_title(assets.get("title", ""))
        if not title:
            title = assets.get("filename")
        if title and title.endswith(self._extension):
            ok = "{0:03d} ".format(parent._lecture_index) + title
            self._filename = ok
        else:
            ok = "{0:03d} ".format(parent._lecture_index) + assets.get("filename")
            self._filename = ok
        self._url = assets.get("download_url")


class InternUdemyLectureSubtitles(UdemyLectureSubtitles):
    def __init__(self, subtitles, parent):
        super(InternUdemyLectureSubtitles, self).__init__(parent)

        self._mediatype = subtitles.get("type")
        self._extension = subtitles.get("extension")
        self._language = subtitles.get("language")
        self._url = subtitles.get("download_url")


class InternUdemyQuiz(UdemyQuizzes):
    def __init__(self, quizzes, access_token=None):
        super(InternUdemyQuiz, self).__init__()
        self._access_token = access_token
        self._info = quizzes

        self._quiz_id = self._info["quiz_id"]
        self._quiz_title = clean_title(self._info["quiz_title"])
        self._question_count = self._info.get("quizzes_count", 0)

    def _process_questions(self):
        questions = (
            [InternUdemyQuizQuestion(self._info["questions"][i], i, self) for i in range(len(self._info["questions"]))]
            if self._question_count > 0
            else []
        )
        self._questions = questions


class InternUdemyQuizQuestion(UdemyQuizQuestion):
    LETTERS = ["a", "b", "c", "d", "e", "f", "g"]

    def __init__(self, question, index, parent):
        super(InternUdemyQuizQuestion, self).__init__(parent)
        self._index = index
        self._question = question

        self._class = question.get("_class")
        self._id = question.get("id")
        self._assessment_type = question.get("assessment_type")
        prompt = question.get("prompt")
        self._feedbacks = {self.LETTERS[i]: prompt.get("feedbacks", [])[i] for i in range(len(prompt.get("feedbacks", [])))}
        self._answers = {self.LETTERS[i]: prompt.get("answers", [])[i] for i in range(len(prompt.get("answers", [])))}
        self._explanation_html = prompt.get("explanation", "")

        self._correct_response = question.get("correct_response")
        self._section = question.get("section")
        self._question_plain = question.get("question_plain")

    def _process_related_lectures(self, lectures: List[UdemyLectures]):
        rel_lectures = []
        pending_lectures = self._question.get("related_lectures", [])
        for lec in lectures:
            if pending_lectures:
                _rel = pending_lectures[0]
                found = False
                for _rel in pending_lectures:
                    if _rel['id'] == lec.id:
                        rel_lectures.append(lec)
                        found = True
                        break
                if found:
                    pending_lectures.remove(_rel)
        self._related_lectures = rel_lectures
        return self._related_lectures
