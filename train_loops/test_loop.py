import torch
import torch.nn as nn
from sklearn.metrics import recall_score, accuracy_score
from utils.utils import save_results, set_seed, select_device
from utils.dataloader_utils import get_dataloder_from_strategy
from dataloaders.DataLoader import DataLoader
from config import USE_DOUBLE_LOSS, BATCH_SIZE, SAVE_RESULTS, DATASET_LIMIT, NORMALIZE, RANDOM_SEED, PATH_TO_SAVE_RESULTS, NUM_CLASSES, HIDDEN_SIZE, INPUT_SIZE, IMAGE_SIZE, PATCH_SIZE, EMB_SIZE, N_HEADS, N_LAYERS
from constants import DEFAULT_STATISTICS, IMAGENET_STATISTICS
from shared.enums import DynamicSegmentationStrategy, SegmentationStrategy
from models.ResNet24Pretrained import ResNet24Pretrained
from models.DenseNetPretrained import DenseNetPretrained
from models.InceptionV3Pretrained import InceptionV3Pretrained
from models.ViTStandard import ViT_standard
from models.ViTPretrained import ViT_pretrained
from models.ViTEfficient import EfficientViT


def test(test_model, test_loader, device, data_name):
    loss_function_multiclass = nn.CrossEntropyLoss()
    if USE_DOUBLE_LOSS:
        loss_function_binary = nn.CrossEntropyLoss()
    test_model.eval()
    test_loss_iter = 0
    epoch_test_preds = torch.tensor([]).to(device)
    epoch_test_labels = torch.tensor([]).to(device)

    with torch.no_grad():
        for _, (test_images, test_labels) in enumerate(test_loader):
            test_images = test_images.to(device)
            test_labels = test_labels.to(device)

            test_outputs = test_model(test_images)
            test_preds = torch.argmax(test_outputs, -1).detach()
            epoch_test_preds = torch.cat((epoch_test_preds, test_preds), 0)
            epoch_test_labels = torch.cat((epoch_test_labels, test_labels), 0)

            # First loss: Multiclassification loss considering all classes
            test_epoch_loss_multiclass = loss_function_multiclass(
                test_outputs, test_labels)
            test_epoch_loss = test_epoch_loss_multiclass

            if USE_DOUBLE_LOSS:
                test_labels_binary = torch.zeros_like(
                    test_labels, dtype=torch.long).to(device)
                # Set ground-truth to 1 for classes 0, 1, and 6 (the malignant classes)
                test_labels_binary[(test_labels == 0) | (
                    test_labels == 1) | (test_labels == 6)] = 1

                # Second loss: Binary loss considering only benign/malignant classes
                test_outputs_binary = torch.zeros_like(
                    test_outputs[:, :2]).to(device)
                test_outputs_binary[:, 1] = torch.sum(
                    test_outputs[:, [0, 1, 6]], dim=1)
                test_outputs_binary[:, 0] = 1 - test_outputs_binary[:, 1]

                test_epoch_loss_binary = loss_function_binary(
                    test_outputs_binary, test_labels_binary)

                # Sum of the losses
                test_epoch_loss += test_epoch_loss_binary

            test_loss_iter += test_epoch_loss.item()

        test_loss = test_loss_iter / (len(test_loader) * BATCH_SIZE)
        test_accuracy = accuracy_score(
            epoch_test_labels.cpu().numpy(), epoch_test_preds.cpu().numpy()) * 100
        test_recall = recall_score(epoch_test_labels.cpu().numpy(
        ), epoch_test_preds.cpu().numpy(), average='macro', zero_division=0) * 100

        print('Test -> Loss: {:.4f}, Accuracy: {:.4f}%, Recall: {:.4f}%'.format(
            test_loss, test_accuracy, test_recall))

        test_results = {
            'test_accuracy': test_accuracy,
            'test_recall': test_recall,
            'test_loss': test_loss
        }
        if SAVE_RESULTS:
            save_results(data_name, test_results, test=True)
        # return test_loss, test_accuracy, test_recall


def get_model(type, device):
    if type == "resnet24":
        model = ResNet24Pretrained(
            INPUT_SIZE, HIDDEN_SIZE, NUM_CLASSES, norm_layer='BN').to(device)
        normalization_stats = IMAGENET_STATISTICS
    elif type == "densenet121":
        model = DenseNetPretrained(
            INPUT_SIZE, HIDDEN_SIZE, NUM_CLASSES, norm_layer='BN').to(device)
        normalization_stats = IMAGENET_STATISTICS
    elif type == "inception_v3":
        model = InceptionV3Pretrained(NUM_CLASSES).to(device)
        normalization_stats = IMAGENET_STATISTICS
    elif type == "standard":
        model = ViT_pretrained(NUM_CLASSES, pretrained=True).to(device)
        normalization_stats = None
    elif type == "pretrained":
        model = ViT_standard(in_channels=INPUT_SIZE, patch_size=PATCH_SIZE, d_model=EMB_SIZE,
                             img_size=IMAGE_SIZE, n_classes=NUM_CLASSES, n_head=N_HEADS, n_layers=N_LAYERS).to(device)
        normalization_stats = IMAGENET_STATISTICS
    elif type == "efficient":
        model = EfficientViT(img_size=224, patch_size=16, in_chans=INPUT_SIZE, stages=['s', 's', 's'], embed_dim=[
                             64, 128, 192], key_dim=[16, 16, 16], depth=[1, 2, 3], window_size=[7, 7, 7], kernels=[5, 5, 5, 5])
        normalization_stats = None
    else:
        raise ValueError(f"Unknown architecture {type}")

    return model, normalization_stats


def load_test_model(model, model_path, epoch):
    test_model = model.load_state_dict(torch.load(
        f"{PATH_TO_SAVE_RESULTS}/{model_path}/models/melanoma_detection_ep{epoch}.pt"))
    return test_model


def main(model_path, type, epoch):
    set_seed(RANDOM_SEED)
    device = select_device()
    model_type, normalization_stats = get_model(type, device)
    test_model = load_test_model(model_type, model_path, epoch)

    dataloader = get_dataloder_from_strategy(
        strategy=SegmentationStrategy.NO_SEGMENTATION.value,
        limit=DATASET_LIMIT,
        dynamic_load=True,
        normalize=NORMALIZE,
        normalization_statistics=normalization_stats,
        batch_size=BATCH_SIZE)
    test_dataloader = dataloader.get_test_dataloader()
    print(test_model)
    test(test_model, test_dataloader, device, model_path)


if __name__ == "__main__":
    model_path = "resnet24_2023-12-07_17-13-18"
    type = "resnet24"
    epoch = 2

    main(model_path, type, epoch)