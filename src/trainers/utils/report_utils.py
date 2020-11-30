
import torch
import torchvision.utils as vutils
import matplotlib.pyplot as plt
import matplotlib.animation as animation

from math import log2, floor


def plot_lines(losses_dict, filename=None, title=""):
    """
    Plots the losses of the discriminator and the generator.

    Args:
        filename: The plot's filename. If None, plot won't be saved.
    """

    plt.figure(figsize=(10,5))
    plt.title(title)
    for label, losses in losses_dict.items():
        plt.plot(losses, label=label)
    plt.xlabel("t")
    plt.legend()
    
    if filename is not None:
        plt.savefig(filename)
    
    plt.show()
    plt.close()


def create_progress_animation(frames, filename):
    """
    Creates a video of the progress of the generator on a fixed latent vector.

    Args:
        filename: The animation's filename.
    """

    fig = plt.figure(figsize=(8,8))
    plt.axis("off")
    ims = [[plt.imshow(img.permute(1,2,0), animated=True)]
           for img in frames]
    ani = animation.ArtistAnimation(fig, ims, blit=True)
    
    ani.save(filename)

    plt.close()


def generate_grid(generator, latent):
    """
    Check generator's output on latent vectors and return it.

    Args:
        generator: The generator.
        latent: Latent vector from which an image grid will be generated.

    Returns:
        A grid of images generated by `generator` from `latent`.
    """

    with torch.no_grad():
        fake = generator(latent).detach()

    image_grid = vutils.make_grid(fake.cpu(), padding=2, normalize=True, range=(-1,1))

    return image_grid


def generate_G_grid(generator, before):
    """
    Generate a grid of pairs of images, where each pair shows a before-after
    transition when applying G on before.
    """

    if len(before.size()) == 3:
        before.unsqueeze(0)

    batch_size = before.size()[0]
    img_dim = before.size()[1:]

    with torch.no_grad():
        after = generator(before)

    row = torch.zeros([2 * batch_size, *img_dim])
    row[0::2] = before.detach()
    row[1::2] = after.detach()

    image_grid = vutils.make_grid(row.cpu(), nrow=8, padding=2, normalize=True, range=(-1,1))

    return image_grid


def generate_makeup_grid(applier_ref, remover, before, after_ref):
    """
    Generate a grid, 8 images per row, as follows:
      Image #1: real photo of a face WITHOUT makeup (call it face #1).
      Image #2: real (makeup reference) photo of a face WITH makeup (call it face #2).
      Image #3: fake photo of face #1 WITH makeup style from face #2 (applied).
      Image #4: fake photo of face #2 WITHOUT makeup (removed).
      Image #5: Repeat the same pattern from Image #1...

    In case only 4 images are needed per row, change `nrow` below to 4.
    """

    if len(before.size()) == 3:
        before.unsqueeze(0)

    batch_size = before.size()[0]
    img_dim = before.size()[1:]

    with torch.no_grad():
        fake_after = applier_ref(before, after_ref)
        fake_before_ref = remover(after_ref)


    row = torch.zeros([4 * batch_size, *img_dim])
    row[0::4] = before.detach()
    row[1::4] = after_ref.detach()
    row[2::4] = fake_after.detach()
    row[3::4] = fake_before_ref.detach()

    image_grid = vutils.make_grid(row.cpu(), nrow=8, padding=2, normalize=True, range=(-1,1))

    return image_grid

