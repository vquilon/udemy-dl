# pylint: disable=R,C
#!/usr/bin/env python3

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
import json
import subprocess

from udemy.auxiliar.decrypt_all_sources import clean_title
from udemy.compat import (
    re,
    os,
    sys,
    time,
    requests,
    conn_error,
    HEADERS,
)
from udemy.decryptor.utils import extract_kid, mux_process, decrypt
from udemy.ffmpeg import FFMPeg
from udemy.logger import logger
from udemy.utils import to_file, prepare_html


class Downloader(object):
    def __init__(self):
        self._url = None
        self._filename = None
        self._mediatype = None
        self._extension = None
        self._active = True
        self._is_hls = False
        self._token = None
        self._sess = requests.session()

    @property
    def url(self):
        """abac"""
        return self._url

    @property
    def token(self):
        return self._token

    @property
    def is_hls(self):
        return self._is_hls

    @property
    def mediatype(self):
        return self._mediatype

    @property
    def extension(self):
        return self._extension

    @property
    def filename(self):
        if not self._filename:
            self._filename = self._generate_filename()  # pylint: disable=E
        return self._filename

    def _generate_filename(self):  # pylint: disable=E
        pass

    def _write_external_links(self, filepath):
        retVal = {}
        savedirs, name = os.path.split(filepath)
        filename = u"external-assets-links.txt"
        filename = os.path.join(savedirs, filename)
        file_data = []
        if os.path.isfile(filename):
            file_data = [
                i.strip().lower()
                for i in open(filename, encoding="utf-8", errors="ignore")
                if i
            ]

        content = u"\n{}\n{}\n".format(name, self.url)
        if name.lower() not in file_data:
            retVal = to_file(filename, "a", content)
        return retVal

    def download(
        self,
        filepath="",
        quiet=False,
        callback=lambda *x: None,
    ):
        savedir = filename = ""
        retVal = {}

        if filepath and os.path.isdir(filepath):
            savedir, filename = (
                filepath,
                self.filename,
            )

        elif filepath:
            savedir, filename = os.path.split(filepath)

        else:
            filename = self.filename

        filepath = os.path.join(savedir, filename)
        if os.name == "nt" and len(filepath) > 250:
            filepath = "\\\\?\\{}".format(filepath)

        if self.mediatype == "external_link":
            return self._write_external_links(filepath)

        if filepath and filepath.endswith(".vtt"):
            filepath_vtt2srt = filepath.replace(".vtt", ".srt")
            if os.path.isfile(filepath_vtt2srt):
                retVal = {"status": "True", "msg": "already downloaded"}
                return retVal

        if os.path.isfile(filepath):
            retVal = {"status": "True", "msg": "already downloaded"}
            return retVal

        temp_filepath = filepath + ".part"

        if self.is_hls:
            temp_filepath = filepath.replace(".mp4", "")
            temp_filepath = temp_filepath + ".hls-part.mp4"
            retVal = FFMPeg(None, self.url, self.token, temp_filepath).download()
            if retVal:
                self._active = False
        else:
            bytes_to_be_downloaded = 0
            fmode, offset = "wb", 0
            chunksize, bytesdone, t0 = 16384, 0, time.time()
            headers = {"User-Agent": HEADERS.get("User-Agent"), "Accept-Encoding": None}
            if os.path.exists(temp_filepath):
                offset = os.stat(temp_filepath).st_size

            if offset:
                offset_range = "bytes={}-".format(offset)
                headers["Range"] = offset_range
                bytesdone = offset
                fmode = "ab"

            status_string = (
                "  {:,} Bytes [{:.2%}] received. Rate: [{:4.0f} "
                "KB/s].  ETA: [{:.0f} secs]"
            )

            try:
                try:
                    response = self._sess.get(
                        self.url, headers=headers, stream=True, timeout=10
                    )
                except conn_error as error:
                    return {
                        "status": "False",
                        "msg": "ConnectionError: %s" % (str(error)),
                    }
                if response.ok:
                    bytes_to_be_downloaded = total = int(
                        response.headers.get("Content-Length")
                    )
                    if bytesdone > 0:
                        bytes_to_be_downloaded = bytes_to_be_downloaded + bytesdone
                    total = bytes_to_be_downloaded
                    with open(temp_filepath, fmode) as media_file:
                        is_malformed = False
                        for chunk in response.iter_content(chunksize):
                            if not chunk:
                                break
                            media_file.write(chunk)
                            elapsed = time.time() - t0
                            bytesdone += len(chunk)
                            if elapsed:
                                try:
                                    rate = (
                                        (float(bytesdone) - float(offset)) / 1024.0
                                    ) / elapsed
                                    eta = (total - bytesdone) / (rate * 1024.0)
                                except ZeroDivisionError:
                                    is_malformed = True
                                    try:
                                        os.unlink(temp_filepath)
                                    except Exception:  # pylint: disable=W
                                        pass
                                    retVal = {
                                        "status": "False",
                                        "msg": "ZeroDivisionError : it seems, lecture has malfunction or is zero byte(s) ..",
                                    }
                                    break
                            else:
                                rate = 0
                                eta = 0

                            if not is_malformed:
                                progress_stats = (
                                    bytesdone,
                                    bytesdone * 1.0 / total,
                                    rate,
                                    eta,
                                )

                                if not quiet:
                                    status = status_string.format(*progress_stats)
                                    sys.stdout.write("\r" + status + " " * 4 + "\r")
                                    sys.stdout.flush()

                                if callback:
                                    callback(total, *progress_stats)
                if not response.ok:
                    code = response.status_code
                    reason = response.reason
                    retVal = {
                        "status": "False",
                        "msg": "Udemy returned HTTP Code %s: %s" % (code, reason),
                    }
                    response.close()
            except KeyboardInterrupt as error:
                raise error
            except Exception as error:  # pylint: disable=W
                retVal = {"status": "False", "msg": "Reason : {}".format(str(error))}
                return retVal
            # # check if file is downloaded completely
            if os.path.isfile(temp_filepath):
                total_bytes_done = os.stat(temp_filepath).st_size
                if total_bytes_done == bytes_to_be_downloaded:
                    self._active = False
                # if total_bytes_done < bytes_to_be_downloaded:
                #     # set active to be True as remaining bytes to be downloaded
                #     self._active = True
                #     # try downloading back again remaining bytes until we download completely
                #     self.download(filepath=filepath, quiet=quiet)

        if not self._active:
            os.rename(temp_filepath, filepath)
            retVal = {"status": "True", "msg": "download"}

        return retVal


