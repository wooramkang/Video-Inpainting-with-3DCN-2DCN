import os
import glob
import numpy as np
from numpy import genfromtxt
import PIL
import keras
from keras.models import Model
import os
from random import randint, seed
import itertools
import numpy as np
import cv2
from copy import deepcopy

global default_dir
global image_dir
global video_dir
global shape 
#2019. 05 .16 video to images & only image stream loader // wooramkang

def Set_video_dir(t_str):
    global video_dir
    video_dir= t_str
def Set_image_dir(t_str):
    global image_dir
    image_dir= t_str
def Set_shape(size):
    global shape
    shape = size
    
def Init_dataloader(data_dir=None):
    global default_dir
    global image_dir
    global video_dir
    global shape

    if data_dir == None:
        default_dir = "/TEST_MODEL/UCF-101-image/"
    else:
        default_dir = data_dir

    Set_video_dir(default_dir)
    Set_image_dir(default_dir)
    shape = None

def Img_loader():
    ###UCF-101
    ###use image stream not video type
    '''
        2019. 05 .16 video to images & only image stream loader // wooramkang
        dataset UCF-101 - >x_data  hash structure tree i made

        x_data[1]          ["path"][1]  [2]  [3]
              [start from 0]
        x_data[scene_order]
              [random name order of scene]
        x_data[scene_order]["name"]
        x_data[scene_order]["path"]
                                   [1]
                                   [g01 = longcut01]
                                   [start from 1]
                                        [1]
                                        [c01 = cut01]
                                        [start from 1]
                                             [0] = "/ho...."
                                             [random order of image]
                                             [start from 0]
    '''
    x_data = []
    global image_dir

    folders_root = os.listdir(image_dir)

    for name in folders_root:
        #ex) ApplyEyeMakeup
        count=0
        folders_son = os.listdir(image_dir+name)

        images = dict()
        images["name"] = name    
        images["path"] = dict()

        past_g = ""
        past_c = ""

        check_change= False

        for name_son in folders_son:
            
            folder_property = name_son.split('_')
            temp_len = len(folder_property) - 1
            now_g = folder_property[temp_len-1]
            now_c = folder_property[temp_len]
            
            if past_g != now_g :
                check_change = True
            
            if past_c != now_c :
                check_change = True
            
            if check_change:
                
                if not int( now_g[1:3] ) in images["path"]:
                    images["path"][ int( now_g[1:3] ) ] = dict()

                past_g = now_g
                past_c = now_c
                check_change= False
            
            images["path"][ int( now_g[1:3] ) ][ int(now_c[1:3]) ] = []
            
            for file in glob.glob(image_dir + name + "/" + name_son + "/*"):
                #ex) ApplyEyeMakeup_G01_C01
                count= count+1

                identity = str(file).split('.')
                if identity[len(identity)-1] != 'jpg':
                    continue

                images["path"][ int( now_g[1:3] ) ][ int(now_c[1:3]) ].append(file)
                
        x_data.append(images)

    #print(len(x_data))    
    #print(x_data[0]["name"])
    #print(len(x_data[1]["path"]))
    #print(len(x_data[1]["path"][1] ))
    #print(len(x_data[1]["path"][1][1] ))
    #print(x_data[1]["path"][1][2][1] )
    
    '''
        2019. 05 .16 video to images & only image stream loader // wooramkang
        dataset UCF-101 - >x_data  hash structure tree i made

        x_data[1]          ["path"][1]  [2]  [3]
              [start from 0]
        x_data[scene_order]
              [random name order of scene]
        x_data[scene_order]["name"]
        x_data[scene_order]["path"]
                                   [1]
                                   [g01 = longcut01]
                                   [start from 1]
                                        [1]
                                        [c01 = cut01]
                                        [start from 1]
                                             [0] = "/ho...."
                                             [random order of image]
                                             [start from 0]
    '''
    
    img = Image_read(x_data[1]["path"][1][2][0])
    Set_shape( img.shape )

    return x_data

###### ON GOING 

