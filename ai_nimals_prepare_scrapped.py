# import the necessary packages
import numpy as np
import cv2
from os import listdir
from os.path import isfile, join
import os
import shutil

prototxt = "MobileNetSSD_deploy.prototxt.txt"
model = "MobileNetSSD_deploy.caffemodel"
confidence_threshold = 0.5

# initialize the list of class labels MobileNet SSD was trained to detect
CLASSES = ["background", "aeroplane", "bicycle", "bird", "boat",
           "bottle", "bus", "car", "cat", "chair", "cow", "diningtable",
           "dog", "horse", "motorbike", "person", "pottedplant", "sheep",
           "sofa", "train", "tvmonitor"]

# load our serialized model from disk
print("[INFO] loading model...")
detectionNet = cv2.dnn.readNetFromCaffe(prototxt, model)

os.environ["PATH"] += os.pathsep + os.getcwd()
datasetPath = os.getcwd() + "/Downloads"

def padCroppedImage(crop_img):
    # Let's do some padding! That helps achieving square images for training CNNs
    height, width, channels = crop_img.shape

    # Pad left and right side of image with zeros. Or...
    if height > width:
        fillpix = int((height - width) / 2)
        crop_img = cv2.copyMakeBorder(crop_img, 0, 0, fillpix, fillpix, cv2.BORDER_CONSTANT, 0)

    # ... pad top and bottom side of image with zeros.
    if height < width:
        fillpix = int((width - height) / 2)
        crop_img = cv2.copyMakeBorder(crop_img, fillpix, fillpix, 0, 0, cv2.BORDER_CONSTANT, 0)
    return crop_img

def findBirdInFrame(frame):
    # grab the frame dimensions and convert it to a blob
    (h, w) = frame.shape[:2]
    blob = cv2.dnn.blobFromImage(cv2.resize(frame, (600, 600)), 0.007843, (300, 300), 127.5)

    # pass the blob through the network and obtain the detections and
    # predictions
    detectionNet.setInput(blob)
    detections = detectionNet.forward()

    # loop over the detections done by MobieNet SSD.
    for i in np.arange(0, detections.shape[2]):
        # extract the confidence (i.e., probability) associated with
        # the prediction
        confidence = detections[0, 0, i, 2]

        # filter out weak detections by ensuring the `confidence` is
        # greater than the minimum confidence
        if confidence > confidence_threshold:
            # extract the index of the class label from the
            # `detections`, then compute the (x, y)-coordinates of
            # the bounding box for the object
            idx = int(detections[0, 0, i, 1])
            box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
            (startX, startY, endX, endY) = box.astype("int")
            crop_img = frame[startY:startY + (endY - startY), startX:startX + (endX - startX)]
            break
        else:
            return None
    return crop_img

def main():
    for (i, imagePath) in enumerate(os.listdir(datasetPath)):

        # Delete all previous detections
        if os.path.exists(join(datasetPath, imagePath, "detected")):
            shutil.rmtree(join(datasetPath, imagePath, "detected"))

        print(imagePath)
        os.makedirs(join(datasetPath, imagePath, "detected"))
        onlyfileslist = [f for f in listdir(join(datasetPath, imagePath)) if isfile(join(datasetPath, imagePath, f))]

        images = np.empty(len(onlyfileslist), dtype=object)

        # Now let's loop over all files in range of one class.
        for n in range(0, len(onlyfileslist)):
            # print(join(datasetPath, imagePath, onlyfileslist[n]))
            imgPath = join(datasetPath, imagePath, onlyfileslist[n])
            frame = cv2.imread(imgPath, cv2.IMREAD_COLOR)
            if frame is None:
                print("Can not read image")
            else:
                # Find one(!) bird on loaded image and crop it.
                croppedImg = findBirdInFrame(frame)

                # Check if bird was found :)
                if croppedImg is not None:
                    # Pad cropped images with 0 to have square images for future processing
                    paddedCropImg = padCroppedImage(croppedImg)

                    # Make vertical flip of cropped image. I am working on verification feature so I will need this anyway
                    paddedCropImg = cv2.flip(paddedCropImg, 1)

                    # Save image
                    cv2.imwrite(join(datasetPath, imagePath, "detected", str(n) + '.png'), paddedCropImg)
            os.remove(imgPath)

    # do a bit of cleanup
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
