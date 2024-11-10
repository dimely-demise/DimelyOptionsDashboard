import time
import os
import glob
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class Watcher:
    DIRECTORY_TO_WATCH = "./src/ui"

    def __init__(self):
        self.observer = Observer()

    def compile_ui_files(self):
        ui_files = glob.glob(os.path.join(self.DIRECTORY_TO_WATCH, "*.ui"))
        for ui_file in ui_files:
            output_file = ui_file.replace(".ui", "_ui.py")
            os.system(f"pyuic5 {ui_file} -o {output_file}")
            print(f"Recompiled {ui_file} to {output_file}")

    def run(self):
        # Compile files when script starts
        self.compile_ui_files()

        event_handler = Handler(self.compile_ui_files)
        self.observer.schedule(event_handler, self.DIRECTORY_TO_WATCH, recursive=True)
        self.observer.start()
        try:
            while True:
                time.sleep(1)
        except:
            self.observer.stop()
        self.observer.join()

class Handler(FileSystemEventHandler):
    def __init__(self, compile_ui_files):
        self.compile_ui_files = compile_ui_files

    def on_modified(self, event):
        print("Mpdified", event.src_path)
        if not event.src_path.endswith(".py"):
            self.compile_ui_files()

if __name__ == '__main__':
    watcher = Watcher()
    watcher.run()