def flow_loader(flow_dir=None, ):
    flows = []
    
    folders_root = os.listdir(flow_dir)
    for name in folders_root:
        folders_son = os.listdir(image_dir+name)

        flow = dict()
        flow["name"] = name    
        flow["path"] = dict()

        for name_son in folders_son:        
            folder_property = name_son.split('_')
    
            for file in glob.glob(image_dir + name + "/" + name_son + "/*"):
                #LOAD IMG i,  IMG i+1,  FLOW(file)
                print("XXX")

        flows.append(flow)

    return flows


def Data_split(x_data, train_test_ratio = 0.7):
    #params
    #to split data to train and validate OR to train and test
    
    x_train = []
    x_test = []
    
    data_len = len(x_data)
    train_len = int(data_len * train_test_ratio)

    train_list = range(train_len)
    test_list = range(train_len, data_len)

    for i in train_list:
        x_train.append(x_data[i])
        
    for i in test_list:
        x_test.append(x_data[i])
        
    return np.array(x_train), np.array(x_test)

def data_batch_loader_forward(data_batch, size = None):
    while True:
        for scene in range(len(data_batch)):
            for longcut in data_batch[scene]["path"]:
                for cut in data_batch[scene]["path"][longcut]:
                    data_batch[scene]["path"][longcut][cut].sort()
                    #feed frames of video from forward
                    for image_path in data_batch[scene]["path"][longcut][cut]:
                        #to check working properly
                        #print(image_path)
                        if size == None:
                            yield Image_read(image_path), cut
                        else:
                            img = cv2.resize(cv2.imread(image_path), size)
                            img = np.transpose(img, (1, 0, 2))
                            yield img, cut

def data_batch_loader_backward(data_batch, size = None):
    while True:
        for scene in range(len(data_batch)):
            for longcut in data_batch[scene]["path"]:
                for cut in data_batch[scene]["path"][longcut]:
                    data_batch[scene]["path"][longcut][cut].sort()
                    #feed frames of video from backward
                    for image_path in reversed(data_batch[scene]["path"][longcut][cut]):
                        #to check working properly
                        #print(image_path)
                        if size == None:
                                yield Image_read(image_path), cut
                        else:
                            img = cv2.resize(cv2.imread(image_path), size)
                            img = np.transpose(img, (1, 0, 2))
                            yield img, cut

def Random_sampling_data(SAMPLE_BATCH_SIZE, data_batch_loader_forward):
    
    sample_frames_batch = []
    sample_img_batch = []

    for i in range(SAMPLE_BATCH_SIZE):
        rand_idx = randint(0, 100)
        sample_frames = []

        for step in range(rand_idx):
            next(data_batch_loader_forward)
        
        for step in range(SAMPLE_BATCH_SIZE):
            sample_frames.append( next(data_batch_loader_forward))

        sample_img_batch.append(sample_frames[-1])
        sample_frames_batch.append(sample_frames)

    return np.array(sample_img_batch), np.array(sample_frames_batch)

def iter_to_one_batch(iter, batch_size, with_normalizing=True):
    data_batch = []
    temp = None
    __checker = None
    count = 0 

    for i in range(batch_size):
        bef_checker = __checker
        temp, __checker = next(iter)
        
        if (bef_checker != __checker) and ( i != 0 ):
            for i in range(batch_size - (count)):
                data_batch.append( data_batch[len(data_batch)-1] )
            return np.array(data_batch)            

        count = i + 1
        if with_normalizing:
            data_batch.append( image_normalization(temp) )
        else:
            data_batch.append( temp )

    return np.array(data_batch)

def mask_to_one_batch(mask_loader, batch_size):
    mask_batch = []

    for i in range(batch_size):
        mask_batch.append(mask_loader._generate_mask() )

    return mask_batch

def Image_read(file_path):
    img = cv2.imread(file_path)
    '''
    img = cv2.resize(img,(128,128))
    #IN A LOT OF PAPER,
    #RESIZE 128 * 128
    #channel first
    #img = np.transpose(img, (2, 0, 1))
    '''
    img = np.transpose(img, (1, 0, 2))
    #print(img.shape)
    return img

def Get_image_shape():
    global shape 
    return shape

def image_normalization(image_batch):
    image_batch = image_batch - 127.5
    image_batch = np.divide(image_batch, 127.5)
    return image_batch

def image_to_origin(image_batch):
    image_batch = np.multiply(image_batch, 127.5)
    image_batch = image_batch + 127.5
    #image_batch = np.transpose(image_batch, (0, 3, 1, 2))
    return image_batch

