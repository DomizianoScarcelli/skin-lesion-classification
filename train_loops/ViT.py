import torch
from config import BALANCE_UNDERSAMPLING, BATCH_SIZE, DYNAMIC_SEGMENTATION_STRATEGY, INPUT_SIZE, NUM_CLASSES, HIDDEN_SIZE, N_EPOCHS, LR, REG, ARCHITECTURE_VIT, DATASET_LIMIT, DROPOUT_P, NORMALIZE, SEGMENTATION_BOUNDING_BOX, SEGMENTATION_STRATEGY, UPSAMPLE_TRAIN, USE_DOUBLE_LOSS, N_HEADS, N_LAYERS, PATCH_SIZE, EMB_SIZE, IMAGE_SIZE, RANDOM_SEED, RESUME, RESUME_EPOCH, PATH_MODEL_TO_RESUME, PATH_TO_SAVE_RESULTS
from constants import IMAGENET_STATISTICS, DEFAULT_STATISTICS
from utils.dataloader_utils import get_dataloder_from_strategy
from utils.utils import select_device, set_seed
from train_loops.train_loop import train_eval_loop
from models.ViTStandard import ViT_standard
from models.ViTPretrained import ViT_pretrained
from models.ViTEfficient import EfficientViT


def get_model(device):
    if ARCHITECTURE_VIT == "pretrained":
        model = ViT_pretrained(NUM_CLASSES, pretrained=True).to(device)
    elif ARCHITECTURE_VIT == "standard":
        model = ViT_standard(in_channels=INPUT_SIZE, patch_size=PATCH_SIZE, d_model=EMB_SIZE,
                             img_size=IMAGE_SIZE, n_classes=NUM_CLASSES, n_head=N_HEADS, n_layers=N_LAYERS).to(device)
    elif ARCHITECTURE_VIT == "efficient":
        model = EfficientViT(img_size=224, patch_size=16, in_chans=INPUT_SIZE, stages=['s', 's', 's'], embed_dim=[
                             64, 128, 192], key_dim=[16, 16, 16], depth=[1, 2, 3], window_size=[7, 7, 7], kernels=[5, 5, 5, 5])
    else:
        raise ValueError(f"Unknown architechture {ARCHITECTURE_VIT}")

    if RESUME:
        model.load_state_dict(torch.load(
            f"{PATH_TO_SAVE_RESULTS}/{PATH_MODEL_TO_RESUME}/models/melanoma_detection_{RESUME_EPOCH}.pt"))

    print(f"--Model-- Using ViT_{ARCHITECTURE_VIT} model")
    return model

def get_normalization_statistics():
    image_net_pretrained_models = ["pretrained"]
    if ARCHITECTURE_VIT in image_net_pretrained_models:
        return IMAGENET_STATISTICS
    else:
        return DEFAULT_STATISTICS


def main():
    set_seed(RANDOM_SEED)

    device = select_device()

    config = {
        "learning_rate": LR,
        "architecture": ARCHITECTURE_VIT,
        "epochs": N_EPOCHS,
        'reg': REG,
        'batch_size': BATCH_SIZE,
        "hidden_size": HIDDEN_SIZE,
        "dataset": "HAM10K",
        "optimizer": "AdamW",
        "dataset_limit": DATASET_LIMIT,
        "dropout_p": DROPOUT_P,
        "normalize": NORMALIZE,
        "resumed": RESUME,
        "from_epoch": RESUME_EPOCH,
        "segmentation_bounding_box": SEGMENTATION_BOUNDING_BOX,
        "balance_undersampling": BALANCE_UNDERSAMPLING,
        "initialization": "default",
        "segmentation_strategy": SEGMENTATION_STRATEGY,
        "dynamic_segmentation_strategy": DYNAMIC_SEGMENTATION_STRATEGY,
        "upsample_train": UPSAMPLE_TRAIN,
        "n_heads": N_HEADS,
        "n_layers": N_LAYERS,
        "patch_size": PATCH_SIZE,
        "emb_size": EMB_SIZE,
        "double_loss": USE_DOUBLE_LOSS
    }

    dataloader = get_dataloder_from_strategy(
        strategy=SEGMENTATION_STRATEGY,
        dynamic_segmentation_strategy=DYNAMIC_SEGMENTATION_STRATEGY,
        limit=DATASET_LIMIT,
        dynamic_load=True,
        upsample_train=UPSAMPLE_TRAIN,
        normalize=NORMALIZE,
        normalization_statistics=get_normalization_statistics(),
        batch_size=BATCH_SIZE)
    train_loader, val_loader = dataloader.get_train_val_dataloders()
    model = get_model(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=REG)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer, T_max=N_EPOCHS, eta_min=1e-5)

    train_eval_loop(device, train_loader=train_loader, val_loader=val_loader, model=model,
                    config=config, optimizer=optimizer, scheduler=scheduler, resume=RESUME)


if __name__ == "__main__":
    main()