class EncryptDownloader(object):
    def __init__(self):
        self._url = None
        self._filename = None
        self._mediatype = None
        self._extension = None
        self._active = True
        self._is_hls = False
        self._token = None
        self._sess = requests.session()

    @property
    def url(self):
        """abac"""
        return self._url

    @property
    def token(self):
        return self._token

    @property
    def is_hls(self):
        return self._is_hls

    @property
    def mediatype(self):
        return self._mediatype

    @property
    def extension(self):
        return self._extension

    @property
    def filename(self):
        if not self._filename:
            self._filename = self._generate_filename()  # pylint: disable=E
        return self._filename

    def _generate_filename(self):  # pylint: disable=E
        pass

    def handle_segments(self,  keep_encrypted, do_decrypt, keys_decryptors, url, format_id, video_title, output_path, concurrent_connections=10):
        lecture_file_path = os.path.join(output_path, self.filename)

        file_name = lecture_file_path.replace("%", "").replace(".mp4", "")
        video_filepath_enc = file_name + ".encrypted.mp4"
        audio_filepath_enc = file_name + ".encrypted.m4a"
        video_filepath_dec = file_name + ".decrypted.mp4"
        audio_filepath_dec = file_name + ".decrypted.m4a"
        logger.info(msg="> Downloading Lecture Tracks...", new_line=True)
        ret_code = subprocess.Popen([
            "yt-dlp", "--force-generic-extractor", "--allow-unplayable-formats",
            "--concurrent-fragments", f"{concurrent_connections}", "--downloader",
            "aria2c", "--fixup", "never", "-k", "-o", f"{file_name}.encrypted.%(ext)s",
            "-f", format_id, f"{url}"
        ]).wait()
        logger.info(msg="> Lecture Tracks Downloaded", new_line=True)

        logger.info(msg="Return code: " + str(ret_code))
        if ret_code != 0:
            logger.error(msg="Return code from the downloader was non-0 (error), skipping!", new_line=True)
            return

        video_kid = extract_kid(video_filepath_enc)
        logger.info(msg="KID for video file is: " + video_kid, new_line=True)

        audio_kid = extract_kid(audio_filepath_enc)
        logger.info(msg="KID for audio file is: " + audio_kid, new_line=True)

        try:
            if do_decrypt and keys_decryptors:
                decrypt(keys_decryptors, video_kid, video_filepath_enc, video_filepath_dec)
                decrypt(keys_decryptors, audio_kid, audio_filepath_enc, audio_filepath_dec)
                mux_process(video_title, video_filepath_dec, audio_filepath_dec, lecture_file_path)
            # else:
            #     self.mux_process(file_name+"video_audio_encrypted.mp4", video_filepath_enc, audio_filepath_enc, output_path)
            if not keep_encrypted and os.path.isfile(lecture_file_path):
                os.remove(video_filepath_enc)
                os.remove(audio_filepath_enc)

            if do_decrypt and keys_decryptors:
                os.remove(video_filepath_dec)
                os.remove(audio_filepath_dec)
        except Exception as e:
            print(f"Error: ", e)