def mask_normalization(image_batch):
    image_batch = image_batch / 255 #np.divide(image_batch, 255)
    return image_batch

def mask_to_origin(image_batch):
    image_batch = image_batch * 255 #np.multiply(image_batch, 255)
    return image_batch

def flow_resize(mask_batch, target_size):
    
    #mask_batch = 
    mask_size = (mask_batch[0].shape[0] , mask_batch[0].shape[1] )
    #print(mask_size)
    target_batch = []

    if mask_size == target_size:
        return mask_batch

    for i in range( len(mask_batch) ):
        mask = np.zeros( (mask_size[0], mask_size[1], 3)) #, dtype=np.uint8 )
        target_mask = np.zeros( (target_size[1], target_size[0], 2 ))#, dtype=np.uint8 )
        
        for h in range( mask_size[0] ):
            for w in range( mask_size[1] ):
                mask[h][w][0] = mask_batch[i][h][w][0]
                mask[h][w][1] = mask_batch[i][h][w][1]
                mask[h][w][2] = mask_batch[i][h][w][1]

        mask = cv2.resize( mask , (target_size[0], target_size[1])  )
        
        #print(mask.shape)
        #print(target_mask.shape)
        for h in range( target_size[1] ):
            for w in range( target_size[0] ):
                target_mask[h][w][0] = mask[h][w][0]
                target_mask[h][w][1] = mask[h][w][1]
        
        target_batch.append(target_mask)

    return np.array(target_batch)

def mask_resize(mask_batch, target_size):
    
    #mask_batch = 
    mask_size = (mask_batch[0].shape[0] , mask_batch[0].shape[1] )
    #print(mask_size)

    target_batch = []
    
    if mask_size == target_size:
        return mask_batch

    for i in range( len(mask_batch) ):
        mask = np.zeros( (mask_size[0], mask_size[1], 3), dtype=np.uint8 )
        target_mask = np.zeros( (mask_size[0], mask_size[1], 3), dtype=np.uint8 )
        
        for h in range( mask_size[0] ):
            for w in range( mask_size[1] ):
                if mask_batch[i][h][w][0] != 0:
                    mask[h][w][0] = 1

                if mask_batch[i][h][w][1] != 0:
                    mask[h][w][1] = 1

                if mask_batch[i][h][w][2] != 0:
                    mask[h][w][2] = 1

        temp_mask = deepcopy(cv2.resize( mask , target_size))
        
        for h in range( target_size[0] ):
            for w in range( target_size[1] ):
                if temp_mask[h][w][0] != 0:
                    target_mask[h][w][0] = 1

                if temp_mask[h][w][1] != 0:
                    target_mask[h][w][1] = 1

                if temp_mask[h][w][2] != 0:
                    target_mask[h][w][2] = 1

        target_batch.append(target_mask)

    return np.array(target_batch)

def image_to_half_size(image_batch):
    shape = image_batch[0].shape
    new_image_batch = []

    for image in image_batch:
        new_image_batch.append(  np.transpose(  cv2.resize(image, (int(shape[0]/2), int(shape[1]/2) ) ) , (1, 0, 2)))

    return np.array(new_image_batch)

def flow_to_image(prev_image = None, flow = None):
    covered_img = None


    return covered_img

def image_masking(image_batch, mask_batch):
    if len(image_batch) != len(mask_batch):
        return None
    
    masked_image_batch = []

    for i in range(len(image_batch)):
        masked_image = deepcopy(image_batch[i])
        masked_image[ mask_batch[i] == 0 ] = 255
        masked_image_batch.append(masked_image)
        
    return np.array(masked_image_batch)


