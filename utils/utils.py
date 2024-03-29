from typing import Tuple
import numpy as np
import torch
import cv2
from PIL import Image
from tqdm import tqdm
import os
import pandas as pd
from torchvision import transforms
import json
import random
from config import IMAGE_SIZE, USE_DML, PATH_TO_SAVE_RESULTS, USE_MPS

if USE_DML:
    import torch_directml


# def center_crop(image: torch.Tensor, size: Tuple[int, int]) -> np.ndarray:
#     if size[0] > image.shape[0] or size[1] > image.shape[1]:
#         image = cv2.resize(image.numpy(), (size[0] * 3, size[1] * 3))
#         image = torch.from_numpy(image)
#     assert image.ndim == 3, f"Input must be a 3D array. Input shape is {image.shape}"
#     assert image.shape[2] == 3, "Input must have 3 channels (RGB image)"
#     assert size[0] <= image.shape[0] and size[1] <= image.shape[
#         1], f"Crop size must be smaller than input size. Current input size is {image.shape} and crop size is {size}"

#     h, w = image.shape[0], image.shape[1]
#     top = (h - size[0]) // 2
#     left = (w - size[1]) // 2
#     bottom = top + size[0]
#     right = left + size[1]

#     cropped_image = image[top:bottom, left:right, :]

#     return cropped_image.numpy()


# def crop_roi(images: torch.Tensor, size: Tuple[int, int]) -> torch.Tensor:
#     if images.dim() == 3:
#         images = images.unsqueeze(0)
#     assert images.dim(
#     ) == 4, f"Input must be a 4D tensor. Input shape is {images.shape}"
#     # assert images.shape[1:] == (
#     # 3, size[0], size[1]), "Input must be a 4D tensor of shape (N, 3, H, W)"
#     batch_images = np.array([(image_tensor.permute(
#         1, 2, 0) * 255).numpy().astype(np.uint8) for image_tensor in images])

#     cropped_images = []
#     for image_array in batch_images:
#         # Convert image to grayscale
#         image_gray = cv2.cvtColor(
#             image_array, cv2.COLOR_BGR2GRAY)

#         # plot_image_grid(torch.from_numpy(image_gray))

#         ret, thresh = cv2.threshold(image_gray, 0, 1, cv2.THRESH_BINARY)

#         # plot_image_grid(torch.from_numpy(thresh.astype(np.uint8)))

#         # Find contours in the edge image
#         contours, _ = cv2.findContours(
#             thresh.astype(np.uint8), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

#         # If there are no contours, save the image as it is
#         if len(contours) == 0:
#             cropped_images.append(torch.from_numpy(
#                 image_array).permute(2, 0, 1))
#             continue

#         # Find the contour with the maximum area (assuming it corresponds to the item)
#         max_contour = max(contours, key=cv2.contourArea)

#         # Get the bounding box of the contour
#         x, y, w, h = cv2.boundingRect(max_contour)

#         # Crop the image using the bounding box
#         cropped_image = image_array[y:y + h, x:x + w]
#         # cropped_image = center_crop(
#         #     torch.from_numpy(cropped_image), (150, 150))
#         cropped_image = cv2.resize(cropped_image, size)
#         cropped_image = torch.from_numpy(cropped_image).permute(2, 0, 1)
#         cropped_images.append(cropped_image / 255)

#     cropped_images = torch.stack(cropped_images, dim=0)
#     return cropped_images


def zoom_out(image: torch.Tensor or np.ndarray, size=(700, 700)) -> torch.Tensor:
    # Create a new black image
    if image.shape[-1] != 3:
        # image = image.permute(2, 0, 1)
        image = image.permute(1, 2, 0).cpu().numpy()
    new_image = np.zeros((size[0], size[1], 3))

    # Calculate the position to paste the original image
    y_offset = (size[0] - image.shape[0]) // 2
    x_offset = (size[1] - image.shape[1]) // 2

    # Paste the original image into the new image
    new_image[y_offset:y_offset+image.shape[0],
              x_offset:x_offset+image.shape[1]] = image
    new_image = torch.from_numpy(new_image)
    new_image = new_image.permute(2, 0, 1)
    return new_image


def get_bounding_boxes_from_segmentation(segmentation: torch.Tensor) -> torch.Tensor:
    segmentation_channel = segmentation.squeeze(0)
    # Find the indices of the white pixels
    rows, cols = torch.where(segmentation_channel == 1)
    # Get the minimum and maximum of the rows and columns
    min_row, max_row = rows.min(), rows.max()
    min_col, max_col = cols.min(), cols.max()
    # Define the bounding box
    bbox = torch.tensor([min_row, min_col, max_row, max_col])
    # Reshape the bounding box tensor to the expected shape
    bbox = bbox.unsqueeze(0)
    # print(f"Bounding box are: {bbox}")
    return bbox


