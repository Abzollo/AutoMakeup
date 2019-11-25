
import torch
import torchvision.utils as vutils
import matplotlib.pyplot as plt
import matplotlib.animation as animation


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


def generate_grid(generator, latent):
    """
    Check generator's output on latent vectors and return it.

    Args:
        generator: The generator.
        latent: Latent vector from which an image grid will be generated.

    Returns:
        A grid of images generated by `generator` from `latent`.
    """

    # @TODO: check latent.size()[0] == 64, or adjust make_grid(nrows=?, ...) below

    with torch.no_grad():
        fake = generator(latent).detach()

    image_grid = vutils.make_grid(fake.cpu(), padding=2, normalize=True)

    return image_grid


def generate_applier_grid(applier, plain_faces):

    if len(plain_faces.size()) == 3:
        plain_faces.unsqueeze(0)

    num_faces = plain_faces.size()[0]
    img_dim = plain_faces.size()[1:]

    with torch.no_grad():
        makeup_faces = applier(plain_faces)

    num_cols = 2
    row = torch.zeros([num_cols * num_faces, *img_dim])
    row[0::num_cols] = plain_faces.detach()
    row[1::num_cols] = makeup_faces.detach()

    image_grid = vutils.make_grid(row.cpu(), nrow=num_cols, padding=2, normalize=True)

    return image_grid




