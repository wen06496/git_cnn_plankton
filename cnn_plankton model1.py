import lasagne
import theano.tensor as T
import theano,scipy
from lasagne.nonlinearities import softmax,very_leaky_rectify,softplus,sigmoid
from lasagne.layers import InputLayer, DenseLayer, get_output,MaxPool2DLayer,Conv2DLayer,Layer
from lasagne.updates import sgd, apply_momentum,apply_nesterov_momentum
from lasagne.objectives import categorical_accuracy
from lasagne.regularization import regularize_layer_params
from scipy.misc import imshow
import pickle
import theano.typed_list
import numpy as np
import random
path  =r'/media/pan/Acer/Users/Pan/Desktop/plankton/'


'''
xtrain1 = pickle.load(open(path+ r'xtrain1.p','rb'))
ytrain1 = pickle.load(open(path+ r'ytrain1.p','rb'))

n = len(ytrain1)
index = range(n)
random.shuffle(index)
#xtrain = np.array(i.ravel()/255. for i in xtrain1[0:60000]])
xtrain =[]
for i in range(60000):
    xtrain.append( xtrain1[index[i]].ravel())

ytrain = np.array(ytrain1)[index[0:60000]]
pickle.dump(xtrain,open(path+'xtrain2.p','wb'))   
pickle.dump(ytrain,open(path+'ytrain2.p','wb'))

#xtest = np.array(i.ravel()/255. for i in xtrain1[50000:n])
xtest = []
for i in range(n-60000):
    xtest.append(xtrain1[index[i+60000]].ravel())

ytest = np.array(ytrain1)[index[60000:n]]
pickle.dump(xtest,open(path+'xtest2.p','wb'))
pickle.dump(ytest,open(path+'ytest2.p','wb'))
'''
class cyclicslice(Layer):
    def get_output_for(self,p1,**kwargs):
        self.shape=p1.shape
#        pp=T.tensor4('pp')
        def rotate(p):
            r1=p.dimshuffle(0,2,1)[:,:,::-1]
            r2=p[:,:,::-1].dimshuffle(0,2,1)
            r3=p[:,::-1,:][:,:,::-1]
            r4=p
            return T.concatenate((r4,r1,r3,r2))
        tmp1,update=theano.scan(rotate,outputs_info=None,sequences=p1)
        return tmp1.reshape((tmp1.shape[0]*tmp1.shape[1],1,tmp1.shape[2],tmp1.shape[3]))
    def get_output_shape_for(self, input_shape):
        return (None,input_shape[1],input_shape[2],input_shape[3])


class cyclicpool(Layer):
    def get_output_for(self,input,**kwargs):
        tmp=input.reshape((input.shape[0]/4,4,input.shape[1]))
        return T.mean(tmp,axis=1)
    def get_output_shape_for(self, input_shape):
        return (None,input_shape[1])

rng=np.random
x1=T.matrix('x1',dtype='float32')
y1=T.vector('y1',dtype='int64')
batchsize=64
cycle=True

train_x = pickle.load(open(path+'xtrain2.p','rb'))
train_y = pickle.load(open(path+'ytrain2.p','rb'))
xtest = pickle.load(open(path+'xtest2.p','rb'))
ytest =  pickle.load(open(path+'ytest2.p','rb'))
#train_x=pickle.load(open('/home/ziheng/Desktop/cnn/train_x.pkl','r')).reshape((65000,10000))/255.0
#train_y=pickle.load(open('/home/ziheng/Desktop/cnn/train_y.pkl','r'))-1

#test_x=pickle.load(open('/home/ziheng/Desktop/cnn/test_x.pkl','r')).reshape((10000,10000))/255.0
#test_y=pickle.load(open('/home/ziheng/Desktop/cnn/test_y.pkl','r'))-1

l0=InputLayer(shape=(None,1,100,100),input_var=x1.reshape((x1.shape[0],1,100,100)))
l0_5=cyclicslice(l0)
l1=Conv2DLayer(l0_5,32,(5,5),nonlinearity=very_leaky_rectify)
l2=MaxPool2DLayer(l1,(2,2))
l3=Conv2DLayer(l2,48,(5,5),nonlinearity=very_leaky_rectify)
l4=MaxPool2DLayer(l3,(2,2))
l5=Conv2DLayer(l4,64,(5,5),nonlinearity=very_leaky_rectify)
l6=MaxPool2DLayer(l5,(3,3))
l7=DenseLayer(l6,512,nonlinearity=very_leaky_rectify)
l7_5=cyclicpool(l7)
l8=DenseLayer(l7_5,121,nonlinearity=softmax)


