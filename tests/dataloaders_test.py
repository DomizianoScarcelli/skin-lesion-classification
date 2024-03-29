from tqdm import tqdm
from config import BATCH_SIZE, DATASET_LIMIT, NORMALIZE
from dataloaders.MSLANetDataLoader import MSLANetDataLoader
from dataloaders.StyleGANDataLoader import StyleGANDataLoader
from shared.constants import IMAGENET_STATISTICS
from dataloaders.SegmentedImagesDataLoader import SegmentedImagesDataLoader
from dataloaders.DynamicSegmentationDataLoader import DynamicSegmentationDataLoader
from dataloaders.ImagesAndSegmentationDataLoader import ImagesAndSegmentationDataLoader
from shared.enums import DynamicSegmentationStrategy
import pytest
import torch


@pytest.mark.skip(reason="Deprecated")
def test_segmeneted_images_dataloader():
    dataloder = SegmentedImagesDataLoader(dynamic_load=True)
    train_dataloder = dataloder.get_train_dataloder()
    val_dataloder, _ = dataloder.get_val_test_dataloader()
    assert len(train_dataloder) > 0
    assert len(val_dataloder) > 0
    train_batch = next(iter(train_dataloder))
    assert len(train_batch) == 2
    val_batch = next(iter(val_dataloder))
    assert len(val_batch) == 2
    tr_images, tr_labels = train_batch
    val_images, val_labels = val_batch
    assert tr_images.shape == val_images.shape
    assert tr_labels.shape == val_labels.shape


def test_images_and_segmentation_dataloader():
    dataloder = ImagesAndSegmentationDataLoader(
        dynamic_load=True,
        normalization_statistics=IMAGENET_STATISTICS)
    train_dataloder = dataloder.get_train_dataloder()
    val_dataloder = dataloder.get_val_dataloader()
    test_dataloader = dataloder.get_test_dataloader()
    assert len(train_dataloder) > 0
    assert len(val_dataloder) > 0
    train_batch = next(iter(train_dataloder))
    assert len(train_batch) == 3
    val_batch = next(iter(val_dataloder))
    assert len(val_batch) == 3
    test_batch = next(iter(test_dataloader))
    assert len(test_batch) == 3
    tr_images, tr_labels, tr_segmentations = train_batch
    val_images, val_labels, val_segmentations = val_batch
    te_images, te_labels, te_segmentations = test_batch
    assert tr_images.shape == val_images.shape == te_images.shape, f"tr_images.shape: {tr_images.shape}, val_images.shape: {val_images.shape}, te_images.shape: {te_images.shape}"
    assert tr_segmentations.shape == val_segmentations.shape == te_segmentations.shape, f"tr_segmentations.shape: {tr_segmentations.shape}, val_segmentations.shape: {val_segmentations.shape}, te_segmentations.shape: {te_segmentations.shape}"
    assert tr_labels.shape == val_labels.shape == te_labels.shape, f"tr_labels.shape: {tr_labels.shape}, val_labels.shape: {val_labels.shape}, te_labels.shape: {te_labels.shape}"


def test_images_and_segmentation_dataloader_augmented():
    dataloder = ImagesAndSegmentationDataLoader(
        dynamic_load=True,
        normalization_statistics=IMAGENET_STATISTICS,
        load_segmentations=False)
    train_dataloder = dataloder.get_train_dataloder()
    val_dataloder = dataloder.get_val_dataloader()
    test_dataloader = dataloder.get_test_dataloader()
    assert len(train_dataloder) > 0
    assert len(val_dataloder) > 0
    train_batch = next(iter(train_dataloder))
    assert len(train_batch) == 2
    val_batch = next(iter(val_dataloder))
    assert len(val_batch) == 2
    test_batch = next(iter(test_dataloader))
    assert len(test_batch) == 2
    tr_images, tr_labels = train_batch
    val_images, val_labels = val_batch
    te_images, te_labels, = test_batch
    print(f"tr_images.shape: {tr_images.shape}")


def test_dynamic_segmentation_dataloader():
    dataloader = DynamicSegmentationDataLoader(
        dynamic_load=True,
        batch_size=8,
        segmentation_strategy=DynamicSegmentationStrategy.SAM.value,
        normalization_statistics=IMAGENET_STATISTICS,
        load_synthetic=True)
    train_dataloder = dataloader.get_train_dataloder()
    val_dataloder = dataloader.get_val_dataloader()
    test_dataloader = dataloader.get_test_dataloader()
    assert len(train_dataloder) > 0
    assert len(val_dataloder) > 0
    train_batch = next(iter(train_dataloder))
    assert len(train_batch) == 2
    val_batch = next(iter(val_dataloder))
    assert len(val_batch) == 2
    test_batch = next(iter(test_dataloader))
    assert len(test_batch) == 2
    tr_images, tr_labels = train_batch
    val_images, val_labels = val_batch
    te_images, te_labels = test_batch
    assert tr_images.shape == val_images.shape == te_images.shape, f"tr_images.shape: {tr_images.shape}, val_images.shape: {val_images.shape}, te_images.shape: {te_images.shape}"
    assert tr_labels.shape == val_labels.shape == te_labels.shape, f"tr_labels.shape: {tr_labels.shape}, val_labels.shape: {val_labels.shape}, te_labels.shape: {te_labels.shape}"


def test_stylegan_dataloader():
    dataloader = StyleGANDataLoader(dynamic_load=True)
    train_dataloders = dataloader.get_train_dataloder()
    for dataloader_label in tqdm(range(8)):
        for batch in train_dataloders[dataloader_label]:
            images, labels, image_path = batch
            assert images.shape == (32, 3, 224, 224)
            assert torch.all(labels == dataloader_label)
        break


def test_offline_mslanet_dataloader():
    batch_size = 8
    dataloader = MSLANetDataLoader(
        limit=None,
        dynamic_load=True,
        normalize=True,
        normalization_statistics=IMAGENET_STATISTICS,
        batch_size=batch_size,
        load_synthetic=True,
        online_gradcam=False,
        upscale_train=False
    )
    train_loader = dataloader.get_train_dataloder()
    loader_steps = len(train_loader)
    for batch_i in tqdm(range(loader_steps)):
        try:
            batch = next(iter(train_loader))
        except Exception as e:
            print(f'Exception: {e}')
            continue


if __name__ == "__main__":
    test_dynamic_segmentation_dataloader()