class UdemyCourses(object):
    def __init__(self, username="", password="", cookies="", basic=True):

        self._courses = []
        self._username = username
        self._password = password
        self._cookies = cookies

        if basic:
            self._fetch_course()

    def _fetch_course(self):
        raise NotImplementedError

    def dump_courses(self, filepath):
        if not filepath:
            filepath = os.path.join(os.getcwd(), "enrolled-courses.txt")
        with open(filepath, "w") as fd:
            courses_urls = "\n".join(self._courses)
            fd.write(courses_urls)
        return filepath

    @property
    def courses(self):
        return self._courses


class UdemyCourse(object):
    def __init__(
        self,
        url,
        username="",
        password="",
        cookies="",
        basic=True,
        skip_hls_stream=False,
        cache_session=False,
        callback=None,
        chapter_start=0
    ):

        self._url = url
        self._username = username
        self._password = password
        self._cookies = cookies
        self._cache_session = cache_session
        self._skip_hls_stream = skip_hls_stream
        self._callback = callback or (lambda x: None)
        self._have_basic = False

        self._id = None
        self._title = None
        self._chapters_count = None
        self._total_lectures = None
        self._total_quizzes = None

        self._chapters = []

        self._chapter_start = chapter_start

        if basic:
            self._fetch_course()

        whole_lectures = []
        if self._chapters:
            for c in self._chapters:
                for l in c.get_lectures():
                    whole_lectures.append(l)
            for c in self._chapters:
                for q in c.get_quizzes():
                    q.update_related_questions_lectures(whole_lectures)

    def _fetch_course(self):
        raise NotImplementedError

    @property
    def id(self):
        if not self._id:
            self._fetch_course()
        return self._id

    @property
    def title(self):
        if not self._title:
            self._fetch_course()
        return self._title

    @property
    def chapters(self):
        if not self._chapters_count:
            self._fetch_course()
        return self._chapters_count

    @property
    def lectures(self):
        if not self._total_lectures:
            self._fetch_course()
        return self._total_lectures

    @property
    def quizzes(self):
        if not self._total_quizzes:
            self._fetch_course()
        return self._total_quizzes

    def get_chapters(self, chapter_number=None, chapter_start=None, chapter_end=None):
        if not self._chapters:
            self._fetch_course()
        if (
            chapter_number
            and not chapter_start
            and not chapter_end
            and isinstance(chapter_number, int)
        ):
            is_okay = bool(0 < chapter_number <= self.chapters)
            if is_okay:
                self._chapters = [self._chapters[chapter_number - 1]]
        if chapter_start and not chapter_number and isinstance(chapter_start, int):
            is_okay = bool(0 < chapter_start <= self.chapters)
            if is_okay:
                self._chapters = self._chapters[chapter_start - 1 :]
        if chapter_end and not chapter_number and isinstance(chapter_end, int):
            is_okay = bool(0 < chapter_end <= self.chapters)
            if is_okay:
                self._chapters = self._chapters[: chapter_end - 1]
        return self._chapters