rate=theano.shared(np.cast['float32'](0.01))
params = lasagne.layers.get_all_params(l8)
prediction = lasagne.layers.get_output(l8)
l2_penalty = regularize_layer_params([l7,l8], lasagne.regularization.l2)*np.cast['float32'](.0001)
loss = lasagne.objectives.categorical_crossentropy(prediction, y1)  
loss = loss.mean()+l2_penalty
updates_sgd = sgd(loss, params, learning_rate=rate)
updates = apply_nesterov_momentum(updates_sgd, params, momentum=0.8)
train_model = theano.function([x1,y1],outputs=loss,updates=updates,allow_input_downcast=True)
fprediction = theano.function([x1],outputs=prediction,allow_input_downcast=True)
pred=theano.function([x1,y1],outputs=categorical_accuracy(prediction,y1),allow_input_downcast=True)
sp_output = updates.values().append(loss)
sp_return = theano.function(inputs=[x1,y1],outputs=updates.values(),allow_input_downcast=True)
lossf = theano.function([x1,y1],outputs = loss,allow_input_downcast=True)
def spupdate(outputs,updates):
    for i in range(len(outputs)):
        updates.keys()[i].set_value(outputs[i])

train_x = np.array(train_x)
train_y = np.array(train_y)-1
xtest =np.array(xtest)
ytest = np.array(ytest)-1
n = len(train_y)
###begin to train
renewtrain=len(train_x)/batchsize
def getpvalue(params):
    vpara = []
    for i in params:
        vpara.append(i.get_value())
    return vpara

def saveparam(paramvalue,i):
    pickle.dump(paramvalue,open(path+'param_'+str(i)+'.p','wb'))

def setpvalue(para0,params):
    for i in range(len(params)):
        params[i].set_value(para0[i])

#renewtest=len(test_x)/batchsize
#LOSS = []
#PRED = []
i=22296
LOSS = pickle.load(open(path +'LOSS_'+str(i)+'.p','rb'))
PRED = pickle.load(open(path +'PRED_'+str(i)+'.p','rb'))
#pickle.dump(LOSS,open(path +'LOSS_'+str(i)+'.p','wb'))
#pickle.dump(PRED,open(path +'PRED_'+str(i)+'.p','wb'))
para0 = pickle.load(open(path +'param_'+str(i)+'.p','rb'))
setpvalue(para0,params)
while i <=100000:
    if i%renewtrain+1 == 0:    
        tem = random.shuffle(range(n))
        train_x = train_x[tem]
        train_y = train_y[tem]  
    if i>600 and i<900:
        rate.set_value(np.cast['float32'](.006))
    if i>900 and i<3000:
        rate.set_value(np.cast['float32'](.002))
    elif i>3000 and i<7000:
        rate.set_value(np.cast['float32'](.001))
    elif i>7000 and i<12000:
        rate.set_value(np.cast['float32'](.0005))        
    elif i>12000 and i<20000:
        rate.set_value(np.cast['float32'](.0001))
    elif i>20000:
        rate.set_value(np.cast['float32'](.00002))           
    if cycle:
        i1=i%renewtrain
        tindex=range(i1*batchsize,(i1+1)*batchsize)
        #spupdate(sp_return(train_x[tindex]/255.,train_y[tindex]),updates)        
        #newloss= lossf(train_x[tindex]/255.,train_y[tindex])
        newloss = train_model(train_x[tindex]/255.,train_y[tindex])
        LOSS.append(newloss)
        if i >2:
            if (LOSS[-1]-LOSS[-2])>5:
                print 'diverge!!'
                saveparam(para0,i)
                break
            para0=getpvalue(params)
    if i%renewtrain ==0:
        temp = range(len(ytest))
        random.shuffle(temp)
        prederror1 = pred(xtest[temp[0:500]]/255.,ytest[temp[0:500]])
        prederror2 = pred(xtest[temp[500:1000]]/255.,ytest[temp[500:1000]])
        prederror3 = pred(xtest[temp[1000:1500]]/255.,ytest[temp[1000:1500]])        
        errorrate = sum(prederror1+prederror2+prederror3)/1500.
        PRED.append(errorrate)
        print '++++++++++PREDERROR:%f' %errorrate        
    print 'in %d round, the loss function is %f'%(i+1,newloss)    
    i+=1

