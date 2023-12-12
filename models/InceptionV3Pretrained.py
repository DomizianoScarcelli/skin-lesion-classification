from torch import nn
from torchvision import models
from torchvision.models import Inception_V3_Weights
from config import DROPOUT_P
import numpy as np


class InceptionV3Pretrained(nn.Module):
    def __init__(self, hidden_layers, num_classes):
        super(InceptionV3Pretrained, self).__init__()
        self.model = models.inception_v3(weights=Inception_V3_Weights.DEFAULT)

        self.dropout = nn.Dropout(p=DROPOUT_P)
        self.relu = nn.ReLU()

        self.layers = []
        if len(hidden_layers) == 0:
            self.layers.append(self.dropout)
            self.layers.append(nn.Linear(self.model.fc.in_features, num_classes, bias=False))
        else:
            self.layers.append(self.dropout)
            for i in range(len(hidden_layers)):
                if i == 0:
                    self.layers.append(nn.Linear(self.model.fc.in_features, hidden_layers[i], bias=False))
                    self.layers.append(self.relu)
                    self.layers.append(nn.BatchNorm1d(hidden_layers[i]))
                else:
                    self.layers.append(nn.Linear(hidden_layers[i-1], hidden_layers[i], bias=False))
                    self.layers.append(self.relu)
                    self.layers.append(nn.BatchNorm1d(hidden_layers[i]))
            self.layers.append(nn.Linear(hidden_layers[-1], num_classes, bias=False))
            self.layers.append(nn.BatchNorm1d(num_classes))
        
        self.classifier = nn.Sequential(*self.layers)
        self.model.fc = self.classifier

        model_parameters = filter(
            lambda p: p.requires_grad, self.model.parameters())
        params = sum([np.prod(p.size()) for p in model_parameters])
        print(f'Model has {params} trainable params.')

    def forward(self, x):
        if self.model.training:
            return self.model(x).logits
        return self.model(x)

    def initialize_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.kaiming_normal_(
                    m.weight, mode='fan_out', nonlinearity='relu')
                if m.bias:
                    nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.BatchNorm1d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