class UdemyChapters(object):
    def __init__(self):

        self._chapter_id = None
        self._chapter_index = None
        self._chapter_title = None
        self._lectures_count = None
        self._question_count = None

        self._lectures = []
        self._quizzes = []

    def __repr__(self):
        chapter = "{title}".format(title=self.title)
        return chapter

    @property
    def id(self):
        return self._chapter_id

    @property
    def index(self):
        return self._chapter_index

    @property
    def title(self):
        return self._chapter_title

    @property
    def lectures(self):
        return self._lectures_count

    @property
    def quizzes(self):
        return self._question_count

    def get_lectures(self, lecture_number=None, lecture_start=None, lecture_end=None):
        if (
            lecture_number
            and not lecture_start
            and not lecture_end
            and isinstance(lecture_number, int)
        ):
            is_okay = bool(0 < lecture_number <= self.lectures)
            if is_okay:
                self._lectures = [self._lectures[lecture_number - 1]]
        if lecture_start and not lecture_number and isinstance(lecture_start, int):
            is_okay = bool(0 < lecture_start <= self.lectures)
            if is_okay:
                self._lectures = self._lectures[lecture_start - 1 :]
        if lecture_end and not lecture_number and isinstance(lecture_end, int):
            is_okay = bool(0 < lecture_end <= self.lectures)
            if is_okay:
                self._lectures = self._lectures[: lecture_end - 1]
        return self._lectures

    def get_quizzes(self, quiz_number=None, quiz_start=None, quiz_end=None):
        if (
                quiz_number
                and not quiz_start
                and not quiz_end
                and isinstance(quiz_number, int)
        ):
            is_okay = bool(0 < quiz_number <= self.quizzes)
            if is_okay:
                self._quizzes = [self._quizzes[quiz_number - 1]]
        if quiz_start and not quiz_number and isinstance(quiz_start, int):
            is_okay = bool(0 < quiz_start <= self.lectures)
            if is_okay:
                self._quizzes = self._quizzes[quiz_start - 1:]
        if quiz_end and not quiz_number and isinstance(quiz_end, int):
            is_okay = bool(0 < quiz_end <= self.lectures)
            if is_okay:
                self._quizzes = self._quizzes[: quiz_end - 1]
        return self._quizzes


class UdemyLectures(object):
    def __init__(self):

        self._best = None
        self._duration = None
        self._extension = None
        self._lecture_id = None
        self._lecture_title = None
        self._lecture_index = None
        self._sources_count = None
        self._assets_count = None
        self._subtitles_count = None
        self._html_content = None

        self._is_encrypted = None
        self._asset_id = None

        self._assets = []
        self._streams = []
        self._subtitles = []

        self._encrypt_streams = []

    def __repr__(self):
        lecture = "{title}".format(title=self.title)
        return lecture

    @property
    def id(self):
        return self._lecture_id

    @property
    def encrypt_streams(self):
        if not self._encrypt_streams:
            self._process_encrypted_sources()  # pylint: disable=E
        return self._encrypt_streams

    @property
    def is_encrypted(self):
        return self._is_encrypted

    @property
    def index(self):
        return self._lecture_index

    @property
    def title(self):
        return self._lecture_title

    @property
    def html(self):
        return self._html_content

    @property
    def duration(self):
        return self._duration

    @property
    def extension(self):
        return self._extension

    @property
    def assets(self):
        if not self._assets:
            self._process_assets()  # pylint: disable=E
        return self._assets

    @property
    def streams(self):
        if not self._streams:
            self._process_streams()  # pylint: disable=E
        return self._streams

    @property
    def subtitles(self):
        if not self._subtitles:
            self._process_subtitles()  # pylint: disable=E
        return self._subtitles

    def _getbest(self):
        streams = self.streams or self.encrypt_streams
        if not streams:
            return None

        def _sortkey(x, keyres=0, keyftype=0):
            keyres = int(x.resolution.split("x")[0])
            keyftype = x.extension
            st = (keyftype, keyres)
            return st

        if len(self.encrypt_streams) > 0:
            self._best = streams[-1] # last index is the best quality
            self._best = max([i for i in streams if not i.is_hls], key=_sortkey)
        else:
            return None

        return self._best

    def getbest(self):
        return self._getbest()

    def get_quality(self, quality, preferred_mediatype="video"):
        lecture = self.getbest()
        _temp = {}
        streams = self.streams or self.encrypt_streams or []

        if self.encrypt_streams:
            lecture = min(self.encrypt_streams, key=lambda x: abs(int(x.height) - quality))

        for s in streams:
            if isinstance(quality, int) and s.quality == quality:
                mediatype = s.mediatype
                _temp[mediatype] = s
        if _temp:
            if preferred_mediatype in _temp:
                lecture = _temp[preferred_mediatype]
            else:
                lecture = list(_temp.values()).pop()
        return lecture

    def dump(self, filepath):
        retVal = {}
        filename = os.path.join(filepath, self.title)
        filename += ".html"

        if os.path.isfile(filename):
            retVal = {"status": "True", "msg": "already downloaded"}
            return retVal
        contents = prepare_html(self.title, self.html)
        retVal = to_file(filename, "wb", contents, None, None)
        return retVal


