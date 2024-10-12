import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QGridLayout, QVBoxLayout, QTableWidget, QTableWidgetItem
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import QTimer
import cv2
from vehicle_detector import VehicleDetector
import os


class ATLAS:
    def __init__(self, videos=[], win_Titles=[]):
        self.videos = videos
        self.win_Titles = win_Titles
        self.caps = [cv2.VideoCapture(video_path)
                     for video_path in self.videos]
        
        self.signal_timers = [QTimer() for _ in range(len(self.win_Titles))]
        for timer in self.signal_timers:
            timer.setInterval(1000)
            timer.timeout.connect(self.changeSignal)
        
        self.green_signal_index = None

    def VideoStreamGrid(self):
        app = QApplication(sys.argv)
        window = QWidget()
        layout = QVBoxLayout()
        window.setLayout(layout)

        # Create video grid layout
        video_grid = QGridLayout()
        layout.addLayout(video_grid)

        self.labels = []

        for i, (video_path, title) in enumerate(zip(self.videos, self.win_Titles), start=1):
            # Add video label
            label = QLabel()
            video_grid.addWidget(label, (i-1) // 2, (i-1) % 2)
            self.labels.append(label)

        # Create start button
        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.startButton)
        layout.addWidget(self.start_button)

        # Create capture button
        self.capture_button = QPushButton("Capture Frames")
        self.capture_button.clicked.connect(self.capture_frames)
        layout.addWidget(self.capture_button)

        # Create table
        self.table = QTableWidget(4, 2)
        layout.addWidget(self.table)

        # Set table headers
        self.table.setHorizontalHeaderLabels(["Green Signal", "Red Signal"])
        self.table.setVerticalHeaderLabels(self.win_Titles)

        # Populate table with placeholder data
        for i in range(len(self.videos)):
            for j in range(2):
                item = QTableWidgetItem("Data")
                self.table.setItem(i, j, item)

        window.show()

        # Create QTimer to update video frames periodically
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frames)
        self.timer.start(30)  # Update every 30 milliseconds

        sys.exit(app.exec_())

    def update_frames(self):
        # Find the smallest width and height among all videos
        min_width = min([int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                         for cap in self.caps])
        min_height = min([int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                          for cap in self.caps])

        for cap, label in zip(self.caps, self.labels):
            ret, frame = cap.read()

            # If the video ends, restart it
            if not ret:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Restart the video
                ret, frame = cap.read()

            if ret:
                frame = cv2.resize(frame, (min_width//4, min_height//4))
                height, width, channel = frame.shape
                qImg = QImage(frame.data, width, height, QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(qImg)
                label.setPixmap(pixmap)

    def capture_frames(self):
        print("capturing frames")
        for cap, title in zip(self.caps, self.win_Titles):
            ret, frame = cap.read()
            if ret:
                cv2.imwrite(f"Captured_Frames/{title}.jpg", frame)

    def startButton(self):
        print('Starting')
        self.capture_frames()
        self.AllVehiclesCount = []
        vd = VehicleDetector()
        path = "Captured_Frames"
        for i, frame_name in enumerate(os.listdir(path)):
            print(frame_name)
            frame_path = os.path.join(path, frame_name)
            frame = cv2.imread(frame_path)
            vehicle_boxes = vd.detect_vehicles(frame)
            vehicle_count = len(vehicle_boxes)
            self.AllVehiclesCount.append(vehicle_count)
            print(f"{frame_name}: ", vehicle_count)

            if vehicle_count > 0:
                self.table.item(i, 0).setText("Yes")  # Set signal to green
                if i < len(self.signal_timers):
                    self.signal_timers[i].start()  # Start timer for this signal
                    self.green_signal_index = i

    def changeSignal(self):
        # Stop the timer for the current green signal
        if self.green_signal_index is not None:
            self.signal_timers[self.green_signal_index].stop()
            # Set the table item to "No" for the current green signal
            self.table.item(self.green_signal_index, 0).setText("No")

        # Find the next signal to make green
        next_index = (self.green_signal_index + 1) % len(self.win_Titles)
        self.table.item(next_index, 0).setText(
            "Yes")  # Set next signal to green
        self.green_signal_index = next_index

        # Start the timer for the next green signal
        self.signal_timers[next_index].start()

def main():
    # Define video sources
    videos = ["north_video.mp4", "south_video.mp4",
              "east_video.mp4", "west_video.mp4"]

    # Define window titles
    win_Titles = ["NORTH", "SOUTH", "EAST", "WEST"]

    # Create a new ATLAS object
    atlas = ATLAS(videos=videos, win_Titles=win_Titles)

    # Start video streams
    atlas.VideoStreamGrid()


if __name__ == '__main__':
    main()
