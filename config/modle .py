import torch
import torch.nn as nn
import torch.utils.data as Data
import torchvision
import time
import os
from torchvision import models
import matplotlib.pyplot as plt

class MyCNN(nn.Module):
    """
    网络模型
    """
    def __init__(self, image_size, num_classes):
        super(MyCNN, self).__init__()
        # conv1: Conv2d -> BN -> ReLU -> MaxPool
        self.conv1 = nn.Sequential(
            nn.Conv2d(in_channels=3, out_channels=16, kernel_size=3, stride=1, padding=1),
            nn.Conv2d(in_channels=16, out_channels=16, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(16),
            nn.ReLU(), 
            nn.MaxPool2d(kernel_size=2, stride=1),
        )
        # conv2: Conv2d -> BN -> ReLU -> MaxPool
        self.conv2 = nn.Sequential(
            nn.Conv2d(in_channels=16, out_channels=32, kernel_size=3, stride=1, padding=1),
            nn.Conv2d(in_channels=32, out_channels=32, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2, stride=2),
        )
        self.conv3 = nn.Sequential(
            nn.Conv2d(in_channels=32, out_channels=64, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2, stride=2),
        )
        self.conv4 = nn.Sequential(
            nn.Conv2d(in_channels=64, out_channels=64, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2, stride=2),
        )
        self.conv5 = nn.Sequential(
            nn.Conv2d(in_channels=64, out_channels=128, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2, stride=1),
        )
        # fully connected layer
        self.dp1 = nn.Dropout(0.20)
        self.fc1 = nn.Linear(4608, 256)
        self.dp2 = nn.Dropout(0.50)
        self.fc2 = nn.Linear(256, num_classes)

    def forward(self, x):
        """
        input: N * 3 * image_size * image_size
        output: N * num_classes
        """
        x = self.conv1(x)
        x = self.conv2(x)
        x = self.conv3(x)
        x = self.conv4(x)
        x = self.conv5(x)
        # view(x.size(0), -1): change tensor size from (N ,H , W) to (N, H*W)
        x = x.view(x.size(0), -1)
        x = self.dp1(x)
        x = self.fc1(x)
        x = self.dp2(x)
        output = self.fc2(x)
        return output


def getRsn():
    model = models.resnet18(pretrained=True)
    num_fc_in = model.fc.in_features
    model.fc = nn.Linear(num_fc_in, 6)
    return model


def getMbnet():
    model = models.mobilenet_v2(pretrained=True)
    model.classifier = nn.Sequential(
        nn.Linear(in_features=1280, out_features=64),
        nn.Dropout(p=0.5, inplace=False),
        nn.Linear(in_features=64, out_features=6, bias=True),
    )
    return model


def train(model, train_loader, loss_func, optimizer, device):
    """
    训练模型
    train model using loss_fn and optimizer in an epoch.
    model: CNN networks
    train_loader: a Dataloader object with training data
    loss_func: loss function
    device: train on cpu or gpu device
    """
    total_loss = 0
    # train the model using minibatch
    for i, (images, targets) in enumerate(train_loader):
        images = images.to(device)
        targets = targets.to(device)

        # forward
        outputs = model(images)
        _, preds = torch.max(outputs.data, 1)
        loss = loss_func(outputs, targets)

        # backward and optimize
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        total_loss += loss.item()
        if (i + 1) % 100 == 0:
            print("Step [{}/{}] Train Loss: {:.4f} Train acc".format(i + 1, len(train_loader), loss.item()))
    save_model(model, save_path="results/cnn.pth")
    return total_loss / len(train_loader)


def evaluate(model, val_loader, device, name):
    """
    评估模型
    model: CNN networks
    val_loader: a Dataloader object with validation data
    device: evaluate on cpu or gpu device
    return classification accuracy of the model on val dataset
    """
    # evaluate the model
    model.eval()
    # context-manager that disabled gradient computation
    with torch.no_grad():
        correct = 0
        total = 0

        for i, (images, targets) in enumerate(val_loader):
            # device: cpu or gpu
            images = images.to(device)

