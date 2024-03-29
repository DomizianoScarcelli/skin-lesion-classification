from typing import Optional
from config import BATCH_SIZE, DATASET_LIMIT, KEEP_BACKGROUND, LOAD_SYNTHETIC, NORMALIZE
from dataloaders.DataLoader import DataLoader
from dataloaders.DynamicSegmentationDataLoader import DynamicSegmentationDataLoader
from dataloaders.ImagesAndSegmentationDataLoader import ImagesAndSegmentationDataLoader
from dataloaders.SegmentedImagesDataLoader import SegmentedImagesDataLoader
from shared.enums import DynamicSegmentationStrategy, SegmentationStrategy


def get_dataloder_from_strategy(strategy: SegmentationStrategy,
                                dynamic_segmentation_strategy: DynamicSegmentationStrategy = DynamicSegmentationStrategy.SAM,
                                limit: int = DATASET_LIMIT,
                                dynamic_load: bool = True,
                                oversample_train: bool = True,
                                normalize: bool = NORMALIZE,
                                normalization_statistics: tuple = None,
                                batch_size: int = BATCH_SIZE,
                                keep_background: Optional[bool] = KEEP_BACKGROUND,
                                load_synthetic: bool = LOAD_SYNTHETIC) -> DataLoader:

    if strategy == SegmentationStrategy.DYNAMIC_SEGMENTATION.value:
        dataloader = DynamicSegmentationDataLoader(
            limit=limit,
            dynamic_load=dynamic_load,
            upscale_train=oversample_train,
            segmentation_strategy=dynamic_segmentation_strategy,
            normalize=normalize,
            normalization_statistics=normalization_statistics,
            batch_size=batch_size,
            keep_background=keep_background,
            load_synthetic=load_synthetic,
        )
    elif strategy == SegmentationStrategy.SEGMENTATION.value:
        dataloader = SegmentedImagesDataLoader(
            limit=limit,
            dynamic_load=dynamic_load,
            upscale_train=oversample_train,
            normalize=normalize,
            normalization_statistics=normalization_statistics,
            batch_size=batch_size,
            keep_background=keep_background,

        )
    elif strategy == SegmentationStrategy.NO_SEGMENTATION.value:
        dataloader = ImagesAndSegmentationDataLoader(
            limit=limit,
            dynamic_load=dynamic_load,
            upscale_train=oversample_train,
            normalize=normalize,
            normalization_statistics=normalization_statistics,
            batch_size=batch_size,
            load_synthetic=load_synthetic,
        )
    else:
        raise NotImplementedError(
            f"Segmentation strategy {strategy} not implemented")
    return dataloader