class MaskGenerator():
# MaskGenerator from https://github.com/MathiasGruber/PConv-Keras/blob/master/libs/util.py
    def __init__(self, height, width, channels=3, rand_seed=None, filepath=None):    
        """Convenience functions for generating masks to be used for inpainting training
        
        Arguments:
            height {int} -- Mask height
            width {width} -- Mask width
        
        Keyword Arguments:
            channels {int} -- Channels to output (default: {3})
            rand_seed {[type]} -- Random seed (default: {None})
            filepath {[type]} -- Load masks from filepath. If None, generate masks with OpenCV (default: {None})
        """

        self.height = height
        self.width = width
        self.channels = channels
        self.filepath = filepath

        # If filepath supplied, load the list of masks within the directory
        self.mask_files = []
        if self.filepath:
            filenames = [f for f in os.listdir(self.filepath)]
            self.mask_files = [f for f in filenames if any(filetype in f.lower() for filetype in ['.jpeg', '.png', '.jpg'])]
            print(">> Found {} masks in {}".format(len(self.mask_files), self.filepath))        

        # Seed for reproducibility
        if rand_seed:
            seed(rand_seed)

    def _generate_mask(self):
        """Generates a random irregular mask with lines, circles and elipses"""

        img = np.zeros((self.height, self.width, self.channels), np.uint8)

        # Set size scale
        size = int((self.width + self.height) * 0.03)

        if int(size/2) < 2:
            size = 2
        else:
            size = int(size/2)

        if self.width < 64 or self.height < 64:
            raise Exception("Width and Height of mask must be at least 64!")
        
        # Draw random lines
        for _ in range(randint(1, 20)):
            x1, x2 = randint(1, self.width), randint(1, self.width)
            y1, y2 = randint(1, self.height), randint(1, self.height)
            thickness = randint(1, size)
            cv2.line(img,(x1,y1),(x2,y2),(1,1,1),thickness)
            
        # Draw random circles
        for _ in range(randint(1, 20)):
            x1, y1 = randint(1, self.width), randint(1, self.height)
            radius = randint(1, size)
            cv2.circle(img,(x1,y1),radius,(1,1,1), -1)
            
        # Draw random ellipses
        for _ in range(randint(1, 20)):
            x1, y1 = randint(1, self.width), randint(1, self.height)
            s1, s2 = randint(1, self.width), randint(1, self.height)
            a1, a2, a3 = randint(3, 180), randint(3, 180), randint(3, 180)
            thickness = randint(1, size)
            cv2.ellipse(img, (x1,y1), (s1,s2), a1, a2, a3,(1,1,1), thickness)
        
        return 1-img

    def _load_mask(self, rotation=True, dilation=True, cropping=True):
        """Loads a mask from disk, and optionally augments it"""

        # Read image
        mask = cv2.imread(os.path.join(self.filepath, np.random.choice(self.mask_files, 1, replace=False)[0]))
        
        # Random rotation
        if rotation:
            rand = np.random.randint(-180, 180)
            M = cv2.getRotationMatrix2D((mask.shape[1]/2, mask.shape[0]/2), rand, 1.5)
            mask = cv2.warpAffine(mask, M, (mask.shape[1], mask.shape[0]))
            
        # Random dilation
        if dilation:
            rand = np.random.randint(5, 47)
            kernel = np.ones((rand, rand), np.uint8) 
            mask = cv2.erode(mask, kernel, iterations=1)
            
        # Random cropping
        if cropping:
            x = np.random.randint(0, mask.shape[1] - self.width)
            y = np.random.randint(0, mask.shape[0] - self.height)
            mask = mask[y:y+self.height, x:x+self.width]

        return (mask > 1).astype(np.uint8)

    def sample(self, random_seed=None):
        """Retrieve a random mask"""
        if random_seed:
            seed(random_seed)
        if self.filepath and len(self.mask_files) > 0:
            return self._load_mask()
        else:
            return self._generate_mask()


def Weight_load(model, weights_path):
    model.load_weights(weights_path)
    return model

def Weight_save(model, weights_path):
    model.save_weights(weights_path)
    return True
'''
def get_video_shape(image_data):
    
    global shape
    shape =None

    return shape
def Video_loader(sampling_size = 30):
    video_list = None
    video_streams = None
    video_shape = None
    global video_dir

    return video_list, video_streams, video_shape
'''

#FOR DATALOADER TEST

if __name__ == "__main__":
    Init_dataloader()
    train_data = Img_loader()
    dataloader = data_batch_loader_forward(train_data)
    print(next(dataloader))
    print(next(dataloader))
    dataloader_back = data_batch_loader_backward(train_data)
    print(next(dataloader_back))
    print(next(dataloader_back))
    

    