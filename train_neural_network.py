import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import numpy as np
import matplotlib.pyplot as plt
import os
from os.path import exists
from glob import glob
from torchvision import transforms
from PIL import Image
import math
from torchvision.utils import save_image
from Training_Page_Integration import get_image,refresh_image,update_progress_bar,update_loss_bar
import extract_data as extract
os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'


# Normalise the dataset
def create_dataset(data):
    # normalize the data to be in range [0,1]
    NormData = (data - data.min()) / (data.max() - data.min())
    return NormData


# Splits dataframe into subsets and returns the values
def split_dataset(data, training_ratio):
    rows = len(data.index)
    training_ratio = int(float(training_ratio))
    split_percentage = math.floor(rows * (training_ratio / 100))  # split amount

    training_set = data.iloc[:split_percentage, :]  # all rows before the split index

    test_set = data.iloc[split_percentage:, :]  # all rows after the split index
    return (training_set, test_set)


# Opens and accesses the data of the raw data files in order to convert them into tensor
def getOriginalImage(file_num):
    # hardcoded path name and file type
    file_path1 = original_image + "/1.0/SR000" + str(file_num) + ".BMT"
    file_path2 = original_image + "/1.0/SR00" + str(file_num) + ".BMT"
    file_exist1 = exists(file_path1)
    file_exist2 = exists(file_path2)
    if file_exist1:
        img = Image.open(file_path1)
    elif file_exist2:
        img = Image.open(file_path2)
    else:
        return [0, 0, 0]
    convert_tensor = transforms.ToTensor()
    OriginalImageTensor = convert_tensor(img)

    if OriginalImageTensor.shape[1] != 120 or OriginalImageTensor.shape[2] != 160:
        OriginalImageTensor = F.interpolate(OriginalImageTensor, 160)
        OriginalImageTensor = OriginalImageTensor.swapaxes(1, 2)
        OriginalImageTensor = F.interpolate(OriginalImageTensor, 120)
        OriginalImageTensor = OriginalImageTensor.swapaxes(1, 2)

    OriginalImageTensor = OriginalImageTensor.swapaxes(0, 1)
    OriginalImageTensor = OriginalImageTensor.swapaxes(1, 2)
    return OriginalImageTensor


