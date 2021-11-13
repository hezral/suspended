# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2021 Adi Hezral <hezral@gmail.com>

import threading
import traceback
import logging

from gi.repository import GLib


class ThreadObject:

    stop_thread = False

    @staticmethod
    def _run(command, args=(), callback=None, errorback=None):
        def call(data):
            command, args, callback, errorback = data
            try:
                result = command(*args)
                if callback:
                    GLib.idle_add(callback, result)
            except Exception as e:
                e.traceback = traceback.format_exc()
                if errorback:
                    GLib.idle_add(errorback, e)

        if errorback is None:
            errorback = ThreadObject ._default_errorback
            
        data = command, args, callback, errorback
        thread = threading.Thread(target=run, args=(data,))
        thread.daemon = True
        thread.start()

    @staticmethod
    def _stop():
        ...

    @staticmethod
    def _default_errorback(error):
        logging.error("Unhandled exception in worker thread:\n%s", error.traceback)