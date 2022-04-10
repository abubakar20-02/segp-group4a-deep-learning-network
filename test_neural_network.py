import matplotlib.pyplot as plt
import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision.utils import save_image


def get_image():
    return ProducedImageTensor


def load_model(data):

    file = open("CorrectFileReceived.txt", 'w')
    file.write('1')
    file.close()

    file = open("Path.txt", 'r')
    FileName = file.readline().strip()
    file.close()

    model = Net()
    try:
        model.load_state_dict(torch.load(FileName, map_location=torch.device('cpu')), strict=False)
    except:
        file = open("CorrectFileReceived.txt", 'w')
        file.write('0')
        file.close()
        print("Model could not be loaded. Please verify that the file is a trained neural network.")
    model.eval()
    global ProducedImageTensor
    ProducedImageTensor = model(data.float(), 120, 160)
    pltTensor = ProducedImageTensor.cpu().detach().numpy()
    plt.cla()
    plt.imshow(pltTensor[0])
    plt.show()
    ProducedImageTensor = ProducedImageTensor.squeeze(0)
    save_image_from_tensor(ProducedImageTensor)
    return ProducedImageTensor
    # produced_image_tensor = model(data.float(),120,160)
    # print(produced_image_tensor)


# Saves a single tensor as an image to file
def save_image_from_tensor(image_tensor, height=500, width=666):
    # swap tensor axes so 'channels' is first
    image_tensor = image_tensor.swapaxes(2, 1)
    image_tensor = image_tensor.swapaxes(1, 0)
    save_image(image_tensor, "temp2.png")
    print('Before conversion {}'.format(image_tensor.dtype))
    # resize image to 666 * 500
    image_tensor = F.interpolate(image_tensor.unsqueeze(0).float(), size=(height, width), mode='nearest').squeeze(
        0).float()
    # name of the saved file
    file_name = 'temp.png'
    # save image
    print('After conversion {}'.format(image_tensor.dtype))
    save_image(image_tensor, file_name)


class Net(nn.Module):

    #Below are the layers applied during training
    def __init__(self):
        super(Net, self).__init__()
        self.fc1 = nn.Linear(11, 2000)
        self.batchnorm1 = nn.BatchNorm2d(64)
        self.relu = nn.ReLU()
        self.dropout1 = nn.Dropout(0.25)
        self.batchnorm2 = nn.BatchNorm2d(128)

        self.dropout2 = nn.Dropout2d(0.25)

        self.fc2 = nn.Linear(2000,19200)

        self.Convolution1 = nn.Conv2d(36,64, (3, 3), padding=1, bias = True)
        self.dropout3 = nn.Dropout2d(0.25)
        self.batchnorm3 = nn.BatchNorm2d(64)
        self.Convolution2 = nn.Conv2d(64, 128, (3, 3), padding=1, bias = True)
        self.Convolution3 = nn.Conv2d(128, 64, (3, 3), padding = 1, bias = True)
        self.Convolution4 = nn.Conv2d(64, 3, (3, 3), padding = 1, bias = True)




    # x represents our data
    def forward(self, x, originalimageheight, originalimagewidth):


        torch.set_printoptions(threshold=10_000)

        out = self.fc1(x)
        leakRelu = nn.ReLU()
        out = leakRelu(out)
        #out = self.dropout1(out)
        out = self.fc2(out)

        test_shape = torch.reshape(out, (12,40,40)) #Formula : input_size = channels * sqr_root(dimension)


        #changes the shape of the data
        test_shape = F.interpolate(test_shape,originalimagewidth, mode='linear', align_corners = True)
        test_shape = test_shape.permute(0,2,1)
        test_shape = F.interpolate(test_shape,originalimageheight, mode='linear', align_corners = True)
        test_shape = test_shape.permute(2,1,0)
        test_shape = F.interpolate(test_shape,36)
        test_shape = test_shape.permute(2,1,0)
        test_shape = test_shape.permute(0,2,1)

        test_shape = test_shape.unsqueeze(0)

        #1st Convolutional Layer
        test_shape=self.Convolution1(test_shape)
        #test_shape=self.batchnorm1(test_shape)
        leakRelu = nn.ReLU()
        test_shape=leakRelu(test_shape)
        #test_shape=self.dropout3(test_shape)

        #2nd Convolutional Layer
        test_shape=self.Convolution2(test_shape)
       # test_shape=self.batchnorm2(test_shape)
        leakRelu = nn.ReLU()
        test_shape=leakRelu(test_shape)
        #test_shape=self.dropout3(test_shape)


        #Last Convolutional Layer
        test_shape = self.Convolution3(test_shape)
        #test_shape = self.batchnorm3(test_shape)
        leakRelu = nn.ReLU()
        test_shape = leakRelu(test_shape)

        #last layer
        test_shape = self.Convolution4(test_shape)
        #m = nn.MaxPool2d(3, stride=1, padding=1)
        #test_shape = m(test_shape)
        #test_shape=leakRelu(test_shape)
        test_shape = test_shape.swapaxes(1,2) #reverse order to 'width, height, channels'
        test_shape = test_shape.swapaxes(2,3)
        return test_shape