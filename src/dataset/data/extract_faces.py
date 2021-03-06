
import os
import argparse
import pickle
import cv2
import numpy as np
import face_recognition
from PIL import Image, ImageDraw

from utility import files_iter


# Get absolute path and force relative-to-file paths
FILE_DIR = os.path.dirname(os.path.realpath(__file__))

### NOTE: we assume that all visible files in source dir are images ###
SOURCE_DIR = os.path.join(FILE_DIR, "processing", "splits")
DEST_DIR = os.path.join(FILE_DIR, "processing", "faces")


#################### FACES ####################


def centroid(points):
    xs, ys = zip(*points)
    xc = sum(xs) / len(xs)
    yc = sum(ys) / len(ys)
    return round(xc), round(yc)


def align_eyes_horizontally(face_img):
    landmarks = face_recognition.face_landmarks(np.array(face_img))
    if len(landmarks) == 0: raise Exception(" Couldn't extract any faces.")

    left_eye = centroid(landmarks[0]["left_eye"])
    right_eye = centroid(landmarks[0]["right_eye"])
    h = right_eye[1] - left_eye[1]
    w = right_eye[0] - left_eye[0]
    angle = np.arcsin(h / np.sqrt(h*h + w*w)) * 180.0 / np.pi

    return face_img.rotate(angle)


def zoom_on_face(face_img, scale=1.2):
    landmarks = face_recognition.face_landmarks(np.array(face_img))
    if len(landmarks) == 0: raise Exception(" Couldn't extract any faces.")

    landmarks_list = [x for xs in landmarks[0].values() for x in xs]
    x, y, w, h = cv2.boundingRect(np.array(landmarks_list))
    y -= (scale - 1) * 0.7 * h
    x -= (scale - 1) * 0.5 * w
    h *= scale
    w *= scale

    return face_img.crop((x, y, x+w, y+h))


def extract_face(file_name, source_dir, dest_dir):
    """
    Extract the first detected face from the image in `file_name` and save it.

    Args:
        file_name: The name of the file (image).
        source_dir: Directory of source images.
        dest_dir: Directory where processed images will be saved.

    Returns:
        The name of the face image.
    """
    print("Extracting face from {}... ".format(file_name), end="")
    face_image_name = file_name

    # Check if destination image already exists (i.e. processed previously)
    face_image_path = os.path.join(dest_dir, face_image_name)
    if not os.path.exists(face_image_path):
        # load image and extract faces from it
        source_path = os.path.join(source_dir, file_name)
        #image = face_recognition.load_image_file(source_path)
        face_img = Image.open(source_path).convert("RGB")

        face_img = align_eyes_horizontally(face_img)
        face_img = zoom_on_face(face_img)

        # Crop image and save as PIL
        face_img.save(face_image_path)

    print("Done.")
    return face_image_name


def extract_faces(source_dir, faces_dir, with_landmarks=True, ensure_pairs=True):
    """
    Try to extract faces from the images in source_dir and save them to faces_dir.

    Args:
        source_dir: Directory of source images.
        faces_dir: Directory where face images will be saved.
        with_landmarks: Extract faces landmarks as well
        ensure_pairs: Ensure only paired images by removing unpaired ones.
    """

    landmarks_dir = os.path.join(faces_dir, "landmarks")

    # Create destination directory if it doesn't exist
    if not os.path.isdir(faces_dir): os.mkdir(faces_dir)
    if with_landmarks and not os.path.isdir(landmarks_dir): os.mkdir(landmarks_dir)

    for file_name in files_iter(source_dir):
        # Try to extract face from file (image)
        try:
            face_image_name = extract_face(file_name, source_dir, faces_dir)
            
            # Extract landmarks if needed
            if with_landmarks:
                extract_landmarks(face_image_name, faces_dir, landmarks_dir)

        except Exception as e:
            print("Failed."); print(f"  {str(e)}")

    # Delete useless files
    if ensure_pairs: clean_incomplete_face_pairs(faces_dir)
    if with_landmarks: clean_landmarks(faces_dir, landmarks_dir)


