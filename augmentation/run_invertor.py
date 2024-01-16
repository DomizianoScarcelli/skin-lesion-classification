import os
from typing import List
import torch
from torchvision.utils import save_image
from tqdm import tqdm

from dataloaders.StyleGANDataLoader import StyleGANDataLoader
from .Invertor import Invertor
from dataloaders.ImagesAndSegmentationDataLoader import ImagesAndSegmentationDataLoader
from .gan_config import cfg
from shared.constants import DEFAULT_STATISTICS, IMAGENET_STATISTICS


def embed_everything():
    """
    This function is used to embed all images from the train dataset.
    It will save all the files inside the augmentation/invertor_results/latents directory.

    Since Images2Stylegan++ optimized both the latent vector w and the noise, for each image it saves two files:

    - [image_name]_w.pt
    - [image_name]_noise.pt

    If the image is augmented, it will save the files with the suffix "_augmented".
    """
    batch_size = 2
    invertor = Invertor(cfg=cfg)

    dataloader = StyleGANDataLoader(
        dynamic_load=True,
        batch_size=batch_size,
        resize_dim=(
            cfg.dataset.resolution,
            cfg.dataset.resolution
        )
    )
    train_dataloders = dataloader.get_train_dataloder()

    # Skip label 0 since is the majority class
    for dataloader_label in tqdm(range(1, 8)):
        for index, batch in enumerate(tqdm(train_dataloders[dataloader_label])):
            images, labels, image_paths, augmented_list = batch
            clean_paths = [image_path.split(
                "/")[-1].replace(".jpg", "") for image_path in image_paths]
            clean_paths = [clean_path + "_augmented" if augmented else clean_path for clean_path,
                           augmented in zip(clean_paths, augmented_list)]
            latent, noise_list = invertor.embed(
                images=images,
                names=clean_paths,
                save_images=False,
                w_epochs=800,
                n_epochs=500,
                verbose=False,
                show_pbar=True)


def generate_similar_images():
    num_images_to_generate = 20
    batch_size = 16
    invertor = Invertor(cfg=cfg)

    fixed_dataloader = ImagesAndSegmentationDataLoader(
        limit=None,
        dynamic_load=True,
        upscale_train=False,
        normalize=False,
        normalization_statistics=DEFAULT_STATISTICS,
        batch_size=batch_size,
        resize_dim=(
            cfg.dataset.resolution,
            cfg.dataset.resolution,
        )
    )
    fixed_data = fixed_dataloader.get_test_dataloader()
    for batch in fixed_data:
        images, _ = batch

        images = images.to(invertor.device)
        image = images[10].unsqueeze(0)
        break
    latent_1, noise_list_1 = invertor.embed(
        image, "image", w_epochs=800, n_epochs=800)
    invertor.update_noise(noise_list_1)
    for i in range(num_images_to_generate):
        variant_latent = latent_1.clone() + torch.randn_like(latent_1) * 0.15
        image = invertor.generate(variant_latent)
        save_image(
            image, f"augmentation/invertor_results/resample_results/resampled_image_{i}.png")


def embed_v1_test():
    batch_size = 8
    invertor = Invertor(cfg=cfg)

    fixed_dataloader = ImagesAndSegmentationDataLoader(
        limit=None,
        dynamic_load=True,
        upscale_train=False,
        normalize=False,
        normalization_statistics=DEFAULT_STATISTICS,
        batch_size=batch_size,
        resize_dim=(
            cfg.dataset.resolution,
            cfg.dataset.resolution,
        )
    )
    fixed_data = fixed_dataloader.get_test_dataloader()
    for batch in fixed_data:
        images, labels = batch

        images = images.to(invertor.device)
        image = images[7].unsqueeze(0)
        break

    latent_1 = invertor.embed(image, "image")
    # min_noise, max_noise = get_min_max_noise(noise_list_1)
    # for i in range(num_images_to_generate):
    #     invertor.reset_noise(min_value=min_noise,
    #                          max_value=max_noise)
    #     image = invertor.generate(latent_1)
    #     save_image(
    #         image, f"augmentation/invertor_results/resample_results/resampled_image_{i}.png")


