import os

from shared.enums import DynamicSegmentationStrategy, SegmentationStrategy


DATA_DIR = 'data'
PATH_TO_SAVE_RESULTS = 'results'
DATASET_TRAIN_DIR = os.path.join(DATA_DIR, "HAM10000_images_train")
# DATASET_TEST_DIR = os.path.join(DATA_DIR, "HAM10000_images_test")
SEGMENTATION_DIR = os.path.join(
    DATA_DIR, 'HAM10000_segmentations_lesion_tschandl')
# SEGMENTATION_WITH_BOUNDING_BOX_DIR = os.path.join(
# DATA_DIR, 'HAM10000_segmentations_lesion_tschandl_with_bounding_box_450_600')
METADATA_TRAIN_DIR = os.path.join(
    DATA_DIR, 'HAM10000_metadata_train_no_duplicates.csv')
# METADATA_NO_DUPLICATES_DIR = os.path.join(
# DATA_DIR, 'HAM10000_metadata_train.csv')
# METADATA_TEST_DIR = os.path.join(DATA_DIR, 'HAM10000_metadata_test.csv')

BATCH_SIZE = 128


USE_WANDB = False  # Use wandb for logging
# DirectML library for AMD gpu on Windows (set to false if you want to use cpu or standard CUDA)
USE_DML = False
USE_MPS = True  # Use MPS gpu for MacOS
SAVE_RESULTS = True  # Save results in JSON locally
SAVE_MODELS = True  # Save models locally
PRINT_MODEL_ARCHITECTURE = False  # Print the architecture of the model

# Configurations
RANDOM_SEED = 42
INPUT_SIZE = 3
NUM_CLASSES = 7
'''
ResNet HIDDEN_SIZE = [256, 128]
DenseNet HIDDEN_SIZE = [512, 256, 128]
Inception HIDDEN_SIZE = [512, 256, 128]
ViT_Pretrained HIDDEN_SIZE = [256, 128]
'''
HIDDEN_SIZE = [512, 256, 128]
N_EPOCHS = 10
LR = 1e-3
LR_DECAY = 0.85
REG = 0.06
# resnet24, densenet121, inception_v3, standard, pretrained, efficient
ARCHITECTURE = "resnet24"
DATASET_LIMIT = None
DROPOUT_P = 0.5
NORMALIZE = True
BALANCE_UNDERSAMPLING = 1
UPSAMPLE_TRAIN = True  # Decide if upsample with data augmentation the train set or not
# Use binary loss (benign/malign) and multiclassification loss if true, otherwise use only the multiclassification one
USE_DOUBLE_LOSS = True

SEGMENTATION_STRATEGY = SegmentationStrategy.DYNAMIC_SEGMENTATION.value
DYNAMIC_SEGMENTATION_STRATEGY = DynamicSegmentationStrategy.SAM.value
# If true, the background is kept in the segmentation, otherwise it is removed
KEEP_BACKGROUND = True

if ARCHITECTURE == "inception_v3":
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
PATH_MODEL_TO_RESUME = f"resnet24_2023-12-09_09-09-54"
RESUME_EPOCH = 2
