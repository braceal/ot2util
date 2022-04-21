import cv2.aruco
import cv2
import numpy as np
import matplotlib.pyplot as plt
import colorsys
import pathlib

class Camera():

    def initialize_camera(self, camera_id = 2):
        self.cap = cv2.VideoCapture(camera_id)
        self.cap.set(3, 1920)
        self.cap.set(4, 1280)
        self.cap.set(5, 30)  #Set frame rate to 30 fps
        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter.fourcc('M', 'J', 'P', 'G'))
        self.cap.set(cv2.CAP_PROP_BRIGHTNESS, 40) #Set brightness -64 - 64  0.0
        self.cap.set(cv2.CAP_PROP_CONTRAST, 50)   #Set contrast -64 - 64  2.0
        self.cap.set(cv2.CAP_PROP_EXPOSURE, 156)  #Set exposure 1.0 - 5000  156.0
    
    def bgr8_to_jpeg(self, value, quality=75):
        return bytes(cv2.imencode('.jpg', value)[1])

    def get_color(self, img, center_br, center_origin, diameter_x, diameter_y, coordinate):
        H = []
        S = []
        V = []
        img = cv2.resize(img, (640, 480),)
        # transform the colorspace to HSV
        HSV = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        i = coordinate[1]
        j = coordinate[0]
        current = center_origin + i * diameter_y + j * diameter_x
        current = current.astype(int)
        from_bottom = center_br - (11 - i) * diameter_y - (7-j) * diameter_x
        from_bottom = from_bottom.astype(int)
        if i > 6:
            cur_y = from_bottom[1]
        else:
            cur_y = current[1]
        if j > 4:
            cur_x = from_bottom[0]
        else:
            cur_x = current[0]
        cur = np.array([cur_x, cur_y])
        dis = diameter_x[0] // 3
        l = np.array([dis, dis])
        start = (cur - l).astype(int)
        end = (cur + l).astype(int)
        cv2.circle(img, cur, int(dis), (0, 255, 0), 1)
        # Put HSV values in a list
        for i in range(int(start[0]), int(end[0])):
            for j in range(int(start[1]), int(end[1])):
                H.append(HSV[j, i][0])
                S.append(HSV[j, i][1])
                V.append(HSV[j, i][2])
        
        H_avg = np.median(H)
        S_avg = np.median(S)
        V_avg = np.median(V)
        test_color = colorsys.hsv_to_rgb(H_avg/179, S_avg/255, V_avg/255)
        color = [test_color[2] * 255, test_color[1] * 255, test_color[0] * 255]
    #     print("HSV: ", (H_avg, S_avg, V_avg))
    #     print(test_color)
        return img, color, (H_avg, S_avg, V_avg)

    def find_draw_fiducial(self, img):
        # Made by hand. Should be calculated by calibration for better results
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img
        # Find markers
        aruco_dict = cv2.aruco.Dictionary_get(cv2.aruco.DICT_4X4_250)
        parameters = cv2.aruco.DetectorParameters_create()
        corners, ids, rejectedImgPoints = cv2.aruco.detectMarkers(gray, aruco_dict, parameters=parameters)
        img_markers = img.copy()
        
        if len(corners) == 4: # For now we use 4 markers to find the locations for plate 1
            c2 = corners[2][0]
            c1 = corners[0][0]
            c_side = corners[3][0]
            c1 = c1.astype(int)
            c2 = c2.astype(int)
            c_side = c_side.astype(int)
            
            diameter_x = (c_side[1] - c_side[2])/8
            radius_x = diameter_x / 2
            diameter_y = (c1[1] - c2[0]) / 12
            radius_y = diameter_y / 2
            
            origin = (c_side[2][0], c2[0][1]) + np.array([-1, -1])
            cv2.circle(img_markers, origin, 1, (0,255,0), 1)
            cv2.line(img_markers, c2[0], c1[1], 100, 2)
            
            origin_br = (c_side[1][0], c1[1][1]) + np.array([4, -2])
            cv2.circle(img_markers, origin_br, 1, (0,255,0), 1)
            
    #         print("diameter x y: ", diameter_x, diameter_y)
    #         print("well radius x y:", radius_x, radius_y)
            
            center_origin = origin + (radius_x + radius_y) * 0.9
            center_origin = center_origin.astype(int)
            
            center_br = origin_br - (radius_x + radius_y) * 0.9
            
            for i in range(0, 12):
                for j in range(0, 8):
                    current = center_origin + i * diameter_y + j * diameter_x
                    current = current.astype(int)
                    from_bottom = center_br - (11 - i) * diameter_y - (7-j) * diameter_x
                    from_bottom = from_bottom.astype(int)
                    if i > 6:
                        cur_y = from_bottom[1]
                    else:
                        cur_y = current[1]
                    if j > 4:
                        cur_x = from_bottom[0]
                    else:
                        cur_x = current[0]
                    cur = (cur_x, cur_y)
                    cv2.circle(img_markers, cur, 1, (0,255,0), 1)
            
            cv2.line(img_markers, c_side[1], c_side[2], 100, 2)
            for index, cornerset in enumerate(corners):
                cornerset = cornerset[0].astype(int)
                # draw the markers
                tl = cornerset[0]
                tr = cornerset[1]
                bl = cornerset[3]
                br = cornerset[2]
                
                cv2.line(img_markers, tl, tr, 255, 1)
                cv2.line(img_markers, tr, br, 255, 1)
                cv2.line(img_markers, br, bl, 255, 1)
                cv2.line(img_markers, bl, tl, 255, 1)
        else:
            raise Exception("No markers found")

        return img_markers, center_br, center_origin, diameter_x, diameter_y



    def color_recognize(self, workdir, coordinate = np.array([5, 5]), experiment_id = 0):
        ret, frame = self.cap.read()
        frame1, center_br, center_origin, diameter_x, diameter_y = self.find_draw_fiducial(frame)
        frame2, test_color, hsv_avg = self.get_color(frame, center_br, center_origin, diameter_x, diameter_y, coordinate)
        RGB_color = (int(test_color[2]), int(test_color[1]), int(test_color[0]))
        text = f"RGB: {(int(test_color[2]), int(test_color[1]), int(test_color[0]))}"
        frame2 = cv2.putText(frame2, text, (210, 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 255), 2)
        frame2 = cv2.rectangle(frame2, (100, 50), (200, 150), test_color, 10)
        cv2.imwrite(str(workdir / f"exp{experiment_id}_color_recognize_frame1.png"), frame1)
        cv2.imwrite(str(workdir / f"exp{experiment_id}_color_recognize_frame2.png"), frame2)
        return RGB_color, hsv_avg

    def convert_coordinate(self, coordinate_org = 'A1'):
        x = 'H' - coordinate_org[0]
        y = int(coordinate_org[1:]) - 1
        return np.array([x, y])
