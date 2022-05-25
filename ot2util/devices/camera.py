"""Allows for integration of camera into experiments.
"""

import colorsys
from typing import Tuple

import cv2
import cv2.aruco
import numpy as np

ColorRGB = Tuple[int, int, int]
ColorHSV = Tuple[float, float, float]


class Camera:
    """Encapsulates logic of finding coordinates of wells and measuring thier colors.

    In the future this should be expanded to have other self monitoring features.
    """

    @staticmethod
    def _convert_coordinate(well: str = "A1") -> Tuple[int, int]:
        x = ord("H") - ord(well[0])
        y = int(well[1:]) - 1
        return x, y

    def __init__(self, camera_id: int = 2) -> None:
        """Initializes camera object with correct settings for the camera on top of the OT2.

        Parameters
        ----------
        camera_id : int, optional
            ID of the camera on top of the OT2, by default 2
        """
        self.cap = cv2.VideoCapture(camera_id)
        self.cap.set(3, 1920)
        self.cap.set(4, 1280)
        self.cap.set(5, 30)  # Set frame rate to 30 fps
        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter.fourcc("M", "J", "P", "G"))
        self.cap.set(cv2.CAP_PROP_BRIGHTNESS, 40)  # Set brightness -64 - 64  0.0
        self.cap.set(cv2.CAP_PROP_CONTRAST, 50)  # Set contrast -64 - 64  2.0
        self.cap.set(cv2.CAP_PROP_EXPOSURE, 156)  # Set exposure 1.0 - 5000  156.0

    def measure_well_color(self, destination_well: str) -> Tuple[ColorRGB, ColorHSV]:
        """Measures the RGB values of the destination well. Gives RGB and HSV values

        Parameters
        ----------
        destination_well : str
            The coordinate string (e.g :code:`"A1"`) of the well we want to measure

        Returns
        -------
        Tuple[ColorRGB, ColorHSV]
            A tuple of tuples. First one is the RGB values as integers. Second tuple
            is HSV float values.
        """
        # Find target well
        coordinate = self._convert_coordinate(destination_well)

        ret, frame = self.cap.read()
        (
            frame1,
            center_br,
            center_origin,
            diameter_x,
            diameter_y,
        ) = self._find_draw_fiducial(frame)
        frame2, rgb, hsv = self._get_color(
            frame, center_br, center_origin, diameter_x, diameter_y, coordinate
        )
        text = f"RGB: {rgb}"
        frame2 = cv2.putText(
            frame2, text, (210, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 255), 2
        )
        frame2 = cv2.rectangle(frame2, (100, 50), (200, 150), rgb, 10)

        # TODO: Originally the frames were saved,
        # See commit https://github.com/braceal/ot2util/commit/b2346e42a3688917f94d27bd118d9d9dc1d45e8f
        # For details on what was happening. I have removed it for now
        # Can we get rid of the frame logic now? Is it good for logging?

        return rgb, hsv

    def _get_color(
        self, img: cv2.Mat, center_br, center_origin, diameter_x, diameter_y, coordinate
    ) -> Tuple[cv2.Mat, ColorRGB, ColorHSV]:
        h, s, v = [], [], []
        img = cv2.resize(img, (640, 480))
        # transform the colorspace to HSV
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

        # TODO: This block should be a helper function
        x, y = coordinate
        current = center_origin + y * diameter_y + x * diameter_x
        current = current.astype(int)
        from_bottom = center_br - (11 - y) * diameter_y - (7 - x) * diameter_x
        from_bottom = from_bottom.astype(int)
        cur_y = from_bottom[1] if y > 6 else current[1]
        cur_x = from_bottom[0] if x > 4 else current[0]
        cur = np.array([cur_x, cur_y])

        dis = diameter_x[0] // 3
        l_offset = np.array([dis, dis])
        start = (cur - l_offset).astype(int)
        end = (cur + l_offset).astype(int)
        cv2.circle(img, cur, int(dis), (0, 255, 0), 1)
        # Put HSV values in a list
        for i in range(int(start[0]), int(end[0])):
            for j in range(int(start[1]), int(end[1])):
                h.append(hsv[j, i][0])
                s.append(hsv[j, i][1])
                v.append(hsv[j, i][2])

        h, s, v = np.median(h), np.median(s), np.median(v)
        # TODO: Why is h divided by 179 instead of 255?
        hsv = (h / 179, s / 255, v / 255)
        r, g, b = colorsys.hsv_to_rgb(*hsv)
        rgb = (int(g * 255), int(r * 255), int(b * 255))
        return img, rgb, hsv

    def _find_draw_fiducial(self, img: cv2.Mat):
        # Made by hand. Should be calculated by calibration for better results
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img
        # Find markers
        aruco_dict = cv2.aruco.Dictionary_get(cv2.aruco.DICT_4X4_250)
        parameters = cv2.aruco.DetectorParameters_create()
        corners, ids, rejectedImgPoints = cv2.aruco.detectMarkers(
            gray, aruco_dict, parameters=parameters
        )
        img_markers = img.copy()

        # For now we use 4 markers to find the locations for plate 1
        if len(corners) != 4:
            raise ValueError("No markers found")

        c2 = corners[2][0].astype(int)
        c1 = corners[0][0].astype(int)
        c_side = corners[3][0].astype(int)

        diameter_x = (c_side[1] - c_side[2]) / 8
        radius_x = diameter_x / 2
        diameter_y = (c1[1] - c2[0]) / 12
        radius_y = diameter_y / 2

        origin = (c_side[2][0], c2[0][1]) + np.array([-1, -1])
        cv2.circle(img_markers, origin, 1, (0, 255, 0), 1)
        cv2.line(img_markers, c2[0], c1[1], 100, 2)

        origin_br = (c_side[1][0], c1[1][1]) + np.array([4, -2])
        cv2.circle(img_markers, origin_br, 1, (0, 255, 0), 1)

        center_origin = origin + (radius_x + radius_y) * 0.9
        center_origin = center_origin.astype(int)

        center_br = origin_br - (radius_x + radius_y) * 0.9

        for y in range(0, 12):
            for x in range(0, 8):
                current = center_origin + y * diameter_y + x * diameter_x
                current = current.astype(int)
                from_bottom = center_br - (11 - y) * diameter_y - (7 - x) * diameter_x
                from_bottom = from_bottom.astype(int)
                cur_y = from_bottom[1] if y > 6 else current[1]
                cur_x = from_bottom[0] if x > 4 else current[0]
                cur = (cur_x, cur_y)
                cv2.circle(img_markers, cur, 1, (0, 255, 0), 1)

        cv2.line(img_markers, c_side[1], c_side[2], 100, 2)
        for cornerset in corners:
            cornerset = cornerset[0].astype(int)
            # Draw the markers
            tl, tr, bl, br = cornerset[0], cornerset[1], cornerset[3], cornerset[2]
            cv2.line(img_markers, tl, tr, 255, 1)
            cv2.line(img_markers, tr, br, 255, 1)
            cv2.line(img_markers, br, bl, 255, 1)
            cv2.line(img_markers, bl, tl, 255, 1)

        return img_markers, center_br, center_origin, diameter_x, diameter_y