def clean_incomplete_face_pairs(faces_dir):
    """
    Clean incomplete face pairs (either before or after image is missing)

    Args:
        source_dir: Directory of the examples.
    """

    for file_name in files_iter(faces_dir):

        image_name, ext = file_name.split(".")
        index, which = image_name.split("-")

        other_which = "after" if which == "before" else "before"
        other_file = "{}-{}.{}".format(index, other_which, ext)

        if not os.path.exists(os.path.join(faces_dir, other_file)):
            # Remove this file if the other does not exist
            os.remove(os.path.join(faces_dir, file_name))
            print("Removed face: {}".format(file_name))


#################### END FACES ####################


#################### LANDMARKS ####################

def extract_landmarks(file_name, source_dir, dest_dir):
    """
    Extract the first detected face from the image in `file_name` and save it.

    Args:
        file_name: The path to the face image
        source_dir: Directory of images.
        dest_dir: Directory where processed images will be saved.

    Returns:
        The name of the landmarks file.
    """

    landmarks_name = file_name.split(".")[0] + ".png"

    # Check if landmarks already exists
    landmarks_path = os.path.join(dest_dir, landmarks_name)
    if not os.path.exists(landmarks_path):

        # load image and extract landmarks from it
        face_image = Image.open(os.path.join(source_dir, file_name))
        face_landmarks = face_recognition.face_landmarks(np.array(face_image))

        print("Extracted {} face landmarks... ".format(len(face_landmarks)), end="")
        if len(face_landmarks) == 0:
            raise Exception(" Couldn't extract any landmarks.")

        # Draw landmarks on an empty PIL image
        landmarks_image = Image.new("RGB", face_image.size)
        draw_landmarks(landmarks_image, face_landmarks[0])

        # Save landmarks
        landmarks_image.save(os.path.join(dest_dir, landmarks_name))

        # Pickle landmarks
        landmarks_path = os.path.join(dest_dir, os.path.splitext(landmarks_name)[0] + ".pickle")
        with open(landmarks_path, "wb") as f:
            pickle.dump(face_landmarks[0], f)

    return landmarks_name


def draw_landmarks(landmarks_image, landmarks, fill=None, width=3):
    """
    Draws the landmarks on an empty image.

    Args:
        landmarks_image: PIL image on which we will draw the landmarks.
        landmarks: A dict of the landmarks coordinates, as in {"part": [coords, ...]}.
        fill: Color of the lines.
        width: Width of the lines.
    """

    d = ImageDraw.Draw(landmarks_image)

    for part, xy in landmarks.items():
        d.line(xy, fill=fill, width=3)

        # For the eyes, close the loop (sounds a little poetic, i know)
        if part == "right_eye" or part == "left_eye":
            closing_line = [xy[-1], xy[0]]
            d.line(closing_line, fill=fill, width=3)


def clean_landmarks(faces_dir, landmarks_dir):
    """
    Clean landmarks not associated to any images in faces_dir.

    Args:
        faces_dir: Directory of the faces.
        landmarks_dir: Directory of the landmarks.
    """

    faces_set = set(f.split(".")[0] for f in files_iter(faces_dir))
    for landmarks in files_iter(landmarks_dir):
        landmarks_name = landmarks.split(".")[0]
        if landmarks_name not in faces_set:
            os.remove(os.path.join(landmarks_dir, landmarks))
            print("Removed landmarks {}".format(landmarks))


#################### END LANDMARKS ####################


def main(args):
    if args.image:
        extract_face(args.image, args.source_dir, args.dest_dir)
    else:
        extract_faces(args.source_dir, args.dest_dir, args.with_landmarks, args.ensure_pairs)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="extract faces and save them.")
    
    parser.add_argument('--source_dir', type=str, default=SOURCE_DIR,
        help="source directory of images from which faces will be extracted.")
    parser.add_argument('--dest_dir', type=str, default=DEST_DIR,
        help="destination directory where face images will be saved.")
    parser.add_argument('-i', '--image', type=str, default="",
        help="path to the image, relative to --source_dir (if specified, only this image will be processed).")
    parser.add_argument("--with_landmarks", action="store_true",
        help="extract faces landmarks as well")
    parser.add_argument("--ensure_pairs", action="store_true",
        help="ensure only paired images (remove images with no corresponding paired image)")
    
    args = parser.parse_args()

    main(args)

