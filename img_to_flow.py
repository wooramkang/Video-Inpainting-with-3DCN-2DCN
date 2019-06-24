#from __future__ import absolute_import, division, print_function
import os
import sys
import numpy as np
sys.path.append(os.path.dirname(__file__) )
sys.path.append(os.path.dirname(__file__)+ '/opticalflow/' )

from copy import deepcopy
import cv2

from opticalflow.model_pwcnet import ModelPWCNet, _DEFAULT_PWCNET_TEST_OPTIONS
from opticalflow.visualize import display_img_pairs_w_flows
from opticalflow.optflow import flow_to_img
from DataWeight_load import *

# Build a list of image pairs to process

def img_to_optflow(frame_stream, batchsize, target_hei =400, target_wid = 400, direction=True, with_resizing = True):
    
    img_pairs = []
    t_frames = []

    for i in range(batchsize):
        t_frames.append( cv2.resize(frame_stream[i], (1024, 436) ) )
    frame_stream = np.array(t_frames)

    #cv2.imshow("for_checking", frame_stream[1])
    #cv2.waitKey(3000)

    if direction:
        for i in range(batchsize-1):
            img_pairs.append( (frame_stream[i], frame_stream[i+1]) )
    else:
        for i in range(batchsize-1):
            img_pairs.append( (frame_stream[ batchsize - (i+1) ], frame_stream[ batchsize - (i+2) ]) )

    #cv2.imshow("for_checking_1", img_pairs[1][0])
    #cv2.waitKey(3000)

    gpu_devices = ['/device:GPU:0']  
    controller = '/device:GPU:0'

    ckpt_path = 'opticalflow/pwcnet-lg-6-2-multisteps-chairsthingsmix/pwcnet.ckpt-595000'

    nn_opts = deepcopy(_DEFAULT_PWCNET_TEST_OPTIONS)
    nn_opts['verbose'] = True
    nn_opts['ckpt_path'] = ckpt_path
    nn_opts['batch_size'] = 1
    nn_opts['gpu_devices'] = gpu_devices
    nn_opts['controller'] = controller
    nn_opts['use_dense_cx'] = True
    nn_opts['use_res_cx'] = True
    nn_opts['pyr_lvls'] = 6
    nn_opts['flow_pred_lvl'] = 2

    nn_opts['adapt_info'] = (1, 436,1024, 2)

    nn = ModelPWCNet(mode='test', options=nn_opts)
    #nn.print_config()
    
    pred_labels = nn.predict_from_img_pairs(img_pairs, batch_size=1, verbose=False)
    
    width = target_wid
    height = target_hei
    
    if with_resizing:
        resize_ori_images = []    

        for p in frame_stream:
            resize_ori_images.append(cv2.resize(p, (width, height) ))
        
        resize_optflow = []
        
        # need to check diff between auto_resize & manual's
        
        opt_h = p.shape[0]
        opt_w = p.shape[1]
        
        #print( (height, width) )
        for p in pred_labels:
            resize_image = np.zeros(shape=(height, width, 2))

            for H in range(height):
                n_hei = int( H * opt_h/height )
                for W in range(width):
                    n_wid = int( W * opt_w/width )
            
                    resize_image[H][W] = p[n_hei][n_wid]

            resize_optflow.append(resize_image)
        
        resize_optflow = flow_resize(pred_labels, (height, width)  )
        resize_ori_images = np.array(resize_ori_images)
        resize_optflow = np.array(resize_optflow)        

        #display_img_pairs_w_flows(img_pairs, pred_labels)

    else:
        resize_ori_images = frame_stream
        resize_optflow = pred_labels

    return resize_ori_images, resize_optflow

#for test of optflow estim
if __name__ == "__main__":
    frames = []
    frames.append(cv2.imread("mpisintel_test_clean_ambush_1_frame_0001.png"))
    frames.append(cv2.imread("mpisintel_test_clean_ambush_1_frame_0002.png"))
    frames = np.array(frames)
    ori, opt = img_to_optflow(frames, 2,  target_hei =400, target_wid = 1000, direction = False)
