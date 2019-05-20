
import tensorflow as tf
import numpy as np
import os
#from convolutional import Conv3D
from numpy import genfromtxt
from keras import backend as K
from keras.layers import Conv2D, ZeroPadding2D, Activation, Input, concatenate, ZeroPadding3D#, Conv3D 
#from keras.layers import AtrousConvolution2D, AtrousCo
from keras.layers import Conv3D, Concatenate
from keras.layers import LeakyReLU, Deconvolution2D, Deconvolution3D
from keras.layers.normalization import BatchNormalization
from keras.layers.pooling import MaxPooling2D, AveragePooling2D, MaxPooling3D, AveragePooling3D
from keras.layers import UpSampling2D, UpSampling3D
from keras.models import Model
from keras.layers.core import Lambda, Flatten, Dense
import math
from keras.layers import Conv2DTranspose, Conv3DTranspose, Reshape
from keras.optimizers import adam
from DataWeight_load import *


def CN3D(video_info=None , input_video = None, sampling_frame= 8,  vid_net_mid_depth = 3):
    Activ = lambda x: LeakyReLU(alpha=0.2)(x)
    Bat = lambda x: BatchNormalization()(x)
    #Activ = LeakyReLU(alpha=0.2)
    #Bat = BatchNormalization()
    video_size = None

    if not video_size:
        W = 160
        H = 120
    else:
        W = video_info[0]
        H = video_info[1]
        
    #W = int(W/2)
    #H = int(H/2)

    if input_video is None:
        input_video = Input( shape=(sampling_frame, W, H, 3) )

    #print(input_video.get_shape())
    e0 = Conv3D(filters=32,padding='same', kernel_size=(5,5,5))(input_video)
    e0 = Bat(e0)
    e0 = Activ(e0)
    #print(e0.get_shape())
    #WITH NO CONCATENATE Init_dataloader()DING IN 3DCN BUT WITH CONCAT FOR ENCODING IN combination part

    e0_C = Conv3D(filters= 64,  padding='same', kernel_size=(3,3,3), strides =2)(e0)
    e0_C = Bat(e0_C)
    e0_C = Activ(e0_C)
    #print(e0_C.get_shape())

    e1 = Conv3D(filters=128,padding='same', kernel_size=(3,3,3))(e0_C)
    e1 = Bat(e1)
    e1 = Activ(e1)
    #print(e1.get_shape())

    e1_C = Conv3D(filters=256, padding='same', kernel_size=3, strides = 2)(e1)
    e1_C = Bat(e1_C)
    e1_C = Activ(e1_C)
    #print(e1_C.get_shape())

    e2 = Conv3D(filters=512,padding='same', kernel_size=(3,3,3))(e1_C)
    e2 = Bat(e2)
    e2 = Activ(e2)
    #print(e2.get_shape())
    '''
    e2_C = Conv3D(filters=512, padding='same', kernel_size=3, strides = 2)(e2)
    e2_C = Bat(e2_C)
    e2_C = Activ(e2_C)
    print(e2_C.get_shape())
    fc_mid = e2_C
    '''
    fc_mid = e2
    p_num = 2
    
    for i in range(vid_net_mid_depth):
        fc_mid = Conv3D(filters= 512, dilation_rate= p_num, kernel_size = 3, padding='same')(fc_mid)
        fc_mid = Bat(fc_mid)
        fc_mid = Activ(fc_mid)
        #print(fc_mid.get_shape())
        p_num = p_num * 2

    '''
    #fc_mid = Deconvolution3D(strides=2, filters=64, kernel_size= 4, padding='same')(fc_mid)
    d0_C = Concatenate()([fc_mid, e2_C])    
    d0_C = UpSampling3D()(d0_C)
    d0_C = Conv3D(strides=1, filters=256, kernel_size= 4, padding='same')(d0_C)
    d0_C = Bat(d0_C)
    d0_C = Activ(d0_C)
    print(d0_C.get_shape())
    
    d0_CC = Concatenate()([d0_C, e2])    
    '''
    d0_CC = Concatenate()([fc_mid, e2])    
    d0_CC = Conv3D(filters=256,padding='same', kernel_size=3)(d0_CC)
    d0_CC = Bat(d0_CC)
    d0_CC = Activ(d0_CC)
    #print(d0_CC.get_shape())

    d1 = Concatenate()([d0_CC, e1_C])
    d1 = UpSampling3D()(d1)
    d1 = Conv3D(strides=1, filters=128, kernel_size= 4, padding='same')(d1)
    d1 = Bat(d1)
    d1 = Activ(d1)
    #print(d1.get_shape())

    d1_C = Concatenate()([d1, e1])    
    d1_C = Conv3D(filters=64,padding='same', kernel_size=3)(d1_C)
    d1_C = Bat(d1_C)
    d1_C = Activ(d1_C)
    #print(d1_C.get_shape())

    d1_CC = Concatenate()([d1_C, e0_C])
    #d1_CC = Deconvolution3D(strides=2, filters=16, kernel_size= 4, padding='same')(d1_CC)
    d1_CC = UpSampling3D()(d1_CC)
    d1_CC = Conv3D(strides=1, filters=32, kernel_size= 4, padding='same')(d1_CC)
    d1_CC = Bat(d1_CC)
    d1_CC = Activ(d1_CC)
    #print(d1_CC.get_shape())

    d2_CC = Concatenate()([d1_CC, e0])
    d2_CC = Conv3D(filters=3, padding='same', kernel_size=3)(d2_CC)
    d2_CC = Bat(d2_CC)
    d2_CC = Activation('tanh')(d2_CC)
    #print(d2_CC.get_shape())
    video_3DCN = d2_CC
    #video_3DCN = Model(input_video, d2_CC)

    return video_3DCN


