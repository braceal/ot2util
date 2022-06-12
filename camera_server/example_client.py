import cv2
import numpy as np
import requests

if __name__ == "__main__":
    url = "http://127.0.0.1:8000"  # default server ip:port

    # enpoints to test
    status_extension = "/status"
    image_extension = "/get_image"

    # 1. Demonstration of what getting the status of camera 0 would look like
    resp = requests.get(url + status_extension)
    print("Example 1: ")
    print(f'Status response with code: {resp.status_code} and message: {resp.content.decode("utf-8")}')

    # 2. Demonstration of receiving picture from server
    resp = requests.get(url + image_extension)

    if resp.status_code == 200:
        # This is how we would convert the bytes from the respnse into an image cv2 can work with
        img = np.asarray(bytearray(resp.content), dtype="uint8")
        img = cv2.imdecode(img, cv2.IMREAD_COLOR)

        cv2.imshow("Press 'q' to quit", img)
        if cv2.waitKey(0) & 0xFF == ord("q"):  # press q to exit
            cv2.destroyAllWindows()

    else:
        print("\n\nExample 2, error: ")
        print(resp.content.decode("utf-8"))

    # 3. Demonstration of error taking picture from server
    resp = requests.get(url + image_extension + "/1")

    if resp.status_code == 200:
        # This is how we would convert the bytes from the respnse into an image cv2 can work with
        img = np.asarray(bytearray(resp.content), dtype="uint8")
        img = cv2.imdecode(img, cv2.IMREAD_COLOR)

        cv2.imshow("image", img)
        if cv2.waitKey(0) & 0xFF == ord("q"):  # press q to exit
            cv2.destroyAllWindows()

    else:
        print("\n\nExample 3: ")
        print(resp.content.decode("utf-8"))
