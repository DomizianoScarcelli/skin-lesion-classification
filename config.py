import os

from shared.enums import DynamicSegmentationStrategy, SegmentationStrategy


DATA_DIR = 'data'
PATH_TO_SAVE_RESULTS = 'results'
DATASET_TRAIN_DIR = os.path.join(DATA_DIR, "HAM10000_images_train")
DATASET_TEST_DIR = os.path.join(DATA_DIR, "HAM10000_images_test")
SEGMENTATION_DIR = os.path.join(
    DATA_DIR, 'HAM10000_segmentations_lesion_tschandl')
SEGMENTATION_WITH_BOUNDING_BOX_DIR = os.path.join(
    DATA_DIR, 'HAM10000_segmentations_lesion_tschandl_with_bounding_box_450_600')
METADATA_TRAIN_DIR = os.path.join(DATA_DIR, 'HAM10000_metadata_train.csv')
METADATA_NO_DUPLICATES_DIR = os.path.join(
    DATA_DIR, 'HAM10000_metadata_train_no_duplicates.csv')
METADATA_TEST_DIR = os.path.join(DATA_DIR, 'HAM10000_metadata_test.csv')

BATCH_SIZE = 64

USE_WANDB = False
# DirectML library for AMD gpu on Windows (set to false if you want to use cpu or standard CUDA)
USE_DML = False
SAVE_RESULTS = True  # Save results in JSON locally
SAVE_MODELS = True  # Save models locally

# Configurations
RANDOM_SEED = 42
INPUT_SIZE = 3
NUM_CLASSES = 7
HIDDEN_SIZE = [32, 64, 128, 256]
N_EPOCHS = 5
LR = 1e-3
LR_DECAY = 0.85
REG = 0.01
ARCHITECTURE_CNN = "resnet24"
ARCHITECTURE_VIT = "pretrained"  # standard, pretrained, efficient
DATASET_LIMIT = None
DROPOUT_P = 0.3
NORMALIZE = True
# If true, the segmentation is approximated by a squared bounding box.
SEGMENTATION_BOUNDING_BOX = True
BALANCE_UNDERSAMPLING = 0.5
UPSAMPLE_TRAIN = True  # Decide if upsample with data augmentation the train set or not
# Use binary loss (benign/malign) and multiclassification loss if true, otherwise use only the multiclassification one
USE_DOUBLE_LOSS = True

SEGMENTATION_STRATEGY = SegmentationStrategy.NO_SEGMENTATION.value
DYNAMIC_SEGMENTATION_STRATEGY = DynamicSegmentationStrategy.OPENCV.value
# If true, the background is kept in the segmentation, otherwise it is removed
KEEP_BACKGROUND = False

if ARCHITECTURE_CNN == "inception_v3":
    IMAGE_SIZE = (299, 299)  # for inception_v3
else:
    IMAGE_SIZE = (224, 224)  # for the others

# Transformers configurations
N_HEADS = 1
N_LAYERS = 1
PATCH_SIZE = 16
EMB_SIZE = 800

# Resume
RESUME = False
PATH_MODEL_TO_RESUME = f"CNN_resnet24_2023-12-04_17-26-22"
RESUME_EPOCH = 2
