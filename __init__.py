# NEON AI (TM) SOFTWARE, Software Development Kit & Application Framework
# All trademark and other rights reserved by their respective owners
# Copyright 2008-2022 Neongecko.com Inc.
# Contributors: Daniel McKnight, Guy Daniels, Elon Gasper, Richard Leeds,
# Regina Bloomstine, Casimiro Ferreira, Andrii Pernatii, Kirill Hrymailo
# BSD-3 License
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from this
#    software without specific prior written permission.
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS  BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA,
# OR PROFITS;  OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE,  EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# Copyright 2016, Mycroft AI Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
from os.path import exists
import wave
import datetime
import psutil

from adapt.intent import IntentBuilder
from neon_utils.file_utils import get_most_recent_file_in_dir
from neon_utils.message_utils import request_from_mobile
from time import sleep
from lingua_franca.format import nice_duration
from neon_utils.signal_utils import create_signal, check_for_signal
from neon_utils.skills.neon_skill import NeonSkill, LOG
from neon_utils.user_utils import get_message_user, get_user_prefs
from ovos_utils.xdg_utils import xdg_data_home
from mycroft.audio import wait_while_speaking
from mycroft.util import record, play_wav, create_daemon
from mycroft.util.parse import extract_datetime
from mycroft.util.time import now_local

try:
    import tkinter as tk
    import tkinter.simpledialog as dialog_box
except ImportError:
    tk = None
    dialog_box = None