# Trains the neural network to convert data into an image
def training(training_data, testing_data, epoch_num, mode, learning_rate, momentum,preview_image,original_image_widget,progress_bar,epoch_loss_widget,total_loss_widget):
    learning_rate = int(float(learning_rate))
    momentum = int(float(momentum))
    epoch_num = int(float(epoch_num))
    # set up loss functions
    criterion = nn.CrossEntropyLoss()

    device = torch.device('cuda' if (torch.cuda.is_available() and mode == 2) else 'cpu')
    global model
    model = Net()
    if mode == 2:
        model = model.to(device)  # CUDA CODE
    class_instance = model.float()
    optimizer = optim.SGD(class_instance.parameters(), lr=0.009, momentum=0.9)
    loss_function = nn.L1Loss()
    total_training_loss = 0
    total_validation_loss = 0
    count = 0
    global training_loss_arr
    training_loss_arr = []
    global validation_loss_arr
    validation_loss_arr = []

    # trains network for each image (non-epoch)
    for epoch in range(epoch_num):
        torch.cuda.empty_cache()

        for i in range(len(training_data)):
            tensor = torch.tensor(training_data.iloc[i].values)
            if mode == 2:
                tensor = tensor.to(device)  # CUDA CODE
            OriginalImageTensor = getOriginalImage(SR_file_number.iloc[i])  # tensor of the original image
            # skip if empty image
            if OriginalImageTensor == [0, 0, 0]:
                print("I ran")
                continue

            # get the dimensions of the original image
            # OriginalImageheight = OriginalImageTensor.shape[0]
            # OriginalImagewidth = OriginalImageTensor.shape[1]
            OriginalImageTensor = OriginalImageTensor.unsqueeze(0)

            if mode == 2:
                OriginalImageTensor = OriginalImageTensor.to(device)  # CUDA CODE

            # produce tensor of neural network image using previous dimensions
            ProducedImageTensor = class_instance(tensor.float(), 120, 160)  # tensor of the produced image
            if mode == 2:
                ProducedImageTensor = ProducedImageTensor.to(device)  # CUDA CODE

            # loss functions
            optimizer.zero_grad()
            loss = loss_function(ProducedImageTensor, OriginalImageTensor)
            total_training_loss += loss
            loss.backward()
            optimizer.step()  # optimizer
            if(i == 0):
                display_produced_image = ProducedImageTensor
                display_original_image = OriginalImageTensor
                print("I ran2")


        if (epoch % 10 == 0):
            total_training_loss = total_training_loss.cpu().detach().numpy()
            average_training_loss = (total_training_loss / len(training_data))
            training_loss_arr.append(average_training_loss)
            for i in range(len(testing_data)):
                location = SR_file_number.iloc[len(training_data)+i]
                OriginalImage_TestData = getOriginalImage(location)
                if OriginalImage_TestData == [0,0,0]:
                    continue

                OriginalImage_TestData = OriginalImage_TestData.unsqueeze(0)
                if mode == 2:
                    OriginalImage_TestData = OriginalImage_TestData.to(device) #CUDA CODE

                test_tensor = torch.tensor(testing_data.iloc[i].values)
                if mode == 2:
                    test_tensor = test_tensor.to(device) #CUDA CODE
                ProducedImage_TestData = class_instance(test_tensor.float(),120,160)
                if mode == 2:
                    ProducedImage_TestData = ProducedImage_TestData.to(device) #CUDA CODE

                validation_loss  = loss_function(ProducedImage_TestData,OriginalImage_TestData)
                total_validation_loss = total_validation_loss + validation_loss

            total_validation_loss = total_validation_loss.cpu().detach().numpy()
            validation_loss_arr.append(total_validation_loss/len(testing_data))

        # print comparisons
        update_progress_bar(progress_bar,epoch,epoch_num)
        get_image(display_produced_image,display_original_image)
        refresh_image(preview_image,original_image_widget)
        update_loss_bar(loss,(total_training_loss / len(training_data)),epoch_loss_widget,total_loss_widget)
        print("Epoch number:" + str(epoch + 1))
        print("Current epoch loss : {}".format(loss))
        print("Total training loss : {}\n".format(total_training_loss / len(training_data)))
        total_training_loss = 0
        total_validation_loss = 0

    print("Training completed")

    print(validation_loss_arr)
    print(training_loss_arr)
    global x
    x = list(range(0, epoch_num, 10))
    print(x)


def get_graph():
    return x,training_loss_arr,validation_loss_arr
# Saves the current neural network model
def save_model(model_name):
    torch.save(model.state_dict(), model_name)
    print('Model saved as {}'.format(model_name))


# Loads a trained neural network model
def load_model(data, model_name):
    # print(data)
    model = Net()
    model.load_state_dict(torch.load(model_name))
    # model.eval()
    ProducedImageTensor = model(data.float(), 120, 160)
    ProducedImageTensor = ProducedImageTensor.squeeze(0)
    # save_image_from_tensor(ProducedImageTensor)
    return ProducedImageTensor


