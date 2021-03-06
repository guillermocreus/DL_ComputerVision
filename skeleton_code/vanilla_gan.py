#  COMP 6211D & ELEC 6910T , Assignment 3
#
# This is the main training file for the vanilla GAN part of the assignment.
#
# Usage:
# ======
#    To train with the default hyperparamters (saves results to checkpoints_vanilla/ and samples_vanilla/):
#       python vanilla_gan.py

import os
import argparse
import warnings
import numpy as np
import matplotlib.pyplot as plt
warnings.filterwarnings("ignore")

# Torch imports
import torch
import torch.nn as nn
import torch.optim as optim

# Local imports
from data_loader import get_emoji_loader
from models import CycleGenerator, DCDiscriminator
from vanilla_utils import create_dir, create_model, checkpoint, sample_noise, save_samples

SEED = 11

# Set the random seed manually for reproducibility.
np.random.seed(SEED)
torch.manual_seed(SEED)

def train(train_loader, opt, device):

    G, D = create_model(opts)

    G.to(device)
    D.to(device)

    g_optimizer = optim.Adam(G.parameters(), opts.lr, [opts.beta1, opts.beta2])
    d_optimizer = optim.Adam(D.parameters(), opts.lr, [opts.beta1, opts.beta2])

    fixed_noise = sample_noise(16, opts.noise_size).to(device)

    iteration = 1

    mse_loss = torch.nn.MSELoss()
#     bce_loss = torch.nn.BCELoss()
    total_train_iters = opts.num_epochs * len(train_loader)

    all_gen_losses = []
    all_disc_losses = []

    for epoch in range(opts.num_epochs):
        print(f"Epoch: {epoch + 1}/{opts.num_epochs}")

        gen_losses = []
        disc_losses = []

        for batch in train_loader:

            real_images = batch[0].to(device)

            ################################################
            ###         TRAIN THE DISCRIMINATOR         ####
            ################################################

            d_optimizer.zero_grad()

            # FILL THIS IN
            # 1. Compute the discriminator loss on real images
            D_real_loss = ((D(real_images) - 1)**2).sum()
            D_real_loss /= 2 * real_images.shape[0]

            # 2. Sample noise
            noise = sample_noise(opts.batch_size,
                                 opts.noise_size).to(device)

            # 3. Generate fake images from the noise
            fake_images = G(noise)

            # 4. Compute the discriminator loss on the fake images
            D_fake_loss = (D(fake_images)**2).sum()
            D_fake_loss /= 2 * fake_images.shape[0]

            # 5. Compute the total discriminator loss
            D_total_loss = D_real_loss + D_fake_loss

            D_total_loss.backward()
            d_optimizer.step()

            ###########################################
            ###          TRAIN THE GENERATOR        ###
            ###########################################

            g_optimizer.zero_grad()

            # FILL THIS IN
            # 1. Sample noise
            noise = sample_noise(opts.batch_size,
                                 opts.noise_size).to(device)

            # 2. Generate fake images from the noise
            fake_images = G(noise)

            # 3. Compute the generator loss
            G_loss = ((D(fake_images) - 1)**2).sum()
            G_loss /= fake_images.shape[0]

            G_loss.backward()
            g_optimizer.step()

            gen_losses.append(G_loss.item())
            disc_losses.append(D_total_loss.item())

            # Print the log info
            if iteration % opts.log_step == 0:
                print('Iteration [{:4d}/{:4d}] | D_real_loss: {:6.4f} | D_fake_loss: {:6.4f} | G_loss: {:6.4f}'.format(
                    iteration, total_train_iters, D_real_loss.item(), D_fake_loss.item(), G_loss.item()))

            # Save the generated samples
            if iteration % opts.sample_every == 0:
                save_samples(G, fixed_noise, iteration, opts)

            # Save the model parameters
            if iteration % opts.checkpoint_every == 0:
                checkpoint(iteration, G, D, opts)

            iteration += 1

        all_gen_losses.append(np.mean(gen_losses))
        all_disc_losses.append(np.mean(disc_losses))

    plt.xlabel("Epochs")
    plt.ylabel("Generator loss")
    plt.title("DCGAN - Generator")
    plt.plot(all_gen_losses)
    # plt.xticks(list(range(1, opts.num_epochs + 1)),
    #            list(range(1, opts.num_epochs + 1)))
    plt.show()
    plt.clf()

    plt.xlabel("Epochs")
    plt.ylabel("Discriminator loss")
    plt.title("DCGAN - Discriminator")
    plt.plot(all_disc_losses)
    # plt.xticks(list(range(1, opts.num_epochs + 1)),
    #           list(range(1, opts.num_epochs + 1)))
    plt.show()
    plt.clf()


def main(opts):
    """Loads the data, creates checkpoint and sample directories, and starts the training loop.
    """

    # Create a dataloader for the training images
    train_loader, _ = get_emoji_loader(opts.emoji, opts)

    # Create checkpoint and sample directories
    create_dir(opts.checkpoint_dir)
    create_dir(opts.sample_dir)

    if torch.cuda.is_available():
        device = torch.device('cuda')
    else:
        device = torch.device('cpu')

    train(train_loader, opts, device)


def create_parser():
    """Creates a parser for command-line arguments.
    """
    parser = argparse.ArgumentParser()

    # Model hyper-parameters
    parser.add_argument('--image_size', type=int, default=32,
                        help='The side length N to convert images to NxN.')
    parser.add_argument('--conv_dim', type=int, default=32)
    parser.add_argument('--noise_size', type=int, default=100)

    # Training hyper-parameters
    parser.add_argument('--num_epochs', type=int, default=1000)
    parser.add_argument('--batch_size', type=int, default=16,
                        help='The number of images in a batch.')
    parser.add_argument('--num_workers', type=int, default=0,
                        help='The number of threads to use for the DataLoader.')
    parser.add_argument('--lr', type=float, default=0.0003,
                        help='The learning rate (default 0.0003)')
    parser.add_argument('--beta1', type=float, default=0.5)
    parser.add_argument('--beta2', type=float, default=0.999)

    # Data sources
    parser.add_argument('--emoji', type=str, default='Apple', choices=[
                        'Apple', 'Facebook', 'Windows'], help='Choose the type of emojis to generate.')

    # Directories and checkpoint/sample iterations
    parser.add_argument('--checkpoint_dir', type=str,
                        default='./checkpoints_vanilla')
    parser.add_argument('--sample_dir', type=str, default='./samples_vanilla')
    parser.add_argument('--log_step', type=int, default=10)
    parser.add_argument('--sample_every', type=int, default=200)
    parser.add_argument('--checkpoint_every', type=int, default=400)

    return parser


if __name__ == '__main__':

    parser = create_parser()
    opts = parser.parse_args()

    batch_size = opts.batch_size

    print(opts)
    main(opts)