class AudioRecordSkill(NeonSkill):
    def __init__(self):
        super(AudioRecordSkill, self).__init__("AudioRecordSkill")
        self.play_process = None
        self.record_process = None
        self.start_time = now_local()
        self.min_free_disk = 100
        self.rate = 16000
        self.channels = 1
        self.duration = -1
        self.file_path = ''
        self.file_ext = '.wav'
        self.filename = None

        self._record_dir = None
        self.append_recording = ""

    @property
    def record_dir(self):
        if not self._record_dir:
            self._init_record_dir()
        return self._record_dir

    @property
    def default_duration(self):
        return int(self.settings['default_duration'])

    @property
    def last_recording(self):
        try:
            return get_most_recent_file_in_dir(self.record_dir, '.wav')
        except Exception as e:
            LOG.error(e)
            return ""

    def _init_record_dir(self):
        self._record_dir = os.path.expanduser(
            self.settings.get('record_dir') or
            os.path.join(xdg_data_home(), "neon", "neon_recordings"))
        if not os.path.exists(self._record_dir):
            os.makedirs(self._record_dir)

    def initialize(self):
        intent = IntentBuilder("AudioRecordSkillIntent")\
            .optionally("ResumeKeyword").require("AudioRecordSkillKeyword")\
            .optionally("Neon").build()
        self.register_intent(intent, self.handle_record)

        intent = IntentBuilder("AltAudioRecordSkillIntent")\
            .require("Record").require("Audio").optionally("Neon").build()
        self.register_intent(intent, self.handle_record)

        intent = IntentBuilder('AudioRecordSkillPlayIntent')\
            .require('AudioRecordSkillPlayVerb') \
            .require('AudioRecordSkillKeyword').optionally("Neon").build()
        self.register_intent(intent, self.handle_play)

        intent = IntentBuilder('AudioRecordSkillDeleteIntent')\
            .require('AudioRecordSkillDeleteVerb') \
            .require('AudioRecordSkillKeyword').optionally("Neon").build()
        self.register_intent(intent, self.handle_delete)

        intent = IntentBuilder('AudioRecordListIntent')\
            .require('AudioRecordSkillListKeyword')\
            .optionally("Neon").build()
        self.register_intent(intent, self.handle_list)

    def remaining_time(self):
        return self.duration - (now_local() - self.start_time).total_seconds()

    def has_free_disk_space(self):
        space = (self.remaining_time() * self.channels *
                 self.rate / 1024 / 1024)
        free_mb = psutil.disk_usage('/')[2] / 1024 / 1024
        return free_mb - space > self.min_free_disk

    @staticmethod
    def stop_process(process):
        if process.poll() is None:  # None means still running
            process.terminate()
            # No good reason to wait, plus it interferes with
            # how stop button on the Mark 1 operates.
            # process.wait()
            return True
        else:
            return False

    def handle_list(self, message):
        # if (self.check_for_signal("skip_wake_word", -1) and message.data.get("Neon")) \
        #         or not self.check_for_signal("skip_wake_word", -1) or self.check_for_signal("CORE_neonInUtterance"):
        if self.neon_in_request(message):
            self.speak("I found the following recordings:", private=True)
            list_of_files = ""
            for file in os.listdir(self.record_dir):
                filename = str(file.split('.')[0])
                LOG.debug(filename)
                if any(c.isalpha() for c in filename):
                    list_of_files = ", ".join([list_of_files, filename])
            self.speak(list_of_files.lstrip(', '), private=True)

    def handle_delete(self, message):
        LOG.debug(message.data)
        user = get_message_user(message)
        filename = self.get_filename(message.data.get('utterance'), user)
        if os.path.isfile(os.path.join(self.record_dir, filename)):
            self.file_path = os.path.join(self.record_dir, filename)
            try:
                os.remove(self.file_path)
                self.speak(f"{filename} recording removed.", private=True)
            except Exception as e:
                LOG.error(e)
        else:
            self.file_path = get_most_recent_file_in_dir(self.record_dir, self.file_ext)
            # if (self.check_for_signal("skip_wake_word", -1) and message.data.get("Neon")) \
            #         or not self.check_for_signal("skip_wake_word", -1):
            if not exists(self.file_path):
                if not get_user_prefs(message)['response_mode'].get('limit_dialog'):
                    self.speak_dialog('audio.record.no.recording', private=True)
                else:
                    self.speak("No audio recordings found", private=True)
            else:
                try:
                    os.remove(self.file_path)
                    if not get_user_prefs(message)['response_mode'].get('limit_dialog'):
                        self.speak_dialog('audio.record.removed', private=True)
                    else:
                        self.speak("Most recent audio recording removed.", private=True)
                except Exception as e:
                    LOG.error(e)

    # Standard Stop handler
    def stop(self):
        # self.disable_intent("AR_ConfirmYes")
        # self.disable_intent("AR_ConfirmNo")
        if self.record_process:
            self.end_recording()
            return True
        if self.play_process:
            self.end_playback()
            return True
        return False

    # Show a countdown using the eyes
    def render_countdown(self, r_fore, g_fore, b_fore):
        pass
        # display_owner = self.enclosure.display_manager.get_active()
        # if display_owner == "":
        #     # Initialization, first time we take ownership
        #     self.enclosure.mouth_reset()  # clear any leftover bits
        #     self.enclosure.eyes_color(r_fore, g_fore, b_fore)  # foreground
        #     self.last_index = 24
        #
        # if display_owner == "AudioRecordSkill":
        #     remaining_pct = self.remaining_time() / self.settings["duration"]
        #     fill_to_index = int(24 * remaining_pct)
        #     while self.last_index > fill_to_index:
        #         if self.last_index < 24 and self.last_index > -1:
        #             # fill background with gray
        #             self.enclosure.eyes_setpixel(self.last_index, 64, 64, 64)
        #         self.last_index -= 1

    ######################################################################
    # Recording
    def handle_record(self, message):
        # if (self.check_for_signal("skip_wake_word", -1) and message.data.get("Neon")) \
        #         or not self.check_for_signal("skip_wake_word", -1) or self.check_for_signal("CORE_neonInUtterance"):
        if self.neon_in_request(message):
            utterance = message.data.get('utterance')
            user = get_message_user(message)
            # user = None
            # if self.server:
            #     user = nick(message.context["flac_filename"])

            # Calculate how long to record
            self.start_time = now_local()
            stop_time, _ = extract_datetime(utterance, lang=self.lang)
            self.duration = (stop_time - self.start_time).total_seconds()
            if self.duration <= 0:
                self.duration = -1
            else:
                self.duration = round(self.duration)
                # self.duration = self.default_duration  # default recording duration

            if message.data.get("ResumeKeyword"):
                file_to_continue = os.path.splitext(os.path.basename(self.last_recording))[0]
                self.speak(f"I will append this to {file_to_continue}", private=True)
                self.append_recording = self.last_recording
                create_signal("AR_AppendRecording")
                self.filename = file_to_continue + "__continued"
                self.start_recording(message)
            else:
                # Get filename
                filename = self.get_filename(utterance, user)

                if request_from_mobile(message):
                    # self.speak("MOBILE-INTENT AUDIO&name=" + filename + "&duration=" + str(self.duration))
                    self.speak("Audio recording started", private=True)
                    # self.mobile_skill_intent("play_recording", {"name": filename,
                    #                                             "duration": self.duration}, message)
                    # self.socket_io_emit('recorder', f"&name={filename}&duration={self.duration}",
                    #                     message.context["flac_filename"])
                # TODO: If Server?
                else:
                    self.confirm_filename(filename, message)
                # # Throw away any previous recording
                # try:
                #     os.remove(self.file_path)
                # except Exception as e:
                #     LOG.error(e)

    def start_recording(self, message=None):
        # TODO: Server handle this? DM
        self.file_path = os.path.join(self.record_dir,  f"{self.filename}{self.file_ext}")
        LOG.info(self.file_path)
        if os.path.isfile(self.file_path):
            i = 2
            test_name = None
            while os.path.isfile(self.file_path):
                test_name = self.filename + " " + str(i)
                self.file_path = os.path.join(self.record_dir, f"{test_name}{self.file_ext}")
                i += 1
            self.speak_dialog("FileExists", {"name": self.filename, "new_name": test_name},
                              message=message, private=True)
        if self.has_free_disk_space():
            if self.duration == -1:
                self.speak("Audio recording started. Say stop when you are done.", message=message, private=True)
            else:
                record_for = nice_duration(self.duration)
                # record_for = self.get_nice_duration(self.duration)
                if not get_user_prefs(message)['response_mode'].get('limit_dialog'):
                    self.speak_dialog('audio.record.start.duration', {'duration': record_for},
                                      message=message, private=True)
                else:
                    self.speak("Audio recording for {} seconds initialized".format(record_for),
                               message=message, private=True)

            # Initiate recording
            wait_while_speaking()
            self.start_time = now_local()   # recalc after speaking completes
            self.record_process = record(self.file_path,
                                         int(self.duration),
                                         self.rate,
                                         self.channels)
            # TODO: record doesn't handle server DM
            # self.enclosure.eyes_color(255, 0, 0)  # set color red
            # self.last_index = 24
            self.schedule_repeating_event(self.recording_feedback, None, 1, name='RecordingFeedback')
        else:
            if not get_user_prefs(message)['response_mode'].get('limit_dialog'):
                self.speak_dialog("audio.record.disk.full", message=message, private=True)
            else:
                self.speak("You have reached the maximum disk usage. Free some disk space to record an audio",
                           message=message, private=True)

    def recording_feedback(self):
        if not self.record_process:
            self.end_recording()
            return

        # Show recording countdown
        # self.render_countdown(255, 0, 0)

        # Verify there is still adequate disk space to continue recording
        if self.record_process.poll() is None:
            if not self.has_free_disk_space():
                # Out of space
                self.end_recording()
                if not get_user_prefs()['response_mode'].get('limit_dialog'):
                    self.speak_dialog("audio.record.disk.full", private=True)
                else:
                    self.speak("You have reached the maximum disk usage. Free some disk space to record audio.",
                               private=True)

        else:
            # Recording ended for some reason
            self.end_recording()

    def end_recording(self):
        self.cancel_scheduled_event('RecordingFeedback')

        if self.record_process:
            # Stop recording
            self.stop_process(self.record_process)
            self.record_process = None
            # Calc actual recording duration
            self.duration = (now_local() - self.start_time).total_seconds()
            if check_for_signal("AR_AppendRecording"):
                output_filename = os.path.basename(self.append_recording)
                os.rename(self.append_recording, os.path.join(self.record_dir, "first_file" + self.file_ext))
                self.speak(f"Appending audio to {output_filename}", private=True)
                input_files = [os.path.join(self.record_dir, "first_file" + self.file_ext),
                               os.path.join(self.record_dir, self.filename + self.file_ext)]
                wav_data = []
                for file in input_files:
                    audio = wave.open(file, 'rb')
                    wav_data.append([audio.getparams(), audio.readframes(audio.getnframes())])
                    audio.close()
                    os.remove(file)
                out_file = wave.open(os.path.join(self.record_dir, output_filename), 'wb')
                out_file.setparams(wav_data[0][0])
                out_file.writeframes(wav_data[0][1])
                out_file.writeframes(wav_data[1][1])
                out_file.close()
                self.filename = output_filename
                self.append_recording = ""
            else:
                self.speak("Recording ended. You can say 'resume recording for 30 seconds' to add more.", private=True)

        # TODO: Process audio file (normalize levels, trim silence) DM
        file_to_upload = os.path.join(self.record_dir, self.filename + self.file_ext)
        LOG.debug(file_to_upload)
        # TODO: Upload this to server if signed in (desktop)...

    ######################################################################
    # Playback
    def handle_play(self, message):
        # if (self.check_for_signal("skip_wake_word", -1) and message.data.get("Neon")) \
        #         or not self.check_for_signal("skip_wake_word", -1) or self.check_for_signal("CORE_neonInUtterance"):
        if self.neon_in_request(message):
            utterance = message.data.get('utterance')
            user = get_message_user(message)
            # user = None
            # if self.server:
            #     user = nick(message.context["flac_filename"])
            to_find = self.get_filename(utterance, user)

            if request_from_mobile(message):
                self.speak("Playing audio", private=True)
                # if to_find:
                #     # self.speak("MOBILE-INTENT PLAY_AUDIO&name=" + to_find)
                #     self.mobile_skill_intent("play_recording", {"name": to_find}, message)
                #     # self.socket_io_emit('play_recording', f"&name={to_find}", message.context["flac_filename"])
                # else:
                #     # self.speak("MOBILE-INTENT PLAY_AUDIO&name=_")
                #     self.mobile_skill_intent("play_recording", {"name": '_'}, message)
                #     # self.socket_io_emit('play_recording', "&name=_", message.context["flac_filename"])
            else:
                if to_find:
                    self.file_path = self.get_recording(to_find)

                if exists(self.file_path):
                    self.speak("Here is your requested recording.", private=True)
                    # This will speak overlapping playback
                    sleep(2)
                    # Initialize for playback
                    self.start_time = now_local()

                    # Playback the recording, with visual countdown
                    self.play_process = play_wav(self.file_path)
                    # self.enclosure.eyes_color(64, 255, 64)  # set color greenish
                    # self.last_index = 24
                    # TODO: This works, but datetime should be spec'd
                    self.schedule_repeating_event(self.playback_feedback, None, 1, name='PlaybackFeedback')
                elif get_most_recent_file_in_dir(self.record_dir, self.file_ext):
                    self.speak("Here is your most recent recording.", private=True)
                    # This will speak overlapping playback
                    sleep(2)
                    self.file_path = get_most_recent_file_in_dir(self.record_dir, self.file_ext)
                    # Initialize for playback
                    self.start_time = now_local()

                    # Playback the recording, with visual countdown
                    self.play_process = play_wav(self.file_path)
                    # self.enclosure.eyes_color(64, 255, 64)  # set color greenish
                    # self.last_index = 24
                    self.schedule_repeating_event(self.playback_feedback, None, 1, name='PlaybackFeedback')
                else:
                    if not get_user_prefs(message)['response_mode'].get('limit_dialog'):
                        self.speak_dialog('audio.record.no.recording', private=True)
                    else:
                        self.speak("No recording found", private=True)

    def playback_feedback(self):
        if not self.play_process or self.play_process.poll() is not None:
            self.end_playback()
            return

    def end_playback(self):
        self.cancel_scheduled_event('PlaybackFeedback')
        if self.play_process:
            self.stop_process(self.play_process)
            self.play_process = None
        if self.record_process:
            self.stop_process(self.record_process)

    ######################################################################
    # Stop
    # def handle_stop(self):
    #     self.speak('Audio recording stopped.')
    #     self.stop()

    # Helper Functions
    def get_recording(self, to_find):
        files = []
        file_ext = None
        LOG.info(to_find)
        for file in os.listdir(self.record_dir):
            LOG.info(file)
            if to_find in file:
                files.append(os.path.splitext(file)[0])
                file_ext = os.path.splitext(file)[1]
        LOG.info(files)
        if len(files) > 1:
            if to_find in files:
                if to_find + "_2" in files:
                    # TODO: Generalize this to grab the newest (highest incremented) file DM
                    file_path = os.path.join(self.record_dir, f"{to_find}_2.{file_ext}")
                else:
                    file_path = os.path.join(self.record_dir, f"{to_find}.{file_ext}")
            else:
                file_path = os.path.join(self.record_dir, f"{files[0]}.{file_ext}")
        else:
            file_path = os.path.join(self.record_dir, f"{files[0]}.{file_ext}")
        LOG.info(file_path)
        return file_path

    @staticmethod
    def get_filename(utterance, user=None):
        # LOG.info(utterance)
        utterance = utterance.split("record", 1)[1]
        if " my " in utterance:
            filename = utterance.split(" my ", 1)[1]
        elif " the " in utterance:
            filename = utterance.split(" the ", 1)[1]
        else:
            filename = utterance

        filename = filename.split(" for ", 1)[0]
        if filename and filename != "audio":
            filename_to_return = filename.strip()
        else:
            # TODO: Ask for filename
            today = datetime.datetime.today()
            filename_to_return = str(today).replace(" ", "_")
        LOG.info(filename_to_return)

        filename_to_return = user + '-' + filename_to_return
        LOG.info(filename_to_return)
        return filename_to_return

    def confirm_filename(self, filename, message):
        try:
            spoken_filename = filename.split("-", 1)[1].rsplit(".", 1)[0]
        except Exception as e:
            LOG.error(e)
            spoken_filename = filename
        # self.speak_dialog("ConfirmFilename", {'file': spoken_filename}, private=True)
        resp = self.ask_yesno("ConfirmFilename", {'file': spoken_filename})
        self.filename = filename  # TODO: Remove from self param for multi-user (see DCC confirmation num, Controls?)
        if resp == "yes":
            # User said yes
            create_daemon(self.start_recording, kwargs={"message": message})
        elif resp == "no":
            self.speak("Please type in a filename.", private=True)
            if tk:
                try:
                    parent = tk.Tk()
                    parent.withdraw()
                    self.filename = \
                        dialog_box.askstring("Audio Recording",
                                             "Please name your audio recording:")
                    parent.quit()
                    LOG.info(self.filename)
                except Exception as e:
                    LOG.info(e)
            if self.filename:
                create_daemon(self.start_recording,
                              kwargs={"message": message})
            else:
                self.speak("I did not get a filename. Please, try again.",
                           private=True)
        else:
            self.speak_dialog("not_doing_anything")


def create_skill():
    return AudioRecordSkill()
