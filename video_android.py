# language: Python 3.13+, file: video_android.py
# Abre el video con el reproductor nativo de Android (VideoView)

from kivy.utils import platform

_android_video = None


def play_video_android(path, on_finish=None):
    """Devuelve True si pudo abrir el video con el reproductor nativo."""
    if platform != 'android':
        return False

    try:
        from jnius import autoclass, PythonJavaClass, java_method
        from android.runnable import run_on_ui_thread

        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        VideoView = autoclass('android.widget.VideoView')
        MediaController = autoclass('android.widget.MediaController')
        Uri = autoclass('android.net.Uri')
        LayoutParams = autoclass('android.view.ViewGroup$LayoutParams')
        ViewGroup = autoclass('android.view.ViewGroup$LayoutParams')

        activity = PythonActivity.mActivity

        class CompletionListener(PythonJavaClass):
            __javainterfaces__ = ['android/media/MediaPlayer$OnCompletionListener']
            __javacontext__ = 'app'

            def __init__(self, callback):
                super().__init__()
                self.callback = callback

            @java_method('(Landroid/media/MediaPlayer;)V')
            def onCompletion(self, mp):
                if self.callback:
                    self.callback()

        @run_on_ui_thread
        def show_video():
            global _android_video
            video = VideoView(activity)
            controller = MediaController(activity)
            controller.setAnchorView(video)
            video.setMediaController(controller)

            uri = Uri.parse(path)
            video.setVideoURI(uri)

            params = LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.MATCH_PARENT
            )
            activity.addContentView(video, params)

            listener = CompletionListener(on_finish)
            video.setOnCompletionListener(listener)

            video.start()
            _android_video = video

        show_video()
        return True

    except Exception as e:
        print("[play_video_android] error:", e)
        return False


def stop_video_android():
    """Detiene y quita el video nativo si está en pantalla."""
    global _android_video
    if _android_video is None:
        return
    try:
        from android.runnable import run_on_ui_thread

        @run_on_ui_thread
        def _stop():
            global _android_video
            try:
                _android_video.stopPlayback()
                parent = _android_video.getParent()
                if parent:
                    parent.removeView(_android_video)
            except Exception:
                pass
            _android_video = None

        _stop()
    except Exception as e:
        print("[stop_video_android] error:", e)
        _android_video = None