def approximate_bounding_box_to_square(box, min_size=None):
    MAX_WIDTH = 1000
    MAX_HEIGHT = 1000
    width = (box[2] - box[0]).item()
    height = (box[3] - box[1]).item()

    center_x = ((box[0] + box[2]) // 2).item()
    center_y = ((box[1] + box[3]) // 2).item()

    # print(f"Computed width is {width} and height is {height}")
    if min_size is None:
        side_length = max(width, height, 0, 0)
    else:
        side_length = max(min_size)

    # Calculate the new coordinates of the square
    new_box = [
        max(center_x - side_length // 2, 0),
        max(center_y - side_length // 2, 0),
        min(center_x + side_length // 2, MAX_WIDTH),
        min(center_y + side_length // 2, MAX_HEIGHT)
    ]

    return new_box


def shift_boxes(boxes, h_shift, w_shift):
    shifted_boxes = []
    for box in boxes:
        shifted_box = torch.tensor(
            box) + torch.tensor([h_shift // 2, w_shift//2, h_shift//2, w_shift//2])
        shifted_boxes.append([i.item() for i in shifted_box])
    return shifted_boxes


def get_resize_interpolation(image, size):
    if len(image.shape) == 2:
        image = image.unsqueeze(0)
    if image.shape[1:] > size:
        interpolation = cv2.INTER_AREA
    else:
        interpolation = cv2.INTER_CUBIC
    return interpolation


def crop_image_from_box(image, box, size):
    # print(f"Box is {box}")
    cropped_image = image[:, box[0]:box[2], box[1]:box[3]]
    # print(f"Cropped image shape is {cropped_image.shape}")
    cropped_image = cropped_image.permute(1, 2, 0).cpu().numpy()

    if size is None:
        return cropped_image
    interpolation = get_resize_interpolation(cropped_image, size)
    resized_image = cv2.resize(
        cropped_image, size, interpolation=interpolation)
    return resized_image


def resize_images(images, new_size=(800, 800)):
    interpolation = get_resize_interpolation(images, new_size)
    return torch.stack([torch.from_numpy(cv2.resize(
        image.permute(1, 2, 0).cpu().numpy(), new_size, interpolation=interpolation)) for image in images]).permute(0, 3, 1, 2)


def resize_segmentations(segmentation, new_size=(800, 800)):
    interpolation = get_resize_interpolation(segmentation, new_size)
    return torch.stack([torch.from_numpy(cv2.resize(
        image.permute(1, 2, 0).cpu().numpy(), new_size, interpolation=interpolation)) for image in segmentation]).unsqueeze(0).permute(1, 0, 2, 3)


def calculate_normalization_statistics(df: pd.DataFrame) -> Tuple[torch.Tensor, torch.Tensor]:
    images_for_normalization = []

    for _, img in tqdm(df.iterrows(), desc=f'Calculating normalization statistics'):
        if not os.path.exists(img['image_path']):
            continue
        image = transforms.ToTensor()(Image.open(img['image_path']))
        images_for_normalization.append(image)

    images_for_normalization = torch.stack(images_for_normalization)
    mean = torch.tensor([torch.mean(images_for_normalization[:, channel, :, :])
                        for channel in range(3)]).reshape(3, 1, 1)
    std = torch.tensor([torch.std(images_for_normalization[:, channel, :, :])
                       for channel in range(3)]).reshape(3, 1, 1)

    return tuple((mean, std))


def select_device():
    if USE_DML:
        device = torch_directml.device()
    elif USE_MPS:
        device = torch.device('mps')
    else:
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print('Using device: %s' % device)
    return device


def save_configurations(data_name, configurations):
    path = PATH_TO_SAVE_RESULTS + f"/{data_name}/"
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)

    results_file_path = path + 'configurations.json'
    with open(results_file_path, 'w') as json_file:
        json.dump(configurations, json_file, indent=2)


def save_results(data_name, results, test=False):
    path = PATH_TO_SAVE_RESULTS + f"/{data_name}/results/"
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)

    results_file_path = path + 'test_results.json' if test else path + 'tr_val_results.json'
    if os.path.exists(results_file_path):
        final_results = None
        with open(results_file_path, 'r') as json_file:
            final_results = json.load(json_file)
        final_results.append(results)
        with open(results_file_path, 'w') as json_file:
            json.dump(final_results, json_file, indent=2)
    else:
        final_results = [results]
        with open(results_file_path, 'w') as json_file:
            json.dump(final_results, json_file, indent=2)


def save_model(data_name, model, epoch=None, is_best=False):
    path = PATH_TO_SAVE_RESULTS + f"/{data_name}/models/"
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)
    if is_best:
        torch.save(model.state_dict(), f'{path}/melanoma_detection_best.pt')
    else:
        torch.save(model.state_dict(),
                   f'{path}/melanoma_detection_{epoch+1}.pt')


def set_seed(seed):
    np.random.seed(seed)
    random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)
    # When running on the CuDNN backend, two further options must be set
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    # Set a fixed value for the hash seed
    os.environ["PYTHONHASHSEED"] = str(seed)
    print(f"Random seed set as {seed}")