class UdemyLectureEncryptStreams(EncryptDownloader):
    def __init__(self, parent):
        self._mediatype = None
        self._quality = None
        self._resolution = None
        self._dimension = None
        self._extension = None
        self._url = None

        self._parent = parent
        self._filename = None
        self._fsize = None
        self._active = False
        self._is_hls = False
        self._token = None

        self._format_id = None

        EncryptDownloader.__init__(self)

    def _generate_filename(self):
        ok = re.compile(r'[^\\/:*?"<>|]')
        filename = "".join(x if ok.match(x) else "_" for x in self.title)
        filename += "." + self.extension
        return filename

    @property
    def parent(self):
        return self._parent

    @property
    def format_id(self):
        return self._format_id

    @property
    def resolution(self):
        return self._resolution

    @property
    def quality(self):
        return self._quality

    @property
    def url(self):
        return self._url

    @property
    def is_hls(self):
        return self._is_hls

    @property
    def token(self):
        return self._token

    @property
    def id(self):
        return self._parent.id

    @property
    def dimension(self):
        return self._dimension

    @property
    def extension(self):
        return self._extension

    @property
    def filename(self):
        if not self._filename:
            self._filename = self._generate_filename()
        return self._filename

    @property
    def title(self):
        return self._parent.title

    @property
    def mediatype(self):
        return self._mediatype


class UdemyLectureStream(Downloader):
    def __init__(self, parent):

        self._mediatype = None
        self._quality = None
        self._resolution = None
        self._dimension = None
        self._extension = None
        self._url = None

        self._parent = parent
        self._filename = None
        self._fsize = None
        self._active = False
        self._is_hls = False
        self._token = None

        Downloader.__init__(self)

    def __repr__(self):
        out = "%s:%s@%s" % (self.mediatype, self.extension, self.quality)
        return out

    def _generate_filename(self):
        ok = re.compile(r'[^\\/:*?"<>|]')
        filename = "".join(x if ok.match(x) else "_" for x in self.title)
        filename += "." + self.extension
        return filename

    @property
    def parent(self):
        return self._parent

    @property
    def resolution(self):
        return self._resolution

    @property
    def quality(self):
        return self._quality

    @property
    def url(self):
        return self._url

    @property
    def is_hls(self):
        return self._is_hls

    @property
    def token(self):
        return self._token

    @property
    def id(self):
        return self._parent.id

    @property
    def dimension(self):
        return self._dimension

    @property
    def extension(self):
        return self._extension

    @property
    def filename(self):
        if not self._filename:
            self._filename = self._generate_filename()
        return self._filename

    @property
    def title(self):
        return self._parent.title

    @property
    def mediatype(self):
        return self._mediatype

    def get_filesize(self):
        if not self._fsize:
            headers = {"User-Agent": HEADERS.get("User-Agent")}
            try:
                with requests.get(self.url, stream=True, headers=headers) as resp:
                    if resp.ok:
                        self._fsize = float(resp.headers.get("Content-Length", 0))
                    if not resp.ok:
                        self._fsize = 0
            except conn_error:
                self._fsize = 0
        return self._fsize


class UdemyLectureAssets(Downloader):
    def __init__(self, parent):

        self._extension = None
        self._mediatype = None
        self._url = None

        self._parent = parent
        self._filename = None
        self._fsize = None
        self._active = False

        Downloader.__init__(self)

    def __repr__(self):
        out = "%s:%s@%s" % (self.mediatype, self.extension, self.extension)
        return out

    def _generate_filename(self):
        ok = re.compile(r'[^\\/:*?"<>|]')
        filename = "".join(x if ok.match(x) else "_" for x in self.title)
        filename += ".{}".format(self.extension)
        return filename

    @property
    def id(self):
        return self._parent.id

    @property
    def url(self):
        return self._url

    @property
    def extension(self):
        return self._extension

    @property
    def title(self):
        return self._parent.title

    @property
    def filename(self):
        if not self._filename:
            self._filename = self._generate_filename()
        return self._filename

    @property
    def mediatype(self):
        return self._mediatype

    def get_filesize(self):
        if not self._fsize:
            headers = {"User-Agent": HEADERS.get("User-Agent")}
            try:
                with requests.get(self.url, stream=True, headers=headers) as resp:
                    if resp.ok:
                        self._fsize = float(resp.headers.get("Content-Length", 0))
                    if not resp.ok:
                        self._fsize = 0
            except conn_error:
                self._fsize = 0
        return self._fsize


