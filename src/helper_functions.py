import torch
import wandb
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.metrics import confusion_matrix

import seaborn as sns
import matplotlib.pyplot as plt

def train_model(model, train_loader, test_loader, optimizer, device, epochs=1):
    """
    Train the model and validate after each epoch.
    """
    for epoch in range(epochs):
        print(f"\nEpoch {epoch + 1}")
        
        model.train()
        train_preds, train_labels = [], []
        total_loss = 0

        # Training loop
        for batch in train_loader:
            # Move batch to device
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["labels"].to(device)

            optimizer.zero_grad()

            # Forward pass
            logits, loss = model(input_ids, attention_mask, labels)
            loss.backward()
            optimizer.step()

            total_loss += loss.item()
            preds = torch.argmax(logits, dim=1)
            train_preds.extend(preds.cpu().numpy())
            train_labels.extend(labels.cpu().numpy())

        # Compute training metrics
        avg_train_loss = total_loss / len(train_loader)
        acc = accuracy_score(train_labels, train_preds)
        prec = precision_score(train_labels, train_preds, average='macro')
        rec = recall_score(train_labels, train_preds, average='macro')
        f1 = f1_score(train_labels, train_preds, average='macro')
        f1_weighted = f1_score(train_labels, train_preds, average='weighted')

        print(f"Training Loss: {avg_train_loss:.4f}")
        print(f"Train Accuracy: {acc:.4f}")
        print(f"Train F1 (macro): {f1:.4f}\n")

        # Log results
        wandb.log({
            "epoch": epoch + 1,
            "train_loss": loss.item(),
            "train_accuracy": acc,
            "train_precision_macro": prec,
            "train_recall_macro": rec,
            "train_f1_macro": f1,
            "train_f1_weighted": f1_weighted
        })

        # Call the test_model function for validation after each epoch
        test_model(model, test_loader, device, phase="val")

        # Optionally save model after validation if needed
        # torch.save(model.state_dict(), f"model_epoch_{epoch + 1}.bin")


        

def test_model(model, data_loader, device, phase="test"):
    """
    Evaluates the model on the validation or test set.
    :param phase: One of ["val", "test"] for validation or final testing. Needed for correct logging with wandb
    """
    model.eval()
    all_preds, all_labels = [], []
    total_loss = 0

    for batch in data_loader:
        input_ids = batch["input_ids"].to(device)
        attention_mask = batch["attention_mask"].to(device)
        labels = batch["labels"].to(device)

        # Forward pass (no gradient calculation for validation or testing)
        with torch.no_grad():
            # The loss is required to optimise the model (backpropagation) and is no longer important for testing. 
            # But to make coding easier we opted to not do the case destinction
            logits, loss = model(input_ids, attention_mask, labels)

        preds = torch.argmax(logits, dim=1)
        all_preds.extend(preds.cpu().numpy())
        all_labels.extend(labels.cpu().numpy())

        total_loss += loss.item()

    # Compute metrics
    avg_test_loss = total_loss / len(data_loader)
    acc = accuracy_score(all_labels, all_preds)
    prec = precision_score(all_labels, all_preds, average='macro')
    rec = recall_score(all_labels, all_preds, average='macro')
    f1 = f1_score(all_labels, all_preds, average='macro')
    f1_weighted = f1_score(all_labels, all_preds, average='weighted')

    print(f"{phase.capitalize()} Loss: {avg_test_loss:.4f}")
    print(f"{phase.capitalize()} Accuracy: {acc:.4f}")
    print(f"{phase.capitalize()} F1 (macro): {f1:.4f}\n")

    # Log the metrics in wandb
    wandb.log({
        f"{phase}_loss": avg_test_loss,
        f"{phase}_accuracy": acc,
        f"{phase}_precision_macro": prec,
        f"{phase}_recall_macro": rec,
        f"{phase}_f1_macro": f1,
        f"{phase}_f1_weighted": f1_weighted
    })

    if phase  == "test":
        cm = confusion_matrix(all_labels, all_preds)
        fig = plt.figure(figsize=(6,4))
        sns.heatmap(cm, annot=True, fmt="d")
        wandb.log({"confusion_matrix": wandb.Image(fig)})
        wandb.finish()

    return