# Neural Network
class Net(nn.Module):

    # Below are the layers applied during training
    def __init__(self):
        super(Net, self).__init__()
        self.fc1 = nn.Linear(11, 2048)
        self.batchnorm1 = nn.BatchNorm2d(3)
        self.relu = nn.ReLU()
        self.dropout1 = nn.Dropout(0.25)
        self.batchnorm2 = nn.BatchNorm2d(3)

        self.dropout2 = nn.Dropout2d(0.25)

        self.fc2 = nn.Linear(2048, 9600)

        self.Convolution1 = nn.Conv2d(36,3, (3, 3), padding=1)
        self.dropout3 = nn.Dropout2d(0.25)
        self.batchnorm3 = nn.BatchNorm2d(3)
        self.Convolution2 = nn.Conv2d(3, 3, (3, 3), padding=1)
        self.Convolution3 = nn.Conv2d(3, 3, (3, 3), padding=1)
        self.Convolution4 = nn.Conv2d(3, 3, (3, 3), padding=1)

    # x represents our data
    def forward(self, x, originalimageheight, originalimagewidth):
        torch.set_printoptions(threshold=10_000)

        out = self.fc1(x)
        leakRelu = nn.LeakyReLU(0.1)
        out = leakRelu(out)
        # out = self.dropout1(out)
        out = self.fc2(out)

        test_shape = torch.reshape(out, (12, 20, 40))  # Formula : input_size = channels * sqr_root(dimension)

        # changes the shape of the data
        test_shape = F.interpolate(test_shape, originalimagewidth, mode='linear', align_corners=True)
        test_shape = test_shape.permute(0, 2, 1)
        test_shape = F.interpolate(test_shape, originalimageheight, mode='linear', align_corners=True)
        test_shape = test_shape.permute(2, 1, 0)
        test_shape = F.interpolate(test_shape, 36)
        test_shape = test_shape.permute(2, 1, 0)
        test_shape = test_shape.permute(0, 2, 1)

        test_shape = test_shape.unsqueeze(0)

        # 1st Convolutional Layer
        test_shape = self.Convolution1(test_shape)
        test_shape = self.batchnorm1(test_shape)
        leakRelu = nn.LeakyReLU(0.1)
        test_shape = leakRelu(test_shape)
        # test_shape=self.dropout3(test_shape)

        # 2nd Convolutional Layer
        test_shape = self.Convolution2(test_shape)
        test_shape = self.batchnorm2(test_shape)
        leakRelu = nn.LeakyReLU(0.1)
        test_shape = leakRelu(test_shape)
        # test_shape=self.dropout3(test_shape)

        # Last Convolutional Layer
        test_shape = self.Convolution3(test_shape)
        test_shape = self.batchnorm3(test_shape)
        leakRelu = nn.LeakyReLU(0.1)
        test_shape = leakRelu(test_shape)

        # last layer
        test_shape = self.Convolution4(test_shape)
        m = nn.MaxPool2d(3, stride=1, padding=1)
        test_shape = m(test_shape)
        # test_shape=leakRelu(test_shape)
        test_shape = test_shape.swapaxes(1, 2)  # reverse order to 'width, height, channels'
        test_shape = test_shape.swapaxes(2, 3)
        return test_shape


# Saves a single tensor as an image to file
def save_image_from_tensor(image_tensor, image_size=500):
    # swap tensor axes so 'channels' is first
    image_tensor = image_tensor.swapaxes(2, 1)
    image_tensor = image_tensor.swapaxes(1, 0)

    # resize imagez
    transform = transforms.Compose([
        transforms.ToPILImage(),
        transforms.Resize(size=500),
        transforms.ToTensor()
    ])
    image_tensor = transform(image_tensor)

    # name of the saved file
    file_name = 'test.png'

    # save image
    save_image(image_tensor, file_name)


# Evaluates the neural network based on test dataset
def performance_evaluation(test_data, training_data_count, model_name):
    original_images = []
    predicted_images = []

    for i in range(len(test_data)):

        OriginalImageTensor = getOriginalImage(
            SR_file_number.iloc[training_data_count + i])  # tensor of the original test image
        if OriginalImageTensor == [0, 0, 0]:
            continue

        OriginalImageTensor = OriginalImageTensor.squeeze(0)
        OriginalImageTensor = OriginalImageTensor.cpu().detach().numpy()
        original_images.append(OriginalImageTensor)

        test_tensor = torch.tensor(test_data.iloc[i].values)
        predicted_images.append((load_model(test_tensor, model_name)).cpu().detach().numpy())

    # Code for shape tests
    origianal_img_shape_test = np.array(original_images)
    predicted_img_shape_test = np.array(predicted_images)
    print("Original image array: {}".format(origianal_img_shape_test.shape))
    print("Predicted image array: {}".format(predicted_img_shape_test.shape))

    # mean squared error formula
    MSE = np.square(np.subtract(original_images, predicted_images)).mean()

    print("Mean Squared Error for model '{}' : {}".format(model_name, MSE))

    main()