def embed_and_style_transfer():
    """
    This is a function that is used to see the quality of the embedded image and the quality of the style transfer.
    """
    batch_size = 16
    invertor = Invertor(cfg=cfg)

    fixed_dataloader = ImagesAndSegmentationDataLoader(
        limit=None,
        dynamic_load=True,
        upscale_train=False,
        normalize=False,
        normalization_statistics=DEFAULT_STATISTICS,
        batch_size=batch_size,
        resize_dim=(
            cfg.dataset.resolution,
            cfg.dataset.resolution,
        )
    )
    fixed_data = fixed_dataloader.get_test_dataloader()
    for batch in fixed_data:
        images, labels = batch

        images = images.to(invertor.device)
        first_image = images[1].unsqueeze(0)
        second_image = [image for index, (image, label) in enumerate(zip(
            images, labels)) if index != 1 and label == labels[1]][0].unsqueeze(0)
        break

    latent_1, noise_list_1 = invertor.embed(first_image, "first_image")
    latent_2, noise_list_2 = invertor.embed(second_image, "second_image")

    # NOTE: trying to invert the noise
    invertor.style_transfer(
        latent_1, latent_2, noise_list_2, noise_list_1)

############################
# OFFLINE TEST OPERATIONS  #
############################


def offline_mix_latents():
    invertor = Invertor(cfg=cfg)
    latent_path = invertor.latents_dir
    first_latent_path = os.path.join(latent_path, "first_image_w.pt")
    second_latent_path = os.path.join(latent_path, "second_image_w.pt")
    first_noise_path = os.path.join(latent_path, "first_image_noise.pt")
    second_noise_path = os.path.join(latent_path, "second_image_noise.pt")
    latent_1 = torch.load(first_latent_path)
    latent_2 = torch.load(second_latent_path)
    noise_list_1 = torch.load(first_noise_path)
    noise_list_2 = torch.load(second_noise_path)
    for thresh in [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]:
        invertor.mix_latents(latent_1, latent_2, noise_list_1,
                             noise_list_2, mix_threshold=thresh)


def offline_style_transfer():
    invertor = Invertor(cfg=cfg)
    latent_path = invertor.latents_dir
    first_latent_path = os.path.join(latent_path, "first_image_w.pt")
    second_latent_path = os.path.join(latent_path, "second_image_w.pt")
    first_noise_path = os.path.join(latent_path, "first_image_noise.pt")
    second_noise_path = os.path.join(latent_path, "second_image_noise.pt")
    latent_1 = torch.load(first_latent_path)
    latent_2 = torch.load(second_latent_path)
    noise_list_1 = torch.load(first_noise_path)
    noise_list_2 = torch.load(second_noise_path)
    image_1 = invertor.generate(latent_1, noise_list_1)
    image_2 = invertor.generate(latent_2, noise_list_2)
    save_image(image_1, "image_1.png")
    save_image(image_2, "image_2.png")
    invertor.style_transfer(
        latent_1, latent_2, noise_list_1, noise_list_2, add_random_noise=True)


def get_min_max_noise(noise_list: List[torch.Tensor], scale_factor=1.0):
    min_noise, max_noise = torch.mean(torch.tensor(
        [n.min() for n in noise_list])), torch.mean(torch.tensor([n.max() for n in noise_list]))
    return min_noise * scale_factor, max_noise * scale_factor


def resample_image():
    invertor = Invertor(cfg=cfg)
    latent_path = invertor.latents_dir
    first_latent_path = os.path.join(latent_path, "image_w.pt")
    noise_path = os.path.join(latent_path, "image_noise.pt")
    latent = torch.load(first_latent_path)
    noise = torch.load(noise_path)
    invertor.update_noise(noise)
    num_images_to_generate = 30
    for i in range(num_images_to_generate):
        new_latent = latent.clone() + torch.randn_like(latent) * 0.15
        image = invertor.generate(new_latent)
        save_image(image, f"resampled_image_{i}.png")


if __name__ == '__main__':
    # resample_image()
    # generate_similar_images()
    embed_everything()