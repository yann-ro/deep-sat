import os

import matplotlib.pyplot as plt
import torch
from torchvision.models.detection import (
    fasterrcnn_resnet50_fpn,
    fcos_resnet50_fpn,
    retinanet_resnet50_fpn_v2,
)
from tqdm.notebook import tqdm

from .core.model import Model
from .display_pred_inst import display_img_with_bbox


def get_model_inst(
    num_classes,
    model_name="faster_rcnn",
    pretrained_head=False,
    pretrained_backbone=False,
):
    if model_name == "faster_rcnn":
        model = fasterrcnn_resnet50_fpn(
            num_classes=num_classes,
            pretrained=pretrained_head,
            pretrained_backbone=pretrained_backbone,
        )

    if model_name == "fcos_resnet":
        model = fcos_resnet50_fpn(
            num_classes=num_classes,
            pretrained=pretrained_head,
            pretrained_backbone=pretrained_backbone,
        )

    if model_name == "retinanet":
        model = retinanet_resnet50_fpn_v2(
            num_classes=num_classes,
            pretrained=pretrained_head,
            pretrained_backbone=pretrained_backbone,
        )

    return model


class InstModel(Model):
    def __init__(self, model, model_name, device, threshold=None):
        self.model = model
        self.model_name = model_name
        self.device = device
        self.history = {}
        self.threshold = threshold

    def fit(
        self,
        epochs,
        train_loader,
        optimizer=None,
        val_loader=None,
        criterion=None,
        scheduler=None,
    ):
        self.model.to(self.device)

        params = [p for p in self.model.parameters() if p.requires_grad]
        optimizer = torch.optim.SGD(params, lr=0.005, momentum=0.9, weight_decay=0.0005)

        self.history["loss"] = []

        for epoch in range(epochs):
            self.model.train()

            hist_loss = 0
            for imgs, annotations in tqdm(train_loader):
                imgs = list(img.to(self.device) for img in imgs)
                annotations = [
                    {k: v.to(self.device) for k, v in t.items()} for t in annotations
                ]
                loss_dict = self.model(imgs, annotations)
                losses = sum(loss for loss in loss_dict.values())

                hist_loss += losses

                optimizer.zero_grad()
                losses.backward()
                optimizer.step()

            self.history["loss"].append(hist_loss)
            print(f"Epoch: {epoch}, Loss: {hist_loss}")

            self.display_output(train_loader.dataset, [0, 1, 2, 3, 4])

    def save(self, path_folder):
        torch.save(self.model, os.path.join(path_folder, self.model_name))

    def display_output(self, test_set, list_id, threshold=0):
        self.model.eval()
        fig, axs = plt.subplots(1, len(list_id), figsize=(20, 10))

        for i, id in enumerate(list_id):
            img, _ = test_set[id]
            (pred,) = self.model(img[None, :].to(self.device))

            display_img_with_bbox(
                axs[i],
                img.permute(1, 2, 0).cpu(),
                pred,
                from_pred=True,
                threshold=threshold,
            )
        plt.show()
