import logging
import os
import sys
import time

from mixer.broadcaster.common import MessageType, DEFAULT_PORT
from tests.grabber import Grabber
from tests.grabber import CommandStream
from tests.mixer_testcase import MixerTestCase


logging.basicConfig(stream=sys.stderr, level=logging.WARNING)
logger = logging.getLogger(__name__)


class VRtistTestCase(MixerTestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def assert_stream_equals(self, a_stream: CommandStream, b_stream: CommandStream, msg: str = None):
        a, b = a_stream.data, b_stream.data
        self.assertEqual(a.keys(), b.keys())

        # TODO clarify why we need to ignore TRANSFORM (float comparison)
        ignore = [
            MessageType.TRANSFORM,
            MessageType.BLENDER_DATA_REMOVE,
            MessageType.BLENDER_DATA_RENAME,
            MessageType.BLENDER_DATA_UPDATE,
        ]
        for k in a.keys():
            message_type = str(MessageType(k))
            message_count = len(a[k])
            if message_count != 0:
                logger.info(f"Message count for {message_type:16} : {message_count}")
            if k not in ignore:
                expected_count = self.expected_counts.get(k)
                if expected_count is not None:
                    self.assertEqual(
                        expected_count,
                        message_count,
                        f"Unexpected message count for message {message_type}. Expected {expected_count}: found {message_count}",
                    )
                self.assertEqual(a[k], b[k], f"content mismatch for {message_type}")

    def assert_matches(self):
        # TODO add message cout dict as param

        self._sender.disconnect_mixer()
        # time.sleep(1)
        self._receiver.disconnect_mixer()
        # time.sleep(1)

        host = "127.0.0.1"
        port = int(os.environ.get("VRTIST_PORT", DEFAULT_PORT))
        self._sender.connect_and_join_mixer("mixer_grab_sender", keep_room_open=True)
        time.sleep(1)
        self._sender.disconnect_mixer()
        sender_grabber = Grabber()
        sender_grabber.grab(host, port, "mixer_grab_sender")
        # HACK messages are not delivered in the same order on the receiver and the sender
        # so sort each substream
        sender_grabber.sort()

        self._receiver.connect_and_join_mixer("mixer_grab_receiver", keep_room_open=True)
        time.sleep(1)
        self._receiver.disconnect_mixer()
        receiver_grabber = Grabber()
        receiver_grabber.grab(host, port, "mixer_grab_receiver")
        receiver_grabber.sort()

        # TODO_ timing error : sometimes succeeds
        # TODO_ enhance comparison : check # elements, understandable comparison
        s = sender_grabber.streams
        r = receiver_grabber.streams
        self.assert_stream_equals(s, r)

    def end_test(self):
        self.assert_matches()