# Message to display train or evaluate options
def menu_msg():
    print("\n------Console Menu------")
    print("1.Train")
    print("2.Performance Evaluation")
    print("3.Exit")
    choice = int(input(""))
    return choice


def main(excel_path, original_image_path, epoch_num, mode, training_ratio, learning_rate, momentum,preview_image,original_image_widget,progress_bar,epoch_loss_widget,total_loss_widget):
    global SR_file_number
    data, SR_file_number = extract.main(
        excel_path)  # data and final dataframe(pandas format) obtained from extract_data function
    global original_image
    original_image = original_image_path

    normalized_data = create_dataset(data)

    training_data, test_data = split_dataset(normalized_data, training_ratio)

    if (mode == "CPU"):
        mode_int = 1

    else:
        mode_int = 2
    training(training_data, test_data, epoch_num, mode_int, learning_rate, momentum,preview_image,original_image_widget,progress_bar,epoch_loss_widget,total_loss_widget)


'''
    choice = menu_msg()

    if choice == 1:
        print(">>>Training\n")
        epoch_num = int(input("Please insert the number of epochs to train the model with: "))
        model_name = input("Please set the name of the model: ")
        mode = int(input("Will you be training on CPU or GPU ?\n1.CPU\n2.GPU (CUDA)\n"))
        training(training_data,test_data, epoch_num, model_name, mode)

    elif choice == 2:
        print(">>>Evaluating Performance\n")
        model_name = input("Please state the name of the model you wish to load: ")
        training_data_count = len(training_data)
        performance_evaluation(test_data, training_data_count, model_name)

    elif choice == 3:
        print(">>>Terminating console...")
        return

    else:
        print(">>>Unrecognized command\n")
        main()




------------------ Unused Code Area ------------------

        #Individual Shape Viewing Commands

        #ProducedImagenumpy = ProducedImageTensor.detach().numpy()
        #OriginalImagenumpy = OriginalImageTensor.detach().numpy()
        #print(OriginalImageTensor.shape)
        #print(ProducedImageTensor.shape)

        #Display Image commands
        #plt.imshow(test_shape[0])
        #plt.show()


#Returns a list of tensors from BMT images located in current directory (and sub-dirs)
def get_original_image_tensors():
    original_image_tensors = []

    images_dir = "**"
    images_list = glob(os.path.join(images_dir, "*.BMT"))


    for img_filename in images_list:
        img_path = os.path.join(images_dir, img_filename)
        original_image_tensors.append(getOriginalImage(img_filename))

    return original_image_tensors


#Converts a single image into a tensor
def getOriginalImage(image_name):
    img = Image.open(image_name)
    convert_tensor = transforms.ToTensor()
    OriginalImageTensor = convert_tensor(img)
    OriginalImageTensor = OriginalImageTensor.permute(1, 2, 0)

    return OriginalImageTensor

#CUDA CODE
# setting device on GPU if available, else CPU
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        print('Using device:', device)
        print()

#Additional Info when using cuda
if device.type == 'cuda':
    print(torch.cuda.get_device_name(0))
    print('Memory Usage:')
    print('Allocated:', round(torch.cuda.memory_allocated(0)/1024**3,1), 'GB')
    print('Cached:   ', round(torch.cuda.memory_reserved(0)/1024**3,1), 'GB\n\n')
'''
