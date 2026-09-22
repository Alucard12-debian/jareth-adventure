# language: Python, file: video_android.py
# reproductor nativo de Android via pyjnius

from kivy.utils import platform


def play_video_android(video_path, on_finish=None):
    if platform != 'android':
        return False

    try:
        from jnius import autoclass

        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        Intent = autoclass('android.content.Intent')
        Uri = autoclass('android.net.Uri')
        File = autoclass('java.io.File')

        activity = PythonActivity.mActivity
        video_uri = Uri.fromFile(File(video_path))

        intent = Intent(Intent.ACTION_VIEW)
        intent.setDataAndType(video_uri, "video/mp4")

        activity.startActivity(intent)

        if on_finish:
            on_finish()
        return True
    except Exception as e:
        print(f"[video_android] fallo: {e}")
        return False