class UdemyLectureSubtitles(Downloader):
    def __init__(self, parent):

        self._mediatype = None
        self._extension = None
        self._language = None
        self._url = None

        self._parent = parent
        self._filename = None
        self._fsize = None
        self._active = False

        Downloader.__init__(self)

    def __repr__(self):
        out = "%s:%s@%s" % (self.mediatype, self.language, self.extension)
        return out

    def _generate_filename(self):
        ok = re.compile(r'[^\\/:*?"<>|]')
        filename = "".join(x if ok.match(x) else "_" for x in self.title)
        filename += ".{}.{}".format(self.language, self.extension)
        return filename

    @property
    def id(self):
        return self._parent.id

    @property
    def url(self):
        return self._url

    @property
    def extension(self):
        return self._extension

    @property
    def language(self):
        return self._language

    @property
    def title(self):
        return self._parent.title

    @property
    def filename(self):
        if not self._filename:
            self._filename = self._generate_filename()
        return self._filename

    @property
    def mediatype(self):
        return self._mediatype

    def get_subtitle(self, language, preferred_language="en"):
        _temp = {}
        subtitles = self._parent.subtitles
        for sub in subtitles:
            if sub.language == language:
                _temp[sub.language] = [sub]
        if _temp:
            # few checks to keep things simple :D
            if language in _temp:
                _temp = _temp[language]
            elif preferred_language in _temp and not language in _temp:
                _temp = _temp[preferred_language]
        if not _temp:
            _temp = subtitles
        return _temp

    def get_filesize(self):
        if not self._fsize:
            headers = {"User-Agent": HEADERS.get("User-Agent")}
            try:
                with requests.get(self.url, stream=True, headers=headers) as resp:
                    if resp.ok:
                        self._fsize = float(resp.headers.get("Content-Length", 0))
                    if not resp.ok:
                        self._fsize = 0
            except conn_error:
                self._fsize = 0
        return self._fsize


# PLUGIN: QUIZZES
class UdemyQuizzes(object):
    def __init__(self):
        self._quiz_id = None
        self._quiz_title = None
        self._question_count = None

        self._quiz_index = None

        self._questions = []

    def __repr__(self):
        quiz = "{title}".format(title=self.title)
        return quiz

    @property
    def id(self):
        return self._quiz_id

    @property
    def title(self):
        return self._quiz_title

    @property
    def quiz_index(self):
        return self._quiz_index

    @quiz_index.setter
    def quiz_index(self, quiz_index):
        self._quiz_index = quiz_index

    @property
    def questions(self):
        if not self._questions:
            self._process_questions()
        return self._questions

    def update_related_questions_lectures(self, lectures):
        self._questions = self.questions
        for q in self._questions:
            q.update_related_lectures(lectures)


    def _clean(self, text):
        ok = re.compile(r'[^\\/:*?"<>|]')
        text = "".join(x if ok.match(x) else "_" for x in text)
        text = re.sub(r"\.+$", "", text.strip())
        return text

    def dump(self, filepath):
        filename = os.path.join(filepath, f"{self._quiz_title}")
        filename += ".json"
        # filename = self._clean(filename)
        if os.path.isfile(filename):
            retVal = {"status": "True", "msg": "already downloaded"}
            return retVal
        questions = [x.mapper() for x in self._questions]
        content = {
            "id": self._quiz_id,
            "title": self._quiz_title,
            "questions": questions
        }
        retVal = to_file(filename, "w", json.dumps(content), None, None)
        return retVal


class UdemyQuizQuestion(object):
    def __init__(self, parent):
        self._parent = parent

        self._index = 0
        self._class = None
        self._id = None
        self._assessment_type = None
        self._feedbacks = []
        self._answers = []
        self._correct_response = []
        self._section = None
        self._question_plain = None
        self._related_lectures = []

    @property
    def id(self):
        return self._id

    @property
    def index(self):
        return self._index

    @property
    def title(self):
        return self._question_plain

    @property
    def related_lectures(self):
        return self._related_lectures

    def update_related_lectures(self, lectures):
        self._related_lectures = self._process_related_lectures(lectures)

    def mapper(self):
        return {
            "_class": self._class,
            "id": self._id,
            "assessment_type": self._assessment_type,
            "feedbacks": self._feedbacks,
            "question": self._question_plain,
            "answers": self._answers,
            "correct_response": self._correct_response,
            "section": self._section,
            "related_lectures": [
                {
                    "id": x.id,
                    "title": x.title,
                    "index": x.index
                }
                for x in self._related_lectures
            ]
        }