def CombCN(video_size=None, sampling_frame=8, frame_net_mid_depth = 4):
    #frame_3DCN => total frames or jsut frame of Vk in Vin 
    Activ = lambda x: LeakyReLU(alpha=0.2)(x)
    Bat = lambda x: BatchNormalization()(x)
    #Activ = LeakyReLU(alpha=0.2)
    #Bat = BatchNormalization()
    video_size = None

    if not video_size:
        W = 320
        H = 240
    else:
        W = video_size[0]
        H = video_size[1]
        
    #W = int(W/2)
    #H = int(H/2)

    input_frame = Input( shape=(W, H, 3) )
    input_video = Input( shape=(sampling_frame, W/2, H/2, 3) )
    print(input_frame.get_shape())

    e0 = Conv2D(filters=16,padding='same', kernel_size=(5,5))(input_frame)
    e0 = Bat(e0)
    e0 = Activ(e0)
    print(e0.get_shape())
    #WITH NO CONCATENATE Init_dataloader()DING IN 3DCN BUT WITH CONCAT FOR ENCODING IN combination part

    e0_C = Conv2D(filters= 32,  padding='same', kernel_size=(4,4), strides = 2)(e0)
    e0_C = Bat(e0_C)
    e0_C = Activ(e0_C)
    print(e0_C.get_shape())

    skip_subnet = CN3D(video_info=None , input_video = input_video, sampling_frame= 8,  vid_net_mid_depth = 3)
    size_subnet = skip_subnet.get_shape()

    skip_subnet = Reshape( (int(W/2), int(H/2), int(size_subnet[1]* size_subnet[4]) ) )(skip_subnet)
    skip_subnet = Conv2D(filters= 32,  padding='same', kernel_size=(4,4), strides = 1)(skip_subnet)
    skip_subnet = Bat(skip_subnet)
    skip_subnet = Activ(skip_subnet)
    print("#######")
    print("subnet")
    print(skip_subnet.get_shape())
    print("#######")

    e0_C = Concatenate()([e0_C, skip_subnet])
    print(e0_C.get_shape())

    e1 = Conv2D(filters=128,padding='same', kernel_size=(3,3))(e0_C)
    e1 = Bat(e1)
    e1 = Activ(e1)
    print(e1.get_shape())

    e1_C = Conv2D(filters=256, padding='same', kernel_size=3, strides = 2)(e1)
    e1_C = Bat(e1_C)
    e1_C = Activ(e1_C)
    print(e1_C.get_shape())

    e2 = Conv2D(filters=512,padding='same', kernel_size=(3,3))(e1_C)
    e2 = Bat(e2)
    e2 = Activ(e2)
    print(e2.get_shape())
    
    e2_C = Conv2D(filters=512, padding='same', kernel_size=3, strides = 2)(e2)
    e2_C = Bat(e2_C)
    e2_C = Activ(e2_C)
    print(e2_C.get_shape())

    fc_mid = e2_C
    p_num = 2
    
    for i in range(frame_net_mid_depth):
        fc_mid = Conv2D(filters= 512, dilation_rate= p_num, kernel_size = 3, padding='same')(fc_mid)
        fc_mid = Bat(fc_mid)
        fc_mid = Activ(fc_mid)
        print(fc_mid.get_shape())
        p_num = p_num * 2

    #fc_mid = Deconvolution3D(strides=2, filters=64, kernel_size= 4, padding='same')(fc_mid)
    d0 = Concatenate()([fc_mid, e2_C])    
    print(d0.get_shape())

    d0_C = UpSampling2D()(d0)
    d0_C = Conv2D(strides=1, filters=512, kernel_size= 4, padding='same')(d0_C)
    d0_C = Bat(d0_C)
    d0_C = Activ(d0_C)
    d0_C = Concatenate()([d0_C, e2])    
    print(d0_C.get_shape())

    d0_CC = Conv2D(filters=256,padding='same', kernel_size=3)(d0_C)
    d0_CC = Bat(d0_CC)
    d0_CC = Activ(d0_CC)
    d0_CC = Concatenate()([d0_CC, e1_C])
    print(d0_CC.get_shape())

    d1 = UpSampling2D()(d0_CC)
    d1 = Conv2D(strides=1, filters=128, kernel_size= 4, padding='same')(d1)
    d1 = Bat(d1)
    d1 = Activ(d1)
    d1 = Concatenate()([d1, e1])    
    print(d1.get_shape())

    d1_C = Conv2D(filters=64,padding='same', kernel_size=3)(d1)
    d1_C = Bat(d1_C)
    d1_C = Activ(d1_C)
    d1_C = Concatenate()([d1_C, e0_C])
    print(d1_C.get_shape())

    d1_C = Conv2D(filters=32,padding='same', kernel_size=3)(d1_C)
    d1_C = Bat(d1_C)
    d1_C = Activ(d1_C)
    d1_C = Concatenate()([d1_C, skip_subnet])    
    print(d1_C.get_shape())
    
    d1_CC = UpSampling2D()(d1_C)
    d1_CC = Conv2D(strides=1, filters=16, kernel_size= 4, padding='same')(d1_CC)
    d1_CC = Bat(d1_CC)
    d1_CC = Activ(d1_CC)
    d1_CC = Concatenate()([d1_CC, e0])
    print(d1_CC.get_shape())

    d2_CC = Conv2D(filters=3, padding='same', kernel_size=3)(d1_CC)
    d2_CC = Bat(d2_CC)
    d2_CC = Activation('tanh')(d2_CC)
    print(d2_CC.get_shape())

    image_Comb3DCN = Model([input_frame, input_video], d2_CC)
    
    return image_Comb3DCN

def network_generate(data_shape= None, sampling_frame=8, vid_net_mid_depth=3, frame_net_mid_depth=4):
    # loss_f = loss of 3DNN + loss of CombCN
    # loss_CombCN = Sig( M * G(V,M,I) - V )....
    # final_model => sig ( CN3D  => combCN)
    Init_dataloader()

    loss = None
    optimizer = None
    final_model =None
    
    combCN_model = CombCN()
    combCN_model.summary()
    #CN3D_model = CN3D() # CN3D_MODEL IS NOT REAL FINAL// JUST FOR TEST
    #final_model = CN3D()
    #final_model.summary()
    final_model = combCN_model     
    final_model.compile(optimizer=optimizer, loss= loss )
    return final_model

 ## to check shapes of models to train
if __name__ == "__main__":
    network_generate()
    